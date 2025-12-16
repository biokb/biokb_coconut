"""Basic constants."""

import os
from pathlib import Path

HOME = str(Path.home())
BIOKB_FOLDER = os.path.join(HOME, ".biokb")
DB_DEFAULT_CONNECTION_STR = "sqlite:///" + os.path.join(BIOKB_FOLDER, "biokb.db")
PROJECT_NAME = "coconut"
TABLE_PREFIX = f"{PROJECT_NAME}_"
PROJECT_FOLDER = os.path.join(BIOKB_FOLDER, PROJECT_NAME)
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
os.makedirs(DATA_FOLDER, exist_ok=True)
WCVP_NAMES_FILE = os.path.join(BIOKB_FOLDER, "wcvp", "data")
WCVP_ZIP_FILE = "wcvp.zip"
WCVP_DATA_FOLDER = os.path.join(BIOKB_FOLDER, "wcvp", "data")
os.makedirs(WCVP_DATA_FOLDER, exist_ok=True)
WCVP_ZIP_FILE_PATH = os.path.join(WCVP_DATA_FOLDER, WCVP_ZIP_FILE)
WCVP_NAMES_FILE = "wcvp_names.csv"


# get current year and month
from datetime import datetime

month = datetime.now().month
year = datetime.now().year

DOWNLOAD_LINK = f"https://coconut.s3.uni-jena.de/prod/downloads/{year}-{month:02d}/coconut_csv-{month:02d}-{year}.zip"
FILE_IN_ZIP = f"coconut_csv-{month:02d}-{year}.csv"
WCVP_DOWNLOAD_URL = "https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip"

TAXONOMY_URL = "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdmp.zip"
TAXONOMY_DATA_FOLDER = os.path.join(BIOKB_FOLDER, "taxtree", "data")
os.makedirs(TAXONOMY_DATA_FOLDER, exist_ok=True)

TTL_EXPORT_FOLDER = os.path.join(DATA_FOLDER, "ttls")
os.makedirs(TTL_EXPORT_FOLDER, exist_ok=True)
TAXONOMY_DATA_FOLDER = os.path.join(BIOKB_FOLDER, "taxtree", "data")


BASIC_NODE_LABEL = "DbCoconut"
NEO4J_PASSWORD = "neo4j_password"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
ZIPPED_TTLS_PATH = os.path.join(DATA_FOLDER, "ttls.zip")
