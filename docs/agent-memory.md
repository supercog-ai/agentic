# Agent Memory

Agents support multiple types of _memory_:

- Short term memory in "run history" (the chat session) of the agent. Run history consumes
much of the LLM context that the LLM operates on. Agents include this memory type by default.

You can clear your agent's short term memory:

`runner.reset_session()`

- Persistent facts. Facts and data can be stored anywhere, and applied to the agent context
when it runs. Agents expose a `memories` attribute to make loading memories easy:

```
uploader = Agent(
    name="TransistorFM",
    memories=["Default show ID is 60214"],
)
```
but you can also use a `ContextManager` to inject information into the agent context.

- Run history. Agents can persist their "run histories" (chat sessions) so that those
runs can be reviewed later.

- Larger-than-context memory. There are multiple systems for storing memories for your agent
that exceed the context window limits. The most popular is RAG - retrieval augmented generation.
This system allows your agent to store lots and lots of data and intelligently "retrieve" only
part of it to help it answer ("generate") a question.

