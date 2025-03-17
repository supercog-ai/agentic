import typer
import os
import requests
from rich.markdown import Markdown
from rich.console import Console
from typing import Optional, List, Dict
from .file_cache import file_cache
from .colors import Colors


import agentic.quiet_warnings
from agentic.agentic_secrets import agentic_secrets as secrets
from agentic.settings import settings

import shutil
from pathlib import Path
from importlib import resources, import_module
from rich.status import Status

import warnings
warnings.filterwarnings("ignore")

### WARNING: DO NOT ADD MORE IMPORTS HERE
# Everything imported at module level runs every time you run ANY cli command.
# So its much preferred to defer imports until the specific command that needs them.
##############

GPT_DEFAULT_MODEL = "openai/gpt-4o-mini"


# Create a state class to hold global options
class State:
    def __init__(self):
        self.no_cache: bool = False


state = State()

# Create the app with a callback
app = typer.Typer()


def quiet_log(*args):
    print(Colors.DARK_GRAY + " ".join(map(str, args)) + Colors.ENDC)


# Add the callback to process global options
@app.callback()
def main(
    no_cache: bool = typer.Option(
        False, "--nocache", help="Disable caching for all commands"
    )
):
    """
    Agentic CLI with various commands for managing secrets and running services.
    """
    state.no_cache = no_cache


@app.command()
def list_settings():
    """List all settings."""
    typer.echo("\n".join(sorted(settings.list_settings())))


@app.command()
def list_secrets():
    """List all secrets."""
    typer.echo("\n".join(sorted(secrets.list_secrets())))


@app.command()
def set(name: str, value: str):
    """Set a setting value."""
    typer.echo(settings.set(name, value))


@app.command()
def set_secret(name: str, value: str | None = None):
    """Set a secret."""

    # Allow setting a secret with a single argument in the form "name=value".
    if "=" in name and value is None:
        name, value = name.split("=", 1)

    typer.echo(secrets.set_secret(name, value))


@app.command()
def get(name: str):
    """Get a setting."""
    typer.echo(settings.get(name))


@app.command()
def get_secret(name: str):
    """Get a secret."""
    typer.echo(secrets.get_secret(name))


@app.command()
def get_all_secrets():
    """Get all secrets."""
    typer.echo(secrets.get_all_secrets())


@app.command()
def delete(name: str):
    """Delete a setting."""
    typer.echo(settings.delete_setting(name))


@app.command()
def delete_secret(name: str):
    """Delete a secret."""
    typer.echo(secrets.delete_secret(name))


@app.command()
def ollama():
    """List the latest popular models from Ollama. Use "ollama pull <model> to download."""
    from .llm import llm_generate, LLMUsage, CLAUDE_DEFAULT_MODEL, GPT_DEFAULT_MODEL
    from bs4 import BeautifulSoup

    # Download the web page from ollama.com/library

    url = "https://ollama.com/library"
    response = requests.get(url)
    html_content = response.content

    def extract_models(html_page: bytes) -> tuple[str, LLMUsage]:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        usage = LLMUsage()
        response = llm_generate(
            """
Get the names and descriptions from the top 20 models in this list:
{{models}}
            """,
            models=(soup.get_text() or ""),
            usage=usage,
        )
        return response, usage

    typer.echo("Current popular Ollama models:")

    usage: LLMUsage | None = None
    if state.no_cache:
        listing, usage = extract_models(html_content)
    else:
        listing = file_cache.get(
            url, ttl_seconds=60 * 12, fetch_fn=lambda: extract_models(html_content)
        )

    console = Console()
    md = Markdown(listing or "")
    console.print(md)
    if usage:
        quiet_log(usage)


@app.command()
def ui():
    """Runs the agentic UI"""
    os.execvp("streamlit", ["streamlit", "run", "src/agentic/ui/app.py"])

@app.command()
def claude(prompt: str):
    """Runs a completion with Anthropic's Claude sonnet model"""
    from .llm import llm_generate, LLMUsage, CLAUDE_DEFAULT_MODEL, GPT_DEFAULT_MODEL

    usage = LLMUsage()
    typer.echo(llm_generate(prompt, model=CLAUDE_DEFAULT_MODEL, usage=usage))
    quiet_log(usage)


