from importlib.metadata import PackageNotFoundError, version

from biokb_coconut.db.manager import DbManager, get_session, import_data
from biokb_coconut.rdf.neo4j_importer import Neo4jImporter, import_ttls
from biokb_coconut.rdf.turtle import TurtleCreator, create_ttls

try:
    __version__ = version("biokb_coconut")
except PackageNotFoundError:
    # Package is not installed (e.g., during local development)
    __version__ = "unknown"

__all__ = [
    "DbManager",
    "import_data",
    "get_session",
    "Neo4jImporter",
    "import_ttls",
    "TurtleCreator",
    "create_ttls",
]
