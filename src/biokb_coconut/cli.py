from venv import create

import click
from sqlalchemy import create_engine

from biokb_coconut import __version__
from biokb_coconut.db.manager import DbManager
from biokb_coconut.rdf.neo4j_importer import Neo4jImporter
from biokb_coconut.rdf.turtle import TurtleCreator


@click.group()
def cli():
    """BioKB COCONUT CLI - Manage COCONUT: Import in RDBMS, create turtle files and import into Neo4J.

    Please follow the steps:\n
    1. Import data using 'import-data' command.\n
    2. Create TTL files using 'create-ttls' command.\n
    3. Import TTL files into Neo4j using 'import-neo4j' command.\n
    """
    pass


@cli.command("import-data")
@click.option(
    "-f",
    "--force-download",
    is_flag=True,
    type=bool,
    default=False,
    help="Force re-download of the source file [default: False]",
)
@click.option(
    "-c",
    "--connection-string",
    type=str,
    default="sqlite:///coconut.db",
    help="SQLAlchemy engine URL [default: sqlite:///coconut.db]",
)
def import_data(force_download: bool, connection_string: str):
    """Import COCONUT data."""
    engine = create_engine(connection_string)
    DbManager(engine=engine).import_data(force_download=force_download)
    click.echo(f"Data imported successfully to {connection_string}")


@cli.command("create-ttls")
@click.option(
    "-c",
    "--connection-string",
    type=str,
    default="sqlite:///coconut.db",
    help="SQLAlchemy engine URL [default: sqlite:///coconut.db]",
)
def create_ttls(connection_string: str):
    """Create TTL files from local database."""
    path_to_zip = TurtleCreator(create_engine(connection_string)).create_ttls()
    click.echo(
        f"Path to the zip file containing all generated Turtle files. {path_to_zip}"
    )


@cli.command("import-neo4j")
@click.option("--uri", "-i", default="bolt://localhost:7687", help="Neo4j database URI")
@click.option("--user", "-u", default="neo4j", help="Neo4j username")
@click.option("--password", "-p", required=True, help="Neo4j password")
def import_neo4j(uri: str, user: str, password: str):
    """Import TTL files into Neo4j database."""
    Neo4jImporter(neo4j_uri=uri, neo4j_user=user, neo4j_pwd=password).import_ttls()


if __name__ == "__main__":
    cli()