@app.command()
def gpt(
    prompt: str,
    model: str = typer.Option(
        GPT_DEFAULT_MODEL, "--model", help="The model to use for completion"
    ),
):
    """Runs a completion with OpenAI's GPT-4o-mini model"""
    from .llm import llm_generate, LLMUsage, CLAUDE_DEFAULT_MODEL, GPT_DEFAULT_MODEL

    usage = LLMUsage()
    typer.echo(llm_generate(prompt, model=model, usage=usage))
    quiet_log(usage)


@app.command()
def models():
    typer.echo(
        "Visit https://docs.litellm.ai/docs/providers for the full list of models"
    )
    typer.echo(
        """
Popular models:
    openai/o1-mini
    openai/o1-preview
    openai/gpt-4o
    openai/gpt-4o-mini
    anthropic/claude-3-5-sonnet-20240620
    anthropic/claude-3-5-haiku-20241022
    lm_studio/qwen2.5-7b-instruct-1m
    lm_studio/deepseek-r1-distill-qwen-7B
     """
    )


import importlib.util
import inspect
import time


@app.command()
def serve(filename: str = typer.Argument(default="", show_default=False)):
    """Runs the FastAPI server for an agent"""
    from agentic.common import AgentRunner

    def find_agent_instances(file_path):
        # Load the module from file path
        spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
        if spec:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all Agent instances in the module
            agent_instances = []
            for name, obj in inspect.getmembers(module):
                # Check if object is an instance of Agent class
                if isinstance(
                    obj, module.Agent
                ):  # Assumes Agent class is defined in the module
                    agent_instances.append(obj)
            return agent_instances
        else:
            return []

    agent_instances = find_agent_instances(filename)
    if len(agent_instances) == 0:
        typer.echo(f"No agent instances found in {filename}. Make sure to create at least one agent at module scope.")
        raise typer.Exit(1)
    for agent in agent_instances:
        runner = AgentRunner(agent)
        path = runner.serve()

    # Busy loop until ctrl-c or ctrl-d
    #os.system(f"open http://0.0.0.0:8086{path}/docs")

    while True:
        time.sleep(1)


def copy_examples(src_path: Path, dest_path: Path, console: Console) -> None:
    """Copy example files from source to destination, maintaining directory structure."""
    try:
        if not dest_path.exists():
            dest_path.mkdir(parents=True)

        # Copy all files and directories
        for item in src_path.iterdir():
            target = dest_path / item.name

            if item.is_file():
                shutil.copy2(item, target)
                console.print(f"✓ Copied: {item.name}", style="green")
            elif item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
                console.print(f"✓ Copied directory: {item.name}", style="green")

    except Exception as e:
        console.print(f"Error copying examples: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def init(
    path: str = typer.Argument(
        ".", help="Directory to initial your project (defaults to current directory)"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files in the destination directory",
    ),
):
    """Initialize a new project by copying example files from the package."""
    console = Console()
    dest_path = Path(path + "/examples").resolve()
    os.mkdir("agents")
    os.mkdir("tools")
    os.mkdir("tests")
    os.mkdir("runtime")

    # Check if destination exists and is not empty
    if dest_path.exists() and any(dest_path.iterdir()) and not force:
        console.print(
            "⚠️  Destination directory is not empty. Use --force to overwrite existing files.",
            style="yellow",
        )
        raise typer.Exit(1)

    with Status("[bold green]Copying example files...", console=console):
        try:
            # Get the package's examples directory using importlib.resources
            # Replace 'your_package_name' with your actual package name
            with resources.path("agentic_examples", "") as examples_path:
                copy_examples(examples_path, dest_path, console)

            console.print("\n✨ Examples copied successfully!", style="bold green")
            console.print(f"📁 Location: {dest_path}", style="blue")

        except ModuleNotFoundError:
            console.print(
                "Error: Could not find examples directory in package.", style="red"
            )
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"Error initializing project: {str(e)}", style="red")
            raise typer.Exit(1)

