# Agentic CLI

Commands:

    --help          - Get help

    init            - Initialize a new project by copying example files from the package. 

    models          - list some popular LLM models
    list            - List all settings.
    set             - Set a config value.
    get             - Get a config value.
    delete          - Delete a config value.

    list-secrets    - List all secrets.
    set-secret      - Set a secret.
    get-secret      - Get a secret.
    delete-secret   - Delete a secret.

    ollama          - List the latest popular models from Ollama. Use "ollama pull <model> to download.
    claude          - Runs a completion with Anthropic's Claude sonnet model
    gpt             - Runs a completion with OpenAI's GPT-4o-mini model. Use --model to override.

    run             - Copies secrets into the Environment and Runs a shell command.
    serve           - Runs the FastAPI server for an agent.

    dashboard       - Manage the Next.js dashboard UI.
        start       - Start the Next.js dashboard UI.
        build       - Build the Next.js dashboard UI for production.


