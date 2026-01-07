"""Basic constants."""

import os
from datetime import datetime
from pathlib import Path

# standard for all biokb projects, but individual set
PROJECT_NAME = "coconut"
BASIC_NODE_LABEL = "DbCoconut"
# standard for all biokb projects
ORGANIZATION = "biokb"
LIBRARY_NAME = f"{ORGANIZATION}_{PROJECT_NAME}"
HOME = str(Path.home())
BIOKB_FOLDER = os.path.join(HOME, f".{ORGANIZATION}")
PROJECT_FOLDER = os.path.join(BIOKB_FOLDER, PROJECT_NAME)
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
EXPORT_FOLDER = os.path.join(DATA_FOLDER, "ttls")
ZIPPED_TTLS_PATH = os.path.join(DATA_FOLDER, "ttls.zip")
SQLITE_PATH = os.path.join(BIOKB_FOLDER, f"{ORGANIZATION}.db")
DB_DEFAULT_CONNECTION_STR = "sqlite:///" + SQLITE_PATH
NEO4J_PASSWORD = "neo4j_password"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
LOGS_FOLDER = os.path.join(DATA_FOLDER, "logs")  # where to store log files
TABLE_PREFIX = PROJECT_NAME + "_"
os.makedirs(DATA_FOLDER, exist_ok=True)


# not standard for all biokb projects
WCVP_ZIP_FILE = "wcvp.zip"
WCVP_ZIP_FILE_PATH = os.path.join(DATA_FOLDER, WCVP_ZIP_FILE)
WCVP_NAMES_FILE = "wcvp_names.csv"


# get current year and month
month = datetime.now().month
year = datetime.now().year

DOWNLOAD_LINK = f"https://coconut.s3.uni-jena.de/prod/downloads/{year}-{month:02d}/coconut_csv-{month:02d}-{year}.zip"
FILE_IN_ZIP = f"coconut_csv-{month:02d}-{year}.csv"
WCVP_DOWNLOAD_URL = "https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip"

TAXONOMY_URL = "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdmp.zip"
