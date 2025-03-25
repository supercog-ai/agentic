# Data Model

`Agent` - a named unit of execution which supports one or more operations and maintains a persistent state.

`Thread` - when you interact with an agent you do so in the context of a "thread", which maintains a
history of interactions (events in and events out) with the agent. A Thread has no definite "end" state.

`Run` - requesting the agent to perform an operation constitutes a "run". So Threads are composed of
a sequence of Runs. A Run might be in-process, interrupted, continued, or completed.

`Event` - as the agent runs it publishes events, keyed to the Run and the Thread.

?? "request_id"
