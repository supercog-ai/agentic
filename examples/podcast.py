from agentic.common import Agent, AgentRunner
from agentic.tools.text_to_speech_tool import TextToSpeechTool
from agentic.tools.auth_rest_api_tool import AuthorizedRestApiTool
from agentic.tools.google_news import GoogleNewsTool
from agentic.tools.tavily_search_tool import TavilySearchTool

from agentic.models import CLAUDE, GPT_4O_MINI, GPT_4O
from agentic.common import Agent, Pipeline, RunContext, make_prompt
from agentic.events import Prompt, Event

#model = "groq/llama-3.3-70b-versatile"
model = GPT_4O

def collect_audio_streams(prompt: Prompt, run_context: RunContext) -> Event:
    prompt.set_message(make_prompt(
        """
        {{AI News Reporter}}
        {{Sports Reporter}}
        {{Finance Reporter}}
        """,
        run_context,
    ))

pipeline = Pipeline(
    Agent(
        name=f"AI News Reporter",
        instructions="{{AI_NEWS_REPORTER}}",
        model=CLAUDE,
        tools=[GoogleNewsTool(), TavilySearchTool()],
        max_tokens=8192,
    ),
    Agent(
        name=f"Sports Reporter",
        instructions="{{SPORTS_REPORTER}}",
        model=CLAUDE,
        tools=[GoogleNewsTool(), TavilySearchTool()],
        max_tokens=8192,
        handle_turn_start=lambda prompt, run_context: prompt.set_message("run"),
    ),
    Agent(
        name=f"Finance Reporter",
        instructions="{{FINANCE_REPORTER}}",
        handle_turn_start=lambda prompt, run_context: prompt.set_message("run"),
        model=CLAUDE,
        tools=[GoogleNewsTool(), TavilySearchTool()],
        max_tokens=8192,
    ),
    Agent(
        name="Podcast Producer",
        welcome="I am a podcast producer. I can produce a daily news podcast.",
        instructions="{{FULL_PRODUCER}}",
        model=model,
        max_tokens=16 * 1000,
        tools=[
            TextToSpeechTool(),
            Agent(
                name="TransistorFM",
                welcome="I can work with podcast episodes via the Transistor.fm API.",
                instructions="{{TRANSISTOR_FM}}",
                tools=[AuthorizedRestApiTool("header", "TRANSISTOR_API_KEY", "x-api-key")],
                memories=["Default show ID is 60214"],
                model=model,
            )
        ]
    ),
)

if __name__ == "__main__":
    AgentRunner(pipeline).repl_loop()