@app.command()
def init_runtime_directory(
    path: str = typer.Argument(
        "./runtime", help="Directory to initial your project (defaults to ./runtime)"
    ),
):
    """Initialize runtime directory for agents to store state, adds its path as a setting"""
    absolute_path = Path(path).resolve()
    os.makedirs(absolute_path, exist_ok=True)
    
    # Add to settings
    settings.set("AGENTIC_RUNTIME_DIR", absolute_path)

# make a "run" command which executes a shell with all the args
@app.command()
def run(args: List[str]):
    """Copies secrets into the Environment and Runs a shell command"""
    secrets.copy_secrets_to_env()
    os.execvp("sh", ["sh", "-c", " ".join(args)])


@app.command()
def index_file(
    index_name: str,
    file_path: str,
    embedding_model: str = typer.Option(
        "BAAI/bge-small-en-v1.5",
        help="FastEmbed model name for text embedding"
    ),
    chunk_threshold: float = typer.Option(
        0.5,
        min=0.1,
        max=1.0,
        help="Semantic similarity threshold for chunking"
    ),
    chunk_delimiters: str = typer.Option(
        ". ,! ,? ,\n",
        help="Comma-separated delimiters for fallback chunk splitting"
    ),
):
    from agentic.utils.rag_helper import rag_index_file
    console = Console()

    try:
        rag_index_file(
            file_path,
            index_name,
            chunk_threshold,
            chunk_delimiters,
            embedding_model,
        )    
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}")
        raise typer.Exit(1)

        
