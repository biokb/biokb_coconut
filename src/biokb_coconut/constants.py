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

DOWNLOAD_LINK = (
    "https://coconut.s3.uni-jena.de/prod/downloads/2025-07/coconut_csv-07-2025.zip"
)
