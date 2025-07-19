import logging
import os
import re
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import pandas as pd
from pandas import DataFrame, Series
from sqlalchemy import Engine, create_engine, text
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
        """Downloads file from PSC if it does not already exist locally.
        Returns:
            str: The full path to the downloaded or existing data file.
        """
        path_to_file = os.path.join(constants.DATA_FOLDER, self.filename)
        if not os.path.exists(path_to_file):
            logger.info("Start download %s", self.filename)
            urllib.request.urlretrieve(constants.DOWNLOAD_LINK, path_to_file)
        return path_to_file

    def import_data(self):
        """Import data from SQL file and use mappings to import data."""
        self.recreate_db()
        inserted: dict[str, Optional[int]] = {}
        path_to_file = self.path_to_file or self.download_data()
        logger.info("Importing data from %s", path_to_file)
        # Unzip the test.zip file in the data folder
        with zipfile.ZipFile(path_to_file, "r") as zip_ref:
            zip_ref.extractall(constants.DATA_FOLDER)

        # Assume the extracted file is test.csv
        csv_path = os.path.join(
            constants.DATA_FOLDER,
            "coconut_csv-07-2025.csv",
        )
        column_names = [
            column.name
            for column in models.Compound.__table__.columns
            if column.name != "id"
        ]

        df = pd.read_csv(csv_path, low_memory=False)
        df.rename(
            columns={"cas": "cas_numbers"}, inplace=True
        )  # create a plural to allow for easier handling
        df.index = df.index + 1  # Adjust index to start from 1
        df.index.name = "id"
        df[column_names].to_sql(
            models.Compound.__tablename__,
            self.engine,
            if_exists="append",
            chunksize=100000,
        )  # Select only the relevant columns

        logger.info("Data imported into %s", models.Compound.__tablename__)

        self.import_n2m_column(
            column_series=df.collections,
            column_name=models.Collection.name.name,
            joining_model=models.compound_collection,
            model=models.Collection,
        )

        self.import_n2m_column(
            column_series=df.organisms,
            column_name=models.Organism.name.name,
            joining_model=models.compound_organism,
            model=models.Organism,
        )

        self.import_n2m_column(
            column_series=df.dois,
            column_name=models.DOI.identifier.name,
            joining_model=models.compound_doi,
            model=models.DOI,
        )

        self.import_n2m_column(
            column_series=df.synonyms,
            column_name=models.Synonym.name.name,
            joining_model=models.compound_synonym,
            model=models.Synonym,
        )

        self.import_n2m_column(
            column_series=df.cas_numbers,
            column_name=models.CAS.number.name,
            joining_model=models.compound_cas,
            model=models.CAS,
        )

    def import_n2m_column(
        self,
        column_series: Series,
        column_name: str,
        joining_model,
        model,
    ):
        df = column_series.dropna().str.split("|").explode().to_frame()
        index_on: str = str(column_series.name)

        df_unique = pd.DataFrame(df.iloc[:, 0].unique(), columns=[column_name])
        df_unique.index += 1  # Start index from 1
        df_unique.index.name = "id"
        df_unique.to_sql(model.__tablename__, self.engine, if_exists="append")

        df_unique[index_on[:-1] + "_id"] = df_unique.index
        df["compound_id"] = df.index
        df_1 = df.set_index(index_on)
        df_2 = df_unique.set_index(column_name)
        df_1.join(df_2, how="inner").drop_duplicates(
            subset=["compound_id", index_on[:-1] + "_id"]
        ).to_sql(
            joining_model.name,
            self.engine,
            if_exists="append",
            index=False,
        )
        logger.info(
            "Imported %s",
            joining_model.name,
        )
