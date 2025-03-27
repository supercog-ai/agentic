# Models

Agentic uses [Litellm](https://www.litellm.ai/) as the "LLM router" which allows us
to support most popular LLMs via simple configuration.

Models providers supported include:

* OpenAI
* Anthropic
* Google
* Llama3.x
* Deepseek

and many more.

When you specify the `model` parameter to your Agent, supply a qualified model
name like:

    openai/gpt-4o

or 

    anthropic/claude-3-5-sonnet-20240620

Try using `agentic models` at the command line to get a list of popular models.

## Ollama

Agentic has built-in support for using locally installed models via [Ollama](https://ollama.com/).

To use, first install ollama. Then serve your model:

    ollama run llama3.2:latest

And specify your agent's model:

    model=ollama/llama3.2:latest


