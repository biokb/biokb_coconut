import io
import logging
import os
import sqlite3
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Optional, Type
from urllib.parse import urlparse

import pandas as pd
from numpy import insert
from pandas import DataFrame, Series
from sqlalchemy import Engine, create_engine, event, text, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from biokb_coconut import constants
from biokb_coconut.db import models

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    """Enable foreign key constraint for SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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
    ) -> None:
        connection_str = os.getenv(
            "CONNECTION_STR", constants.DB_DEFAULT_CONNECTION_STR
        )
        self.engine: Engine = engine if engine else create_engine(str(connection_str))
        if self.engine.dialect.name == "sqlite":
            with self.engine.connect() as connection:
                connection.execute(text("pragma foreign_keys=ON"))

        logger.info("Engine %s", self.engine)
        self.Session: sessionmaker[Session] = sessionmaker(bind=self.engine)
        self.filename: str = os.path.basename(urlparse(constants.DOWNLOAD_LINK).path)
        self.path_to_file: Optional[str] = None

    @property
    def session(self) -> Session:
        """Get a new SQLAlchemy session.

        Returns:
            Session: SQLAlchemy session
        """
        return self.Session()

    def set_path_to_file(self, path_to_file: str):
        """
        Set the path to the database file (for testing purposes).
        Args:
            path_to_file (str): The file system path to the database file.
        Raises:
            FileNotFoundError: If the specified file does not exist.
        Note:
            This method validates that the file exists before setting the path.
        """

        if not os.path.exists(path_to_file):
            raise FileNotFoundError(f"The file {path_to_file} does not exist.")
        self.path_to_file = path_to_file

    def create_db(self) -> None:
        """Create the database and all tables."""
        models.Base.metadata.create_all(self.engine)
        logger.info(
            "Database created with tables: %s", models.Base.metadata.tables.keys()
        )

    def drop_db(self) -> None:
        """Drop the database and all tables."""
        models.Base.metadata.drop_all(self.engine)
        logger.info("Database dropped")

    def recreate_db(self) -> None:
        """Recreate the database and all tables."""
        self.drop_db()
        self.create_db()

    def download_data(self, force_download: bool = False) -> str:
        """Downloads file from Coconut if it does not already exist locally.
        Returns:
            str: The full path to the downloaded or existing data file.
        """
        path_to_file = os.path.join(constants.DATA_FOLDER, self.filename)
        if not os.path.exists(path_to_file) or force_download:
            logger.info("Start download %s", self.filename)
            urllib.request.urlretrieve(constants.DOWNLOAD_LINK, path_to_file)
        return path_to_file

    def insert_one_to_n_table(
        self, df: DataFrame, column_name: str, model: Type[models.Base]
    ) -> tuple[int, DataFrame]:
        """
        Insert unique values from a DataFrame column into a database table and return the original DataFrame with added ID mappings.

        This method extracts unique non-null values from a specified column, inserts them into a database table,
        and then merges the generated IDs back into the original DataFrame.

        Args:
            df (DataFrame): The input DataFrame containing the data to process.
            column_name (str): The name of the column containing values to extract and insert.
            model (Type[models.Base]): The SQLAlchemy model class representing the target database table.

        Returns:
            DataFrame: The original DataFrame with an additional column '{column_name}_id' containing
                      the corresponding database IDs for each value in the specified column.

        Note:
            - Duplicate values in the specified column are automatically removed before insertion.
            - Null/NaN values are filtered out before processing.
            - The database table indexes start from 1.
            - The method uses 'append' mode for SQL insertion.
        """
        df_cc = (
            df[[column_name]]
            .drop_duplicates()
            .dropna()
            .rename(columns={column_name: "name"})
            .reset_index(drop=True)
            .rename_axis("id")
        )
        df_cc.index += 1  # Start index from 1
        inserted = df_cc.to_sql(model.__tablename__, self.engine, if_exists="append")
        df_cc[f"{column_name}_id"] = df_cc.index
        return inserted or 0, df.merge(
            df_cc,
            how="left",
            left_on=column_name,
            right_on="name",
            suffixes=("", f"_{column_name}"),
        ).drop(columns=[f"name_{column_name}"])

    def import_data(
        self, force_download: bool = False, keep_files: bool = False
    ) -> dict[str, int]:
        """
        Import chemical compound data from a CSV file into the database.

        This method orchestrates the complete data import process by:
        1. Recreating the database schema
        2. Downloading or using existing data file
        3. Processing and importing hierarchical classification data
        4. Importing main compound records
        5. Handling many-to-many relationships for collections, organisms, DOIs, synonyms, and CAS numbers
        6. Updating organism taxonomic information
        7. Cleaning up temporary files if requested

        Args:
            force_download (bool, optional): If True, forces re-download of data file
                even if it already exists locally. Defaults to False.
            keep_files (bool, optional): If True, preserves downloaded files after
                import completion. If False, removes temporary files. Defaults to False.

        Returns:
            int | None: Number of rows inserted into the main compound table,
                or None if the operation fails.

        Raises:
            Various exceptions may be raised during file operations, database
            operations, or data processing steps.
        """
        self.recreate_db()
        path_to_file = self.path_to_file or self.download_data(
            force_download=force_download
        )

        logger.info("Importing data from %s", path_to_file)
        df = pd.read_csv(
            path_to_file,
            compression="zip",
            low_memory=False,
        )

        df.rename(
            columns={"cas": "cas_numbers"}, inplace=True
        )  # create a plural to allow for easier handling
        inserted: dict[str, int] = {}

        inserted_csupc, df = self.insert_one_to_n_table(
            df, "chemical_super_class", models.ChemicalSuperClass
        )
        inserted[models.ChemicalSuperClass.__tablename__] = inserted_csupc
        inserted_cc, df = self.insert_one_to_n_table(
            df, "chemical_class", models.ChemicalClass
        )
        inserted[models.ChemicalClass.__tablename__] = inserted_cc
        inserted_csubc, df = self.insert_one_to_n_table(
            df, "chemical_sub_class", models.ChemicalSubClass
        )
        inserted[models.ChemicalSubClass.__tablename__] = inserted_csubc
        inserted_dpc, df = self.insert_one_to_n_table(
            df, "direct_parent_classification", models.DirectParentClassification
        )
        inserted[models.DirectParentClassification.__tablename__] = inserted_dpc
        inserted_ncp, df = self.insert_one_to_n_table(
            df, "np_classifier_pathway", models.NpClassifierPathway
        )
        inserted[models.NpClassifierPathway.__tablename__] = inserted_ncp
        inserted_ncs, df = self.insert_one_to_n_table(
            df, "np_classifier_superclass", models.NpClassifierSuperclass
        )
        inserted[models.NpClassifierSuperclass.__tablename__] = inserted_ncs
        inserted_ncc, df = self.insert_one_to_n_table(
            df, "np_classifier_class", models.NpClassifierClass
        )
        inserted[models.NpClassifierClass.__tablename__] = inserted_ncc
        column_names = [
            column.name
            for column in models.Compound.__table__.columns
            if column.name != "id"
        ]
        df.reset_index(inplace=True)
        df.index += 1
        df.index.name = "id"
        inserted_c = (
            df[column_names].to_sql(
                models.Compound.__tablename__,
                self.engine,
                if_exists="append",
                chunksize=100000,
            )
            or 0
        )
        inserted[models.Compound.__tablename__] = inserted_c

        logger.info("Data imported into %s", models.Compound.__tablename__)

        u1, j1 = self.import_n2m_column(
            column_series=df.collections,
            column_name=models.Collection.name.name,
            joining_model=models.CompoundCollection,
            model=models.Collection,
        )
        inserted[models.Collection.__tablename__] = u1
        inserted[models.CompoundCollection.__tablename__] = j1

        u2, j2 = self.import_n2m_column(
            column_series=df.organisms,
            column_name=models.Organism.name.name,
            joining_model=models.CompoundOrganism,
            model=models.Organism,
        )
        inserted[models.Organism.__tablename__] = u2
        inserted[models.CompoundOrganism.__tablename__] = j2

        u3, j3 = self.import_n2m_column(
            column_series=df.dois,
            column_name=models.DOI.identifier.name,
            joining_model=models.CompoundDOI,
            model=models.DOI,
        )
        inserted[models.DOI.__tablename__] = u3
        inserted[models.CompoundDOI.__tablename__] = j3

        u4, j4 = self.import_n2m_column(
            column_series=df.synonyms,
            column_name=models.Synonym.name.name,
            joining_model=models.CompoundSynonym,
            model=models.Synonym,
        )
        inserted[models.Synonym.__tablename__] = u4
        inserted[models.CompoundSynonym.__tablename__] = j4

        u5, j5 = self.import_n2m_column(
            column_series=df.cas_numbers,
            column_name=models.CAS.number.name,
            joining_model=models.CompoundCAS,
            model=models.CAS,
        )
        inserted[models.CAS.__tablename__] = u5
        inserted[models.CompoundCAS.__tablename__] = j5

        self.update_organism_tax_ids(keep_files=keep_files)
        self.update_other_organism_ids_by_wcvp()

        if not keep_files:
            os.remove(path_to_file)
            logger.info("Removed downloaded file %s", path_to_file)
        return inserted

    def import_n2m_column(
        self,
        column_series: Series,
        column_name: str,
        joining_model: Type[models.Base],
        model: Type[models.Base],
    ) -> tuple[int, int]:
        """Import a many-to-many relationship column from a pandas Series to database tables.
        This method processes a pandas Series containing pipe-separated values ('|') and creates
        two database tables: one for unique values and another for the many-to-many associations.
        Args:
            column_series (Series): A pandas Series containing pipe-separated values to be split
                and imported. The series name will be used as the index column name.
            column_name (str): The name of the column in the target table that will store
                the unique values.
            joining_model (Type[models.Base]): SQLAlchemy model class for the association table
                that will store the many-to-many relationships.
            model (Type[models.Base]): SQLAlchemy model class for the table that will store
                the unique values from the column_series.
        Returns:
            None
        Note:
            - The method assumes the column_series contains string values separated by '|'
            - Drops NaN values before processing
            - Creates unique IDs starting from 1 for the model table
            - Creates association records linking compounds to the unique values
            - Uses 'append' mode when writing to SQL tables
        """
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
        inserted_unique = (
            df_unique.to_sql(model.__tablename__, self.engine, if_exists="append") or 0
        )

        # create a association (n:m) table
        df_unique[index_on[:-1] + "_id"] = df_unique.index
        df["compound_id"] = df.index
        df_1 = df.set_index(index_on)
        df_2 = df_unique.set_index(column_name)
        inserted_join = (
            df_1.join(df_2, how="inner")
            .drop_duplicates(subset=["compound_id", index_on[:-1] + "_id"])
            .to_sql(
                joining_model.__tablename__,
                self.engine,
                if_exists="append",
                index=False,
            )
            or 0
        )
        logger.info(
            "Imported %s",
            joining_model.__tablename__,
        )
        return inserted_unique, inserted_join

    def __download_taxdmp(self, path_to_file: str) -> None:
        """Download the NCBI taxdump file."""
        if not os.path.exists(path_to_file):
            logger.info("Download taxonomy data")
            urllib.request.urlretrieve(constants.TAXONOMY_URL, path_to_file)

    def _import_tax_names(self, keep_files: bool = False):
        """
        Import taxonomy names from NCBI taxonomy database into the local database.
        This method downloads the NCBI taxonomy dump file (taxdmp.zip), extracts the names.dmp file,
        processes the taxonomy names data, and imports it into the TaxonomyName table. The process
        involves dropping and recreating the table, parsing the pipe-delimited data, and bulk
        inserting the records.
        Args:
            keep_files (bool, optional): If True, keeps the downloaded taxdmp.zip file after
                processing. If False (default), removes the file to save disk space.
        Returns:
            None
        Note:
            - This operation can take up to 5 minutes to complete
            - The TaxonomyName table is completely rebuilt during this process
            - The method processes the names.dmp file which contains taxonomy names and their types
            - Data is inserted in chunks of 10,000 records for optimal performance
        Raises:
            Various exceptions may be raised during file download, database operations,
            or data processing steps.
        """

        logger.info("import taxonomy names (up to 5min)")
        models.TaxonomyName.__table__.drop(self.engine, checkfirst=True)  # type: ignore
        models.TaxonomyName.__table__.create(self.engine, checkfirst=True)  # type: ignore
        taxtree_path_to_file = os.path.join(constants.DATA_FOLDER, "taxdmp.zip")
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
        if not keep_files:
            os.remove(taxtree_path_to_file)
            logger.info("Removed downloaded file %s", taxtree_path_to_file)

    def update_organism_tax_ids(
        self, import_taxonomy_names: bool = True, keep_files: bool = False
    ):
        """Update taxonomy IDs for organisms in the database.

        This method updates the tax_id field in the Organism table by matching
        organism names with taxonomy data. It first attempts to match using
        scientific names, then falls back to matching any available name type
        for organisms that still lack a tax_id.

        Args:
            import_taxonomy_names (bool, optional): Whether to import taxonomy
                names before updating. Defaults to True.
            keep_files (bool, optional): Whether to keep downloaded taxonomy
                files after import. Defaults to False.

        Note:
            - This operation can take up to 5 minutes to complete
            - The TaxonomyName table is dropped after the update process
            - Updates are performed in two passes: first by scientific names,
              then by any name type for remaining unmatched organisms
        """
        logger.info("Update tax_ids in organism table (up to 5min)")
        if import_taxonomy_names:
            self._import_tax_names(keep_files=keep_files)

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
        """
        Update organism records with external identifiers from WCVP (World Checklist of Vascular Plants).
        This method downloads and processes WCVP data to enrich organism records with additional
        taxonomic identifiers including IPNI IDs, POWO IDs, and WCVP IDs.
        Process:
        1. Downloads WCVP data from external source if not already present locally
        2. Creates a temporary WCVPPlant table and populates it with species-level data
        3. Updates organism records in two passes:
           - First pass: Updates organisms that match accepted plant names
           - Second pass: Updates remaining organisms using synonyms, linking to accepted names
        4. Cleans up the temporary WCVPPlant table
        The method matches organism names with WCVP taxon names and updates the following fields:
        - ipni_id: International Plant Names Index identifier
        - powo_id: Plants of the World Online identifier
        - wcvp_id: World Checklist of Vascular Plants identifier
        """
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


def import_data(
    engine: Optional[Engine] = None,
    force_download: bool = False,
    keep_files: bool = False,
) -> dict[str, int]:
    """Import all data in database.

    Args:
        engine (Optional[Engine]): SQLAlchemy engine. Defaults to None.
        force_download (bool, optional): If True, will force download the data, even if
            files already exist. If False, it will skip the downloading part if files
            already exist locally. Defaults to False.
        keep_files (bool, optional): If True, downloaded files are kept after import.
            Defaults to False.

    Returns:
        Dict[str, int]: table=key and number of inserted=value
    """
    db_manager = DbManager(engine)
    return db_manager.import_data(force_download=force_download, keep_files=keep_files)


def get_session(engine: Optional[Engine] = None) -> Session:
    """Get a new SQLAlchemy session.

    Returns:
        Session: SQLAlchemy session
    """
    db_manager = DbManager(engine)
    return db_manager.session
