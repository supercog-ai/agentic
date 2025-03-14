# Rest API

Agentic includes built-in support for your agent to expose a **REST API** using _FastAPI_. This API
is an alternative way to use your agent besides the command line.

To start the API server, using the `serve` method on `AgentRunner`:

    AgentRunner(agent).serve()

Note that you will need to add some idle loop to prevent your program from existing. For convenience
you can start the API server with the CLI:

    agentic serve examples/basic_agent.py

It may be useful to enable lots of (server side) logging:

    AGENTIC_DEBUG=all agentic serve examples/basic_agent.py

The AgentRunner runs a _FastAPI_ service that exposes an interface to your agent.

There is a discovery endpoint which lists all agent paths:

    http://0.0.0.0:8086/_discovery

This will list `/basic_agent` as an available path.

Your agent will expose endpoints at:

    http://0.0.0.0:8086/<name of agent>

like:

    http://0.0.0.0:8086/basic_agent

visit the embedded `/docs` page for quick testing:

    http://0.0.0.0:8086/basic_agent/docs
    

Some of the main endpoints include:

    GET /describe           Get the agent spec
    POST /process           Start a request
    GET /getevents          SSE stream events from a request
    GET /stream_request     Process and stream events in one call



