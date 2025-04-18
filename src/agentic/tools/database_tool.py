from typing import Callable
import re

import pandas as pd

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError

from agentic.common import RunContext, PauseForInputResult
from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency


class DatabaseConnectionError(Exception):
    pass


class LocalhostConnectionError(DatabaseConnectionError):
    pass

@tool_registry.register(
    name="DatabaseTool",
    description="Connect to SQL databases to analyze and operate on data",
    dependencies=[
        Dependency(
            name="sqlalchemy",
            version="2.0.26",
            type="pip",
        ),
        Dependency(
            name="psycopg2-binary",
            version="2.9.9",
            type="pip",
        )
    ],
    config_requirements=[],
)

class DatabaseTool(BaseAgenticTool):
    """Accessing any SQL database."""

    connection_string: str = ""
    engine: Engine = None

    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
        self.engine = None

    def __reduce__(self):
        deserializer = DatabaseTool
        serialized_data = (self.connection_string,)
        return deserializer, serialized_data

    def get_tools(self) -> list[Callable]:
        return [
            self.run_database_query,
            self.get_database_type,
            # self.connect_to_database,
        ]

    def parse_connection_string(self, connection_string: str) -> str:
        if connection_string.startswith("sqlite"):
            return connection_string

        """Parse the connection string or CLI command and check for localhost."""
        if "://" in connection_string:  # SQLAlchemy connection string
            parsed = urlparse(connection_string)

            # Modify the scheme based on the database type
            scheme = parsed.scheme
            if scheme == "mysql":
                new_scheme = "mysql+pymysql"
            elif scheme == "postgresql":
                new_scheme = "postgresql+psycopg2"
            elif scheme == "mssql":
                # Convert `mssql+pyodbc` to `mssql+pymssql`
                # Split the netloc part into user credentials and host+port/database
                netloc_parts = (
                    parsed.netloc.split("@", 1)
                    if "@" in parsed.netloc
                    else ["", parsed.netloc]
                )
                user_info = (
                    netloc_parts[0].split(":", 1)
                    if ":" in netloc_parts[0]
                    else [netloc_parts[0], ""]
                )
                user = user_info[0]
                password = user_info[1] if len(user_info) > 1 else ""

                # Split host and port/database
                host_and_port = (
                    netloc_parts[1].split("/", 1)
                    if "/" in netloc_parts[1]
                    else [netloc_parts[1], ""]
                )
                host = host_and_port[0]
                database = host_and_port[1] if len(host_and_port) > 1 else ""

                # Handle empty values and defaults
                if not user:
                    user = ""
                if not host:
                    raise ValueError("Host is required in the connection string.")
                if not database:
                    database = ""  # Default to empty string if not specified

                # Parse and remove the driver parameter from the query
                query_params = parse_qs(parsed.query)
                query_params.pop("driver", None)
                new_query = urlencode(query_params, doseq=True)

                new_scheme = "mssql+pymssql"
                # Reconstruct the connection string
                return urlunparse(
                    (new_scheme, f"{user}:{password}@{host}", "", "", new_query, "")
                )
            else:
                new_scheme = scheme  # Keep the original scheme for other databases
            # Reconstruct the connection string with the new scheme
            return urlunparse(
                (
                    new_scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
        else:  # CLI command
            # PostgreSQL
            pg_match = re.match(
                r"(?:PGPASSWORD=(\S+)\s+)?psql\s+(?:-h|--host)\s+(\S+)\s+(?:-p|--port)\s+(\d+)?\s+(?:-U|--username)\s+(\S+)(?:\s+(?:-d|--dbname)\s+(\S+))?(?:\s+(\S+))?(?:\s+--set=sslmode=(\S+))?(?:\s+(-W))?",
                connection_string,
            )

            if pg_match:

                # Unpack matched groups with default values
                (
                    password,
                    host,
                    port,
                    user,
                    db_with_d_flag,
                    db_positional,
                    sslmode,
                    prompt_password,
                ) = pg_match.groups(default="")

                # Database can come either from the -d flag or as a positional argument
                database = db_with_d_flag or db_positional

                if not database:
                    raise ValueError(
                        "Database is required either via -d or as a positional argument."
                    )

                # Default port to 5432 if not specified
                port = port or "5432"

                # Return formatted connection string for SQLAlchemy
                return (
                    f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
                )

            # MySQL
            mysql_match = re.match(
                r"mysql\s+-h\s+(\S+)\s+-P\s+(\d+)\s+-u\s+(\S+)\s+(?:-p\s*(\S*)\s*)?(?:-D\s+(\S+))?",
                connection_string,
            )

            if mysql_match:

                # Unpack matched groups with default values
                host, port, user, password, database = mysql_match.groups(default="")

                # Handle optional password and database
                password = (
                    password if password is not None else ""
                )  # No password provided
                database = (
                    database if database else ""
                )  # Default to empty string if not specified

                # Return the formatted connection string for further use (e.g., SQLAlchemy)
                return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

            # MSSQL
            mssql_match = re.match(
                r"(?:sqlcmd|mssql-cli)\s+-S\s+(\S+)\s+-U\s+(\S+)\s+-P\s+(\S+)(?:\s+-d\s+(\S+))?",
                connection_string,
            )

            if mssql_match:

                # Unpack matched groups with default values
                tool, host, user, password, database = mssql_match.groups(default="")

                # Handle the absence of the -d parameter (optional database)
                if database is None:
                    database = (
                        ""  # Default to empty string or set a default value if needed
                    )

                # Return the connection string formatted for SQLAlchemy or other usage
                return f"mssql+pymssql://{user}:{password}@{host}/{database}"

            # Handle ODBC-style MSSQL connection strings with optional parameters
            odbc_match = re.match(
                r"Server=(\S+)?(?:;Database=(\S+))?(?:;User Id=(\S+))?(?:;Password=(\S+))?;",
                connection_string,
            )

            if odbc_match:

                # Unpack matched groups with default values
                host, database, user, password = odbc_match.groups(default="")

                # Return the connection string formatted for SQLAlchemy or other usage
                return f"mssql+pymssql://{user}:{password}@{host}/{database}"
        raise ValueError("Unable to parse connection string")

    def create_engine(self, connection_string: str):
        """Create a SQLAlchemy engine from the connection string or CLI command."""
        try:
            parsed_connection_string = self.parse_connection_string(connection_string)
            return create_engine(parsed_connection_string)
        except LocalhostConnectionError as e:
            raise e
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to create database engine: {str(e)}")

    def _check_missing_connection(
        self, run_context: RunContext
    ) -> PauseForInputResult | None:
        if not self.engine:
            connection_string = self.connection_string or run_context.get_setting(
                "database_url"
            )
            if not connection_string:
                return PauseForInputResult(
                    {"database_url": "Database connection string"}
                )

            self.connection_string = connection_string
            try:
                engine = self.create_engine(connection_string)
                with engine.begin() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as e:
                print(f"Error connecting to database: {e}")
                return PauseForInputResult(
                    {"database_url": "Corrected database connection string"}
                )

            run_context.set_setting("database_url", connection_string)
            run_context.info(f"Connecting to database: {connection_string}")
            self.engine = self.create_engine(connection_string)
        return None

    def run_database_query(
        self, sql_query: str, run_context: RunContext
    ) -> pd.DataFrame | dict | PauseForInputResult:
        """Runs a SQL query against a database."""

        wait_event = self._check_missing_connection(run_context)
        if wait_event:
            return wait_event

        try:
            with self.engine.begin() as connection:
                # Execute the query
                result = connection.execute(text(sql_query))

                # Check if the query returns rows
                if result.returns_rows:
                    # Try to read it into a DataFrame
                    try:
                        df = pd.read_sql(sql_query, connection)
                        return df
                    except:
                        # If it can't be read into a DataFrame, return as list of dicts
                        return {"result": [dict(row) for row in result.mappings()]}
                else:
                    # Query didn't return any rows
                    if result.rowcount is not None and result.rowcount >= 0:
                        return {
                            "status": f"Query executed successfully. Rows affected: {result.rowcount}"
                        }
                    else:
                        return {"status": "Query executed successfully"}
        except LocalhostConnectionError as e:
            return {"status": f"Error: {str(e)}"}
        except DatabaseConnectionError as e:
            return {"status": f"Connection error: {str(e)}"}
        except SQLAlchemyError as e:
            return {"status": f"Database error: {str(e)}"}
        except pd.errors.DatabaseError as e:
            return {"status": f"SQL query error: {str(e)}"}
        except Exception as e:
            return {"status": f"Unexpected error: {str(e)}"}

    def get_database_type(self, run_context: RunContext) -> str:
        """Returns the type and SQL dialect of the connected database"""
        wait_event = self._check_missing_connection(run_context)
        if wait_event:
            return wait_event

        try:
            parsed_connection_string = self.parse_connection_string(
                self.connection_string
            )
            dialect = parsed_connection_string.split("://")[0].split("+")[0]
            return dialect.capitalize()
        except LocalhostConnectionError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error determining database type: {str(e)}"

    def connect_to_database(self, connection_string: str = None) -> dict:
        """Connects to the database using the provided connection string or the connected database.
        Sample:
        postgresql+psycopg2://username:password@host:port/database
        mysql+pymysql://username:password@host:port/database
        mssql+pymssql://username:password@host:port/database
        """
        if connection_string is None:
            connection_string = self.credentials.get("database_url")

        if not connection_string:
            return {"status": "Connection string is missing"}

        try:
            engine = self.create_engine(connection_string)
            with engine.connect() as connection:
                self.credentials = {
                    "database_url": connection_string,
                }
                connection.execute(text("SELECT 1"))
                return {"status": "Connection successful"}
        except LocalhostConnectionError as e:
            return {"status": f"Error: {str(e)}"}
        except DatabaseConnectionError as e:
            return {"status": f"Connection error: {str(e)}"}
        except SQLAlchemyError as e:
            return {"status": f"Database error: {str(e)}"}
        except Exception as e:
            return {"status": f"Unexpected error: {str(e)}"}

    def test_credential(self, cred, secrets: dict) -> str:
        """Test that the given credential secrets are valid. Return None if OK, otherwise
        return an error message.
        """
        connection_string = secrets.get("database_url")
        if not connection_string:
            return "Connection string is missing"

        try:
            engine = self.create_engine(connection_string)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return None
        except LocalhostConnectionError as e:
            return str(e)
        except DatabaseConnectionError as e:
            return str(e)
        except SQLAlchemyError as e:
            return f"Failed to connect to the database: {str(e)}"
        except Exception as e:
            return f"Unexpected error while testing the connection: {str(e)}"
