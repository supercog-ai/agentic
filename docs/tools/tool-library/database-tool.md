# DatabaseTool

The `DatabaseTool` provides a flexible interface for connecting to and querying SQL databases. This tool supports multiple database engines and allows agents to execute SQL queries with proper authentication.

## Features

- Connect to multiple database types (PostgreSQL, MySQL, SQLite, MSSQL)
- Run arbitrary SQL queries
- Support for SQL connection strings or CLI-style connection commands
- Automatic conversion of query results to pandas DataFrames or JSON
- Safe handling of database credentials

## Initialization

```python
def __init__(connection_string: str = None)
```

**Parameters:**

- `connection_string (str)`: Database connection string or CLI-style connection command

## Methods

### run_database_query

```python
def run_database_query(sql_query: str, thread_context: RunContext) -> pd.DataFrame | dict | PauseForInputResult
```

Runs a SQL query against a connected database.

**Parameters:**

- `sql_query (str)`: The SQL query to execute
- `thread_context (RunContext)`: The execution context with access to secrets

**Returns:**
Query results as a pandas DataFrame (for SELECT queries), or a status message (for other query types).

### get_database_type

```python
def get_database_type(thread_context: RunContext) -> str
```

Returns the type and SQL dialect of the connected database.

**Parameters:**

- `thread_context (RunContext)`: The execution context

**Returns:**
A string indicating the database type (e.g., "PostgreSQL", "MySQL", etc.).

## Connection String Formats

The tool supports the following connection string formats:

### SQLAlchemy Connection Strings

```
postgresql+psycopg2://username:password@host:port/database
mysql+pymysql://username:password@host:port/database  
mssql+pymssql://username:password@host:port/database
sqlite:///path/to/database.db
```

### CLI-Style Connection Commands

PostgreSQL:
```
PGPASSWORD=password psql -h host -p port -U username -d database
```

MySQL:
```
mysql -h host -P port -u username -p password -D database
```

MSSQL:
```
sqlcmd -S host -U username -P password -d database
```

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import DatabaseTool

# Connect with a connection string
db_tool = DatabaseTool("postgresql+psycopg2://user:pass@localhost:5432/mydb")

# Create an agent with database capabilities
db_agent = Agent(
    name="Database Assistant",
    instructions="You help users query databases and analyze data.",
    tools=[db_tool]
)

# Use the agent to run queries
response = db_agent << "Show me the top 5 customers by total order amount"
print(response)

# Or store the connection info in the agent's secrets
# and let the agent prompt for it when needed
generic_db_agent = Agent(
    name="Database Explorer",
    instructions="You connect to various databases and run queries.",
    tools=[DatabaseTool()]
)

response = generic_db_agent << "Connect to our PostgreSQL database and list all tables"
print(response)
```

## Handling Credentials

The tool can access database credentials in multiple ways:

1. Direct initialization: `DatabaseTool("connection_string")`
2. Environment variables
3. Agentic's secret system: `agentic secrets set database_url="connection_string"`
4. Interactive prompting: The tool will pause and ask for credentials if needed

## Supported Database Features

- SELECT queries return pandas DataFrames for easy data manipulation
- INSERT, UPDATE, DELETE queries return row counts
- CREATE, DROP and other DDL statements return success status
- Transaction support based on the underlying database capabilities
- Automatic type conversion between SQL and Python types
