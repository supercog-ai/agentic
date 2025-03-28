#!/usr/bin/env python
"""
Utility script to generate Swagger/OpenAPI documentation for the Agentic API.
"""
import json
import os
from fastapi.openapi.utils import get_openapi

def on_pre_build(config):
    """Hook to run before MkDocs builds the site."""
    # Get version from environment or some other source
    version = os.environ.get("VERSION", "latest")
    generate_swagger(version=version)

def generate_swagger(version="latest", output_path="docs/assets/swagger.json"):
    """Generate Swagger/OpenAPI documentation for the Agentic API."""
    # Import the AgentAPIServer class 
    from agentic.api import AgentAPIServer

    # Create a minimal instance of AgentAPIServer with empty agent list
    server = AgentAPIServer(agent_instances=[], port=8086)
    
    # Get the OpenAPI schema
    openapi_schema = get_openapi(
        title="Agentic API",
        version=version,
        description="API for interacting with Agentic agents",
        routes=server.app.routes,
    )
    new_content = json.dumps(openapi_schema, indent=2)
    
    # If there are no differences do not write to the file
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            existing_content = f.read()
        if existing_content == new_content:
            return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(new_content)
