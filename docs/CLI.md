# Agentic CLI

## Global Commands

    init            - Initialize a new project
    serve           - Run the FastAPI server for an agent
    run             - Run a shell command with secrets in environment
    streamlit       - Run the Streamlit UI
    thread          - Start interactive CLI session with an agent
    dashboard       - Manage the dashboard UI

## Settings Management

    settings set    - Set a setting value
    settings list   - List all settings
    settings get    - Get a setting value
    settings delete - Delete a setting

## Secrets Management

    secrets set     - Set a secret value
    secrets list    - List all secrets (use --values to show values)
    secrets get     - Get a secret value
    secrets delete  - Delete a secret

## Model Operations

    models gpt      - Run completion with GPT (use --model to override)
    models claude   - Run completion with Claude
    models list     - List available LLM models
    models ollama   - List popular Ollama models

## Index Management

    index add              - Create a new index
    index list            - List all available indexes
    index rename          - Rename an index
    index delete          - Delete an index
    index search          - Search in an index

    index document add    - Add a document to an index
    index document list   - List documents in an index
    index document show   - Show document details
    index document delete - Delete a document from an index

## Dashboard Commands

    dashboard start  - Start the dashboard server
    dashboard build - Build the dashboard for production


