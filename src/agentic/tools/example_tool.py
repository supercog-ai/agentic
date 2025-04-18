from typing import Callable, Dict, Optional, Union
import pandas as pd

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, ConfigRequirement
from agentic.common import RunContext, PauseForInputResult

@tool_registry.register(
    name="ExampleTool",
    description="Example tool for demonstrating tool implementation patterns",
    dependencies=[],  # List any required pip packages here that are not already in the pyproject.toml
    config_requirements=[
        # List any required configuration settings here
        ConfigRequirement(
            key="EXAMPLE_API_KEY",
            description="API key for the Example service",
            required=False,  # Set to True if this is mandatory
        ),
    ],
)

class ExampleTool(BaseAgenticTool):
    """
    A tool that demonstrates the standard patterns for implementing agentic tools.
    
    This tool shows how to handle authentication, process data, and interact with
    external services in a standardized way.
    """
    
    # Instance variables for configuration
    api_key: Optional[str]
    base_url: str

    def __init__(self, api_key: str = None, base_url: str = "https://api.example.com"):
        """
        Initialize the Example tool.
        
        Args:
            api_key: Optional API key for authentication, can also be provided via secrets
            base_url: Base URL for the API, defaults to https://api.example.com
        """
        self.api_key = api_key
        self.base_url = base_url

    def required_secrets(self) -> Dict[str, str]:
        """
        Define the secrets that this tool requires.
        
        Returns:
            Dictionary mapping secret names to descriptions
        """
        return {
            "EXAMPLE_API_KEY": "API key for authenticating with the Example service"
        }

    def get_tools(self) -> list[Callable]:
        """
        Return the list of callable methods that will be available to agents.
        
        Returns:
            List of callable methods
        """
        return [
            self.fetch_data,
            self.process_data,
            self.secured_operation,
        ]

    def fetch_data(
        self, 
        run_context: RunContext, 
        query: str, 
        limit: int = 10
    ) -> pd.DataFrame:
        """
        Fetch data from the Example API based on the provided query.
        
        Args:
            run_context: The execution context
            query: Search query string
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            DataFrame containing the query results
        """
        # In a real implementation, you would:
        # 1. Authenticate with the API
        # 2. Send the query
        # 3. Process the response
        # 4. Return the data as a DataFrame
        
        # Example implementation:
        run_context.info(f"Fetching data with query: {query}, limit: {limit}")
        
        # This is just dummy data for the example
        data = {
            "id": list(range(1, limit + 1)),
            "name": [f"Result {i}" for i in range(1, limit + 1)],
            "value": [i * 10 for i in range(1, limit + 1)],
        }
        
        return pd.DataFrame(data)

    async def process_data(
        self, 
        data: Union[pd.DataFrame, str], 
        operation: str = "summarize"
    ) -> Dict[str, any]:
        """
        Process data using an asynchronous operation.
        
        This example demonstrates an async method that can process either a DataFrame
        or a string data source.
        
        Args:
            data: DataFrame or string data to process
            operation: Type of processing to perform (default: "summarize")
            
        Returns:
            Dictionary containing the processing results
        """
        # Convert string to DataFrame if needed
        if isinstance(data, str):
            # In a real implementation, you might parse CSV, JSON, etc.
            df = pd.DataFrame({"text": [data]})
        else:
            df = data
            
        # Example async processing
        # In a real implementation, you would perform async I/O operations here
        
        # Simple demo results
        results = {
            "operation": operation,
            "row_count": len(df),
            "column_count": len(df.columns) if hasattr(df, "columns") else 0,
            "sample": df.head(2).to_dict() if hasattr(df, "head") else str(df)[:100],
        }
        
        return results

    def secured_operation(
        self, 
        run_context: RunContext, 
        action: str, 
        parameters: Dict[str, any] = {}
    ) -> Union[str, PauseForInputResult]:
        """
        Perform an operation that requires authentication.
        
        This example demonstrates how to handle authentication and secrets.
        
        Args:
            run_context: The execution context
            action: The action to perform
            parameters: Additional parameters for the action
            
        Returns:
            Result of the operation or a request for authentication
        """
        # Get API key from secrets or instance variable
        api_key = run_context.get_secret("EXAMPLE_API_KEY", self.api_key)
        
        # If no API key is available, request it from the user
        if not api_key:
            return PauseForInputResult(
                {"EXAMPLE_API_KEY": "Please provide your Example API key"}
            )
        
        # Log the operation (but not the API key!)
        run_context.info(f"Performing secured operation: {action}")
        run_context.debug(f"Parameters: {parameters}")
        
        # In a real implementation, you would:
        # 1. Authenticate with the API using the api_key
        # 2. Perform the requested action
        # 3. Process and return the results
        
        # Example implementation
        return f"Successfully performed {action} with {len(parameters)} parameters"

    def test_credential(self, cred: str, secrets: Dict[str, str]) -> Optional[str]:
        """
        Test that the provided credentials are valid.
        
        Args:
            cred: Credential key to test
            secrets: Dictionary of secrets to test
            
        Returns:
            None if credentials are valid, otherwise an error message
        """
        # Get the API key from the secrets
        api_key = secrets.get("EXAMPLE_API_KEY")
        
        if not api_key:
            return "API key is missing"
            
        # In a real implementation, you would validate the API key
        # by making a test request to the API
        
        # For this example, we'll consider any non-empty string valid
        if len(api_key.strip()) > 0:
            return None
        else:
            return "API key cannot be empty"
