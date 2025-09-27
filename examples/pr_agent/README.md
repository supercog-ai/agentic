# PR summary agent 

This is a PR summary agent with GitHub integrations to automatically attatch a summary when a pull request is opened/reopened.

## Installation and running

This example is designed to be run within a fork of the agentic repository, as it uses features that are still in development and must clone the repository.
However, once the features are released, importing the agentic repository with the following command in the [github actions workflow](pr-summary-agent.yml) should be sufficient.
```
uv pip install "agentic-framework[all,dev]" --extra-index-url https://download.pytorch.org/whl/cpu
```

Create a fork of the agentic repository.
Add [pr-summary-agent.yml](pr-summary-agent.yml) to .github/workflows

Add `PRAgentOpenAIKey` to the github repository secrets, containing a valid OpenAI API key.

Move the folder `pr_agent` containing all the files for the pr agent into the top-most folder, with the repository name.

Create a branch and make changes.

Open a pull request to your main branch.

The action should start running immediately once the PR is opened, leaving a comment under the PR when finished.

## How it works

When a PR opens, the github action clones the repository and puts the differences into a file named PRChanges.patch.
`git diff --merge-base HEAD^1 HEAD > PRChanges.patch`

The main agent is then run, and it generates search queries using this inital patch file. These queries are then put through the [RAG agent](code_rag_agent.py) and the [grep agent](git_grep_agent.py) to return more context.
The RAG agent is configured to index markdown files at startup using agentic's RAGTool. This index is cached to reduce startup times in subsequent runs.
The RAG agent finds relevant documentation and returns it to the main agent.
The grep agent finds code files (currently .py only) with exact matches, which is useful for finding implementations for functions and classes.
The grep agent finds the full function/class the match was found in, which is then returned to the main agent.

This is then all packaged together into a final context window, with the patch file, and search results, separated by file names. 
This is sent to the summary agent, which creates a summary using the branch changes and relavant code/documentation for summary generation.
The main agent then uploads the summary to the PR as a comment, using the GitHub API. 