from agentic.common import Agent, AgentRunner, handoff

agentA = Agent(
    name="Producer",
    welcome="This is the handoff demo.",
    instructions="""
First, print the message 'I am ZZZ  ', 
then call agent B with the message 'hey'.
When agent B finishes then print 'WARNING!'
""",
    tools=[
        handoff(
            Agent(
                name="Agent B",
                instructions="No matter the request, print the message 'and I am B  '",
            )
        )
    ],
    model="openai/gpt-4o",
)

if __name__ == "__main__":
    AgentRunner(agentA) << "go"