@app.command()
def delete_document(
    index_name: str,
    document_identifier: str,  # Changed from file_path to accept both
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    from agentic.utils.rag_helper import (
        init_weaviate,
        delete_document_from_index,
        check_document_in_index,
        get_document_id_from_path,
        get_document_metadata,
    )

    """Delete a document using its ID or filename/path"""
    console = Console()
    
    try:
        with Status("[bold green]Initializing Weaviate...", console=console):
            client = init_weaviate()
            
        if not client.collections.exists(index_name):
            console.print(f"[yellow]⚠️ Index '{index_name}' does not exist[/yellow]")
            raise typer.Exit(0)
            
        collection = client.collections.get(index_name)
        
        # Determine input type (ID or filename/path)
        if len(document_identifier) == 64 and all(c in '0123456789abcdef' for c in document_identifier.lower()):
            document_id = document_identifier
            input_type = "ID"
            filename = "unknown"  # Will get actual filename from metadata
        else:
            document_id, filename = get_document_id_from_path(document_identifier)
            input_type = "filename"
        
        # Verify document exists
        if not check_document_in_index(collection, document_id):
            if input_type == "ID":
                console.print(f"[yellow]⚠️ Document with ID '{document_identifier}' not found[/yellow]")
            else:
                console.print(f"[yellow]⚠️ Document '{document_identifier}' (ID: {document_id[:8]}...) not found[/yellow]")
            raise typer.Exit(0)
            
        # Get actual filename for confirmation
        metadata = get_document_metadata(collection, document_id)
        filename = metadata["filename"] if metadata else filename
            
        if not confirm:
            console.print(f"[red]⚠️ Will delete ALL chunks for document '{filename}'[/red]")
            typer.confirm("Are you sure?", abort=True)
            
        with Status("[bold green]Deleting document chunks...", console=console):
            deleted_count = delete_document_from_index(collection, document_id, filename)
            
        console.print(f"[green]✅ Deleted {deleted_count} chunks for document '{filename}'[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
    finally:
        if client:
            client.close()

@app.command() 
def delete_index(
    index_name: str,
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Delete entire Weaviate index (collection)"""
    from agentic.utils.rag_helper import (
        init_weaviate,
    )
    console = Console()
    
    try:
        with Status("[bold green]Initializing Weaviate...", console=console):
            client = init_weaviate()
            
        if not client.collections.exists(index_name):
            console.print(f"[yellow]⚠️ Index '{index_name}' does not exist[/yellow]")
            raise typer.Exit(0)
            
        if not confirm:
            console.print(f"[red]⚠️ Will delete ENTIRE index '{index_name}'[/red]")
            typer.confirm("Are you sure?", abort=True)
            
        with Status("[bold green]Deleting index...", console=console):
            client.collections.delete(index_name)
            
        console.print(f"[green]✅ Successfully deleted index '{index_name}'[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
    finally:
        if client:
            client.close()

@app.command()
def list_indexes():
    """List all available Weaviate indexes"""
    from agentic.utils.rag_helper import (
        init_weaviate,
        list_collections,
    )

    console = Console()
    client = None
    try:
        with Status("[bold green]Initializing Weaviate...", console=console):
            client = init_weaviate()
        indexes = list_collections(client)
        console.print(Markdown(f"## Available Indexes ({len(indexes)})"))
        for idx in indexes:
            console.print(f"- {idx}\n")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
    finally:
        if client:
            client.close()

@app.command()
def rename_index(
    source_name: str,
    target_name: str,
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing target index")
):
    """Rename a Weaviate index/collection"""
    from agentic.utils.rag_helper import (
        init_weaviate,
        rename_collection,
    )
    console = Console()
    client = None
    try:
        with Status("[bold green]Initializing Weaviate...", console=console):
            client = init_weaviate()
        
        # Check if source exists first
        if not client.collections.exists(source_name):
            console.print(f"[yellow]⚠️ Source index '{source_name}' does not exist[/yellow]")
            raise typer.Exit(0)
            
        if not confirm:
            console.print(f"[red]⚠️ Will rename index '{source_name}' to '{target_name}'[/red]")
            typer.confirm("Are you sure?", abort=True)
            
        success = rename_collection(client, source_name, target_name, overwrite=overwrite)
        if success:
            console.print(f"[green]✅ Successfully renamed index to '{target_name}'[/green]")
        else:
            if client.collections.exists(target_name):
                console.print("[yellow]⚠️ Target index already exists, use --overwrite to replace it[/yellow]")
            else:
                console.print("[red]❌ Failed to rename index[/red]")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
    finally:
        if client:
            client.close()

@app.command()
def list_documents(index_name: str):
    """List all documents in an index with basic info"""
    from agentic.utils.rag_helper import (
        init_weaviate,
        list_documents_in_collection,
    )
    console = Console()
    try:
        with Status("[bold green]Initializing Weaviate...", console=console):
            client = init_weaviate()
        if not client.collections.exists(index_name):
            console.print(f"[yellow]⚠️ Index '{index_name}' does not exist[/yellow]")
            raise typer.Exit(0)
        collection = client.collections.get(index_name)
        documents = list_documents_in_collection(collection)
        
        console.print(Markdown(f"## Documents in '{index_name}' ({len(documents)})"))
        for doc in documents:
            console.print(
                f"- {doc['filename']} \n"
                f"  ID: {doc['document_id'][:8]}... | "
                f"Chunks: {doc['chunk_count']} | "
                f"Last indexed: {doc['timestamp']}\n"
            )
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
    finally:
        if client:
            client.close()

@app.command()
def show_document(
    index_name: str,
    document_identifier: str 
):
    """Show detailed metadata for a specific document using its ID or filename/path"""
    from agentic.utils.rag_helper import (
        init_weaviate,
        get_document_id_from_path,
        get_document_metadata,
    )

    console = Console()
    try:
        with Status("[bold green]Initializing Weaviate...", console=console):
            client = init_weaviate()
        collection = client.collections.get(index_name)
        
        # Determine if input is a document ID or filename
        if len(document_identifier) == 64 and all(c in '0123456789abcdef' for c in document_identifier.lower()):
            document_id = document_identifier
            input_type = "ID"
        else:
            document_id, filename = get_document_id_from_path(document_identifier)
            input_type = "filename"
        
        metadata = get_document_metadata(collection, document_id)
        
        if not metadata:
            if input_type == "ID":
                console.print(f"[yellow]⚠️ Document with ID '{document_identifier}' not found[/yellow]")
            else:
                console.print(f"[yellow]⚠️ Document '{document_identifier}' (ID: {document_id[:8]}...) not found[/yellow]")
            return
            
        console.print(Markdown(f"## Document Metadata ({metadata['filename']})"))
        console.print(f"- ID: {metadata['document_id']}")
        console.print(f"- Source URL: {metadata['source_url']}")
        console.print(f"- MIME Type: {metadata['mime_type']}")
        console.print(f"- Fingerprint: {metadata['fingerprint'][:8]}...")
        console.print(f"- Total Chunks: {metadata['total_chunks']}")
        console.print(f"- Last Indexed: {metadata['timestamp']}")
        console.print(Markdown("\n## Summary\n" + metadata['summary'] + "\n\n"))
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
    finally:
        if client:
            client.close()

@app.command()
def search(
    index_name: str,
    query: str,
    embedding_model: str = typer.Option(
        "BAAI/bge-small-en-v1.5",
        help="FastEmbed model name matching the index's embedding model"
    ),
    limit: int = typer.Option(5, min=1, max=100),
    filter: Optional[str] = typer.Option(None, help="Filter in key:value format"),
    hybrid: bool = typer.Option(False, "--hybrid", help="Enable hybrid search combining vector and keyword"),
    alpha: float = typer.Option(0.5, min=0.0, max=1.0, help="Weight between vector (1.0) and keyword (0.0) search")
):
    """Search documents with hybrid search support"""
    from agentic.utils.rag_helper import (
        init_weaviate,
        init_embedding_model,
        search_collection
    )
    console = Console()
    try:
        with Status("[bold green]Initializing Weaviate...", console=console):
            client = init_weaviate()
            
        if not client.collections.exists(index_name):
            console.print(f"[yellow]⚠️ Index '{index_name}' does not exist[/yellow]")
            raise typer.Exit(0)
            
        collection = client.collections.get(index_name)
        filters = {}
        if filter:
            if ":" not in filter:
                console.print(f"[red]❌ Invalid filter format: '{filter}'. Use key:value[/red]")
                raise typer.Exit(1)
            key, value = filter.split(":", 1)
            filters[key.strip()] = value.strip()
        
        with Status("[bold green]Initializing model...", console=console):
            embed_model = init_embedding_model(embedding_model)
            
        with Status("[bold green]Searching...", console=console):
            results = search_collection(
                collection=collection,
                query=query,
                embed_model=embed_model,
                limit=limit,
                filters=filters,
                hybrid=hybrid,
                alpha=alpha
            )
            
        console.print(Markdown(f"## Search Results ({len(results)})"))
        for idx, result in enumerate(results, 1):
            console.print(Markdown(f"### Result {idx} - {result['filename']}"))
            console.print(f"- Source: {result['source_url']}")
            console.print(f"- Date: {result['timestamp']}")
            console.print(f"- Distance: {result.get('distance', 'N/A') if result.get('distance') is not None else 'N/A'}")
            console.print(f"- Score: {result.get('score', 'N/A') if result.get('score') is not None else 'N/A'}")
            console.print(Markdown("\n**Content:**\n" + result["content"][:500] + "...\n"))
            
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
    finally:
        if client:
            client.close()

# Create a dashboard command group
dashboard_app = typer.Typer(name="dashboard", help="Manage the dashboard UI")

@dashboard_app.callback()
def dashboard_callback():
    """Manage the dashboard UI."""
    # Check if the dashboard package is installed
    try:
        importlib.import_module("agentic.dashboard")
    except ImportError:
        typer.echo("Dashboard package not installed. Install with 'pip install agentic-framework[dashboard]'")
        raise typer.Exit(1)

@dashboard_app.command()
def start(
    port: int = typer.Option(None, "--port", "-p", help="Port to run the dashboard on"),
    dev: bool = typer.Option(False, "--dev", help="Run in development mode"),
    agent_path: str = typer.Option(None, "--agent-path", help="Path to the agent configuration file, will start the agent if provided"),
):
    """Start the dashboard server."""
    import threading
    
    if agent_path:
        # Start the agent in a separate thread
        typer.echo(f"Starting agent from {agent_path} in a background thread...")
        agent_thread = threading.Thread(
            target=serve, 
            args=(agent_path,),
            daemon=True  # This ensures the thread exits when the main program exits
        )
        agent_thread.start()
        typer.echo("Agent thread started")
    
    # Start the dashboard in the main thread
    from agentic.dashboard.setup import start_command
    typer.echo("Starting dashboard...")
    start_command(port=port, dev=dev)

@dashboard_app.command()
def build():
    """Build the dashboard for production."""
    from agentic.dashboard.setup import build_command
    build_command()

# Add the dashboard app to the main app
app.add_typer(dashboard_app)

if __name__ == "__main__":
    app()
