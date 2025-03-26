# Debugging

The simplest tools for debugging are using the debug levels in the REPL:
    
    'agents' - Log agent operations
    'tools'  - Log all tool calls
    'llm'    - Log LLM completions
    'all'    - Log everything

Note that you can also combine tags like 'tools,llm':

```
> .debug tools,llm
Debug level set to: tools,llm
```

You can also set the debug level via the `AGENTIC_DEBUG` env var:

    export AGENTIC_DEBUG=tools

    
**Switching models**

Use `.model <model>` to temporarily change the active model of the current agent:

```
[Basic Agent]> .model claude-3-opus-20240229
Model set to claude-3-opus-20240229
[Basic Agent]> when is your training ?
<thinking>
The user is asking when my training occurred. This question does not require any of the provided weather-related tools to answer. The tools are for retrieving current weather, weather forecasts, historical weather data, and historical weather averages for specific locations and dates. None of them are relevant for providing information about my own training.
</thinking>

I do not have specific information about when I was trained. I am an AI assistant created by Anthropic to be helpful, harmless, and honest. The details of my training process are not something I have direct knowledge of.
[claude-3-opus-20240229: 1 calls, tokens: 12 -> 113, 2.98 cents, time: 5.17s tc: 2.98 c, ctx: 125]
```

**Showing chat messages**

Use `.history` to see the list of Messages in the current LLM context.


