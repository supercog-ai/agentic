# The pipeline problem

The notion of a _code pipeline_ was popularized in data engineering. The idea is simple:
construct a set of re-usable components which have some standardized input/output format,
and then you can flexibly compose these components together into a "pipeline" which
implements an entire process.

The simplest version of this idea is Unix pipes:

    grep -R 'function1' . | wc -l

Eventually people considered that a single-path pipeline wasn't that powerful, so
they generalized to the _graph_, but keeping the idea of re-usuable code at the nodes
and some standard format for passing data along the edges.

This kind of architecture makes good sense when dealing with large amounts of tabular
data, like in a typical data engineering problem. Data formats are standardized as
DataFrames, or CSV, or SQL results, and operation nodes can operate generically on
these inputs, generating new data sets as outputs.

## Over-using the abstraction

But all pipline architectures share similar problems:

- Input and output formats can vary widely
- Because of varying inputs, making _re-usable_ components is very challenging
- Control flow logic is "in the graph", and so it can be hard to understand and change,
or to express complex logic

### Langchain

Original Langchain relied heavily on a _pipeline_ architecture. The LCEL explicitly
defined a "pipe" syntax for chaining "langauge chains" together. Each "chain"
implements this `Runnable` interface which is literally the simplest component
interface you can have:

    def run(input: Any) -> Any:

the problem is a component could do anything. The interface doesn't constrain how
it operates in any way. And because we have externalized control flow into the
pipeline, the only thing you can implement is the single path:

    chain1 | chain2 | chain3

and your inputs and outputs are basically untyped dicts. Can you tell at a glance
what this code is supposed to do?

```
example
```

Recognizing that simple pipelines wouldn't be enough to support more complex control
flow for agents, Langchain (the co) introduced Langgraph.

### LangGraph

LangGraph generalizes the pipeline now to a graph. But all of our original problems
remain. LangGraph "nodes" are not very re-usable, since they can do anything and take
any input. And data passing between nodes is now in this untyped `state` dict which
can hold anything.

And we still have externalized control flow into the graph, modeled as nodes and edges,
and so following/changing that flow is simply difficult. You can see the abstraction
breaking down when you get to trying to implement human-in-the-loop, or when you
start seeing the introduction of `Command` and `goto` and `Send` objects which explicitly
end-run the normal graph traversal.

Programmers don't naturally think in graphs. They are great for math or specific domains, but as
a general programming construct they are really ugly.

What is more natural? Imperative style programming. Do this, then do this, then if this
then do A or B. This is easy to write and easy to read. 

> If you want to get deep, graphs and pipelines are examples of a general programming architecture
called "inversion of control". Instead of using imperative statements, you externalize config and
control flow decisions to some outer framework. This lets your user then re-configure your software
via these externalized knobs. Useful in some cases, but when YOU are the one running the program,
inversion of control almost always makes things more obscure and harder to understand. So there should
be a **really good reason** why the pattern is being employed.

## ...And now back to AI Agents

The actual important question is: how do we trade-off deterministic orchestration from "LLM-based
orchestration"? Using the LLM for orchestration is great! You just tell it what you want in
plain language and it does it. It can even adapt on the fly to errors or unexpected conditions.
ReAct-style agents are wonderfully simple. 

The problem is that the "single loop ReAct" agent doesn't handle complex tasks very well. Its
reasoning is very simple, so it can't carry out very complex plans. This is why _plan and execute_
agents are generally built with deterministic orchestration.

But creating orchestration in code is work, and that code doesn't easily adapt to a changing environment.
Once you get an AI agent based on a graph with even 5 nodes, things are getting complicated to manage.

So I think there is a good research area around how to build more complex agents that still leverage
the LLM for orchestration.

Can we express the Deep Researcher orchestration as a (team of) ReAct agents?

Researcher:
```
You are writing a research report. Gather the report topic from the user, and ask relevant
clarifying questions you may need to focus the report.
Now call the Report Planner agent to generate the report plan.
Show the plan to the user and ask if they have any feedback or not. 
If they provide feedback then call the Report Planner again. 
Otherwise handoff to the Report Writer agent.
```
Report Writer:
```
You are writing a research report based on the provided report plan. Break the report
into sections (via the text_split function) and call the invoke_agent_loop function with the
sections list and calling the Section Researcher agent.

Now call the invoke_agent_loop function with the results from the Section Researcher
but calling the Final Section Writer agent.

Now call "join_list" function and print the completed report.
```
Section Reseacher:
```
Generate 3 web search queries based on the provided report topic and specific section
topic. Execute those queries and retrieve the full page contents. Now draft the 
report section based on this template:

<Topic> <source content> <written content>...
```
Final Section Writer:
```
You are writing final sections for a research report. Write your section based on
considering the entire draft report.
```


## Conclusion

I like frameworks - they reduce boilerplate code and provide useful patterns for solving the same
problem in a standardized way. But a framework shouldn't be making your code significantly harder to 
read and understand. The framework should be making standard things easy, and getting out of the way
of doing harder things. 

Not to be too cheeky, but if you've recently added a _Goto_ statement to your framework, them maybe 
you need to reconsider the original design?



