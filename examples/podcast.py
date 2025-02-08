from agentic import Agent, AgentRunner
from agentic.tools.text_to_speech_tool import TextToSpeechTool
from agentic.tools.auth_rest_api_tool import AuthorizedRESTAPITool

# producer = Agent(
#     name="Podcast Producer",
#     welcome="I am a podcast producer. I can produce a daily news podcast.",
#     instructions="{{PRODUCER}}",
#     model="gpt-4o-mini",
#     tools=[TextToSpeechTool()],
# )
# reporter = Agent(
#     name="AI News Reporter",
#     instructions="{{REPORTER}}",
#     model="openai/gpt-4o",
# )

# producer.add_tool(reporter)

uploader = Agent(
    name="TransistorFM",
    welcome="I can work with podcast episodes via the Transistor.fm API.",
    instructions="{{TRANSISTOR_FM}}",
    tools=[AuthorizedRESTAPITool('header', 'TRANSISTOR_API_KEY', 'x-api-key')],
    memories=["Default show ID is 60214"],
)

# producer.add_tool(uploader)

# if __name__ == "__main__":
#     AgentRunner(producer).repl_loop()
