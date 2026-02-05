import logging
import os

import click
from sqlalchemy import create_engine

from biokb_coconut import __version__
from biokb_coconut.api.main import run_api
from biokb_coconut.constants import DB_DEFAULT_CONNECTION_STR, NEO4J_USER
from biokb_coconut.db.manager import DbManager
from biokb_coconut.rdf.neo4j_importer import Neo4jImporter
from biokb_coconut.rdf.turtle import TurtleCreator


def setup_logging(ctx, param, value):
    # Only set up logging if the user actually asks for it
    if value == 1:
        logging.getLogger("biokb_coconut").setLevel(logging.INFO)
    elif value >= 2:
        logging.getLogger("biokb_coconut").setLevel(logging.DEBUG)

    # We must add a handler so the logs actually print to the screen
    if value > 0:
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logging.getLogger("fetcher").addHandler(ch)


@click.group()
@click.version_option(__version__)
def main() -> None:
    """Import in RDBMS, create turtle files and import into Neo4J.

    Please follow the steps:\n
    1. Import data using `import-data` command.\n
    2. Create TTL files using `create-ttls` command.\n
    3. Import TTL files into Neo4j using `import-neo4j` command.\n
    """
    pass


@main.command("import-data")
@click.option(
    "-f",
    "--force-download",
    is_flag=True,
    type=bool,
    default=False,
    help="Force re-download of the source file [default: False]",
)
@click.option(
    "-d",
    "--delete-files",
    is_flag=True,
    type=bool,
    default=False,
    help="Delete downloaded source files after import [default: False]",
)
@click.option(
    "-c",
    "--connection-string",
    type=str,
    default=DB_DEFAULT_CONNECTION_STR,
    help=f"SQLAlchemy engine URL [default: {DB_DEFAULT_CONNECTION_STR}]",
)
def import_data(
    force_download: bool, connection_string: str, delete_files: bool
) -> None:
    """Import data.

    Args:
        force_download (bool): Force re-download of the source file (default: False)
        connection_string (str): SQLAlchemy engine URL (default: sqlite:///coconut.db)
        delete_files (bool): Delete downloaded source files after import (default: False)
    """
    engine = create_engine(connection_string)
    DbManager(engine=engine).import_data(
        force_download=force_download, delete_files=delete_files
    )
    click.echo(f"Data imported successfully to {connection_string}")


@main.command("create-ttls")
@click.option(
    "-c",
    "--connection-string",
    type=str,
    default=DB_DEFAULT_CONNECTION_STR,
    help=f"SQLAlchemy engine URL [default: {DB_DEFAULT_CONNECTION_STR}]",
)
def create_ttls(connection_string: str) -> None:
    """Create TTL files from local database.

    Args:
        connection_string (str): SQLAlchemy engine URL (default: sqlite:///coconut.db)
    """
    path_to_zip = TurtleCreator(create_engine(connection_string)).create_ttls()
    click.echo(
        f"Path to the zip file containing all generated Turtle files. {path_to_zip}"
    )


@main.command("import-neo4j")
@click.option(
    "--uri",
    "-i",
    default="bolt://localhost:7687",
    help='Neo4j database URI [default:"bolt://localhost:7687"]',
)
@click.option(
    "--user", "-u", default=NEO4J_USER, help='Neo4j username [default="neo4j"]'
)
@click.option("--password", "-p", required=True, help="Neo4j password")
def import_neo4j(
    password: str, uri: str = "bolt://localhost:7687", user: str = NEO4J_USER
) -> None:
    """Import TTL files into Neo4j database."""
    Neo4jImporter(neo4j_uri=uri, neo4j_user=user, neo4j_pwd=password).import_ttls()


@main.command("run-server")
@click.option(
    "--host", "-h", default="0.0.0.0", help="API server host [default: 0.0.0.0]"
)
@click.option("--port", "-P", default=8000, help="API server port [default: 8000]")
@click.option("--user", "-u", default="admin", help="API username [default=admin]")
@click.option("--password", "-p", default="admin", help="API password [default: admin]")
def run_server(host: str, port: int, user: str, password: str) -> None:
    """Run the API server.

    Args:
        host (str): API server host
        port (int): API server port
        user (str): API username
        password (str): API password
    """
    # set env variables for API authentication
    os.environ["API_USER"] = user
    os.environ["API_PASSWORD"] = password
    host_shown = "127.0.0.1" if host == "0.0.0.0" else host
    click.echo(f"API server running at http://{host_shown}:{port}/docs#/")
    run_api(host=host, port=port)


if __name__ == "__main__":
    main()
