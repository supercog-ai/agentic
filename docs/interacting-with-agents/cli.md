# Agentic CLI

## Global Commands

    init            - Initialize a new project by copying example files from the package
    thread          - Start interactive CLI session with an agent
    serve           - Runs the FastAPI server for an agent
    shell           - Copies secrets into the Environment and Runs a shell command
    streamlit       - Run the Streamlit UI

## Secrets Management

    secrets set     - Set a secret value
    secrets list    - List all secrets (use --values to show values)
    secrets get     - Get a secret value
    secrets delete  - Delete a secret
    
## Settings Management

    settings set    - Set a setting value
    settings list   - List all settings
    settings get    - Get a setting value
    settings delete - Delete a setting

## Dashboard Commands

    dashboard start - Start the dashboard server
    dashboard build - Build the dashboard for production

## Index Management

    index add             - Create a new index
    index list            - List all available indexes
    index rename          - Rename an index
    index delete          - Delete an index
    index search          - Search in an index

    index document add    - Add a document to an index
    index document list   - List documents in an index
    index document show   - Show document details
    index document delete - Delete a document from an index

## Model Operations

    models list     - List available LLM models
    models ollama   - List popular Ollama models
    models claude   - Run completion with Claude
    models gpt      - Run completion with GPT (use --model to override)


