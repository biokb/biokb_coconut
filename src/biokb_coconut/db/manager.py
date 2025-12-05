import io
import logging
import os
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Optional, Type
from urllib.parse import urlparse

import pandas as pd
import requests
from pandas import DataFrame, Series
from sqlalchemy import Engine, create_engine, text, update
from sqlalchemy.orm import sessionmaker

from biokb_coconut import constants
from biokb_coconut.db import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TableData:
    table: str
    columns: list[str]
    rows: list[list[str]]

    @property
    def dataframe(self) -> DataFrame:
        return pd.DataFrame(self.rows, columns=self.columns)


class DbManager:
    def __init__(
        self,
        engine: Optional[Engine] = None,
    ):
        connection_str = os.getenv(
            "CONNECTION_STR", constants.DB_DEFAULT_CONNECTION_STR
        )
        self.engine = engine if engine else create_engine(str(connection_str))
        if self.engine.dialect.name == "sqlite":
            with self.engine.connect() as connection:
                connection.execute(text("pragma foreign_keys=ON"))

        logger.info("Engine %s", self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.filename = os.path.basename(urlparse(constants.DOWNLOAD_LINK).path)
        self.path_to_file: Optional[str] = None

    def set_path_to_file(self, path_to_file: str):
        # needed for tests
        self.path_to_file = path_to_file

    def create_db(self):
        """Create the database and all tables."""
        models.Base.metadata.create_all(self.engine)
        logger.info(
            "Database created with tables: %s", models.Base.metadata.tables.keys()
        )

    def drop_db(self):
        """Drop the database and all tables."""
        models.Base.metadata.drop_all(self.engine)
        logger.info("Database dropped")

    def recreate_db(self):
        """Recreate the database and all tables."""
        self.drop_db()
        self.create_db()

    def download_data(self) -> str:
        """Downloads file from Coconut if it does not already exist locally.
        Returns:
            str: The full path to the downloaded or existing data file.
        """
        path_to_file = os.path.join(constants.DATA_FOLDER, self.filename)
        if not os.path.exists(path_to_file):
            logger.info("Start download %s", self.filename)
            urllib.request.urlretrieve(constants.DOWNLOAD_LINK, path_to_file)
        return path_to_file

    def insert_one_to_n_table(
        self, df: DataFrame, column_name: str, model: Type[models.Base]
    ) -> DataFrame:
        df_cc = (
            df[[column_name]]
            .drop_duplicates()
            .dropna()
            .rename(columns={column_name: "name"})
            .reset_index(drop=True)
            .rename_axis("id")
        )
        df_cc.index += 1  # Start index from 1
        df_cc.to_sql(model.__tablename__, self.engine, if_exists="append")
        df_cc[f"{column_name}_id"] = df_cc.index
        return df.merge(
            df_cc,
            how="left",
            left_on=column_name,
            right_on="name",
            suffixes=("", f"_{column_name}"),
        ).drop(columns=[f"name_{column_name}"])

    def import_data(self):
        """Import data from SQL file and use mappings to import data."""
        self.recreate_db()
        path_to_file = self.path_to_file or self.download_data()

        logger.info("Importing data from %s", path_to_file)
        df = pd.read_csv(
            path_to_file,
            compression="zip",
            low_memory=False,
        )

        df.rename(
            columns={"cas": "cas_numbers"}, inplace=True
        )  # create a plural to allow for easier handling

        df = self.insert_one_to_n_table(
            df, "chemical_super_class", models.ChemicalSuperClass
        )
        df = self.insert_one_to_n_table(df, "chemical_class", models.ChemicalClass)
        df = self.insert_one_to_n_table(
            df, "chemical_sub_class", models.ChemicalSubClass
        )
        df = self.insert_one_to_n_table(
            df, "direct_parent_classification", models.DirectParentClassification
        )
        df = self.insert_one_to_n_table(
            df, "np_classifier_pathway", models.NpClassifierPathway
        )
        df = self.insert_one_to_n_table(
            df, "np_classifier_superclass", models.NpClassifierSuperclass
        )
        df = self.insert_one_to_n_table(
            df, "np_classifier_class", models.NpClassifierClass
        )

        column_names = [
            column.name
            for column in models.Compound.__table__.columns
            if column.name != "id"
        ]
        df.reset_index(inplace=True)
        df.index += 1
        df.index.name = "id"
        inserted_rows = df[column_names].to_sql(
            models.Compound.__tablename__,
            self.engine,
            if_exists="append",
            chunksize=100000,
        )

        logger.info("Data imported into %s", models.Compound.__tablename__)

        self.import_n2m_column(
            column_series=df.collections,
            column_name=models.Collection.name.name,
            joining_model=models.CompoundCollection,
            model=models.Collection,
        )

        self.import_n2m_column(
            column_series=df.organisms,
            column_name=models.Organism.name.name,
            joining_model=models.CompoundOrganism,
            model=models.Organism,
        )

        self.import_n2m_column(
            column_series=df.dois,
            column_name=models.DOI.identifier.name,
            joining_model=models.CompoundDOI,
            model=models.DOI,
        )

        self.import_n2m_column(
            column_series=df.synonyms,
            column_name=models.Synonym.name.name,
            joining_model=models.CompoundSynonym,
            model=models.Synonym,
        )

        self.import_n2m_column(
            column_series=df.cas_numbers,
            column_name=models.CAS.number.name,
            joining_model=models.CompoundCAS,
            model=models.CAS,
        )

        self.update_organism_tax_ids()
        self.update_other_organism_ids_by_wcvp()
        return inserted_rows

    def import_n2m_column(
        self,
        column_series: Series,
        column_name: str,
        joining_model: Type[models.Base],
        model: Type[models.Base],
    ):
        index_on: str = str(column_series.name)

        # Import a many-to-many relationship column from the DataFrame.
        # The column_series should contain strings with values separated by '|'.
        df = column_series.dropna().str.split("|").explode().to_frame()

        # create a table with unique values for column
        df_unique = pd.DataFrame(
            df.iloc[:, 0].str.strip().unique(), columns=[column_name]
        )
        df_unique.index += 1  # Start index from 1
        df_unique.index.name = "id"  # rename index to id
        df_unique.to_sql(model.__tablename__, self.engine, if_exists="append")

        # create a association (n:m) table
        df_unique[index_on[:-1] + "_id"] = df_unique.index
        df["compound_id"] = df.index
        df_1 = df.set_index(index_on)
        df_2 = df_unique.set_index(column_name)
        df_1.join(df_2, how="inner").drop_duplicates(
            subset=["compound_id", index_on[:-1] + "_id"]
        ).to_sql(
            joining_model.__tablename__,
            self.engine,
            if_exists="append",
            index=False,
        )
        logger.info(
            "Imported %s",
            joining_model.__tablename__,
        )

    def __download_taxdmp(self, path_to_file: str):
        """Download the NCBI taxdump file."""
        if not os.path.exists(path_to_file):
            logger.info("Download taxonomy data")
            r = requests.get(
                constants.TAXONOMY_URL,
                allow_redirects=True,
            )
            open(path_to_file, "wb").write(r.content)

    def _import_tax_names(self):
        """Import the taxonomy names.

        Returns:
            Dict[str, int]: table name, number of entries
        """
        logger.info("import taxonomy names (up to 5min)")
        models.TaxonomyName.__table__.drop(self.engine, checkfirst=True)  # type: ignore
        models.TaxonomyName.__table__.create(self.engine, checkfirst=True)  # type: ignore
        taxtree_path_to_file = os.path.join(
            constants.TAXONOMY_DATA_FOLDER, "taxdmp.zip"
        )
        self.__download_taxdmp(taxtree_path_to_file)
        archive = zipfile.ZipFile(taxtree_path_to_file, "r")
        names = archive.read("names.dmp")
        df = pd.read_csv(
            io.StringIO(names.decode("utf-8")),
            sep=r"\t\|\t",
            engine="python",
            usecols=[0, 1, 3],
            names=["tax_id", "name", "name_type"],
        )
        df.name_type = df.name_type.str[:-2]
        df.index += 1
        df.index.rename("id", inplace=True)
        df.to_sql(
            models.TaxonomyName.__tablename__,
            self.engine,
            if_exists="append",
            chunksize=10000,
        )

    def update_organism_tax_ids(self, import_taxonomy_names: bool = True):
        """Update the tax_ids in the organism table.

        Uses NCBI Taxonomy names to find tax_ids for plant names in the organism table.

        First tries to match scientific names, then any name.
        """
        logger.info("Update tax_ids in organism table (up to 5min)")
        if import_taxonomy_names:
            self._import_tax_names()

        with self.Session() as session:
            # Scientific name
            logger.info("Update tax_ids by scientific names")
            stmt = (
                update(models.Organism)
                .where(
                    models.Organism.name == models.TaxonomyName.name,
                    models.TaxonomyName.name_type == "scientific name",
                )
                .values(tax_id=models.TaxonomyName.tax_id)
            )
            session.execute(stmt)
            session.commit()

            # Try any name
            stmt = (
                update(models.Organism)
                .where(
                    models.Organism.name == models.TaxonomyName.name,
                    models.Organism.tax_id.is_(None),
                )
                .values(tax_id=models.TaxonomyName.tax_id)
            )
            session.execute(stmt)
            session.commit()
        models.TaxonomyName.__table__.drop(self.engine, checkfirst=True)  # type: ignore

    def update_other_organism_ids_by_wcvp(self):
        # download WCVP data if not already exists
        logger.info("Update other organism ids by WCVP")

        models.WCVPPlant.__table__.drop(self.engine, checkfirst=True)  # type: ignore
        models.WCVPPlant.__table__.create(self.engine, checkfirst=True)  # type: ignore
        if not os.path.exists(constants.WCVP_ZIP_FILE_PATH):
            logger.info("Downloading WCVP data...")
            urllib.request.urlretrieve(
                constants.WCVP_DOWNLOAD_URL, constants.WCVP_ZIP_FILE_PATH
            )

        with zipfile.ZipFile(constants.WCVP_ZIP_FILE_PATH, "r") as zf:
            use_cols = [
                "plant_name_id",
                "taxon_name",
                "taxon_rank",
                "accepted_plant_name_id",
                "powo_id",
                "ipni_id",
            ]
            df = pd.read_csv(
                zf.open(constants.WCVP_NAMES_FILE), usecols=use_cols, sep="|"
            )
            df.set_index("plant_name_id", inplace=True)
            df[df["taxon_rank"] == "Species"].drop(columns=["taxon_rank"]).to_sql(
                models.WCVPPlant.__tablename__,
                self.engine,
                if_exists="append",
                chunksize=10000,
            )
        with self.Session() as session:
            stmt = (
                update(models.Organism)
                .where(
                    models.Organism.name == models.WCVPPlant.taxon_name,
                    models.WCVPPlant.plant_name_id
                    == models.WCVPPlant.accepted_plant_name_id,
                )
                .values(
                    ipni_id=models.WCVPPlant.ipni_id,
                    powo_id=models.WCVPPlant.powo_id,
                    wcvp_id=models.WCVPPlant.plant_name_id,
                )
            )
            session.execute(stmt)
            session.commit()

            stmt = (
                update(models.Organism)
                .where(
                    models.Organism.name == models.WCVPPlant.taxon_name,
                    models.Organism.wcvp_id.is_(None),
                    models.WCVPPlant.plant_name_id
                    != models.WCVPPlant.accepted_plant_name_id,
                    models.WCVPPlant.accepted_plant_name_id.is_not(None),
                )
                .values(
                    ipni_id=models.WCVPPlant.ipni_id,
                    powo_id=models.WCVPPlant.powo_id,
                    wcvp_id=models.WCVPPlant.accepted_plant_name_id,
                )
            )
            session.execute(stmt)
            session.commit()

        models.WCVPPlant.__table__.drop(self.engine, checkfirst=True)  # type: ignore
