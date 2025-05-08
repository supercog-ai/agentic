from agentic.tools import BrowserUseTool

from agentic.common import Agent, AgentRunner

# This example uses the BrowserUseTool to use the [browser-use](https://browser-use.com/) agent for 
# web browsing. That agent uses Playright and an LLM vision model to automate interactions
# with a real browser.
#
# The browser-use agent is quite token intensive. I have seen good luck using Gemini 2.0 Flash, while
# running into context limits with other models.
#
# By default the agent will create a new browser instance with clean state. You can configure the
# tool to re-use YOUR actual Chrome browser instance by passing the "chrome_instance_path" parameter
# to the BrowserUseTool. Then the browser has access to your cookies and local storage. This is 
# powerful, but obviously also pretty dangerous! So be careful.
#
# To run, you need to install playright and browser-use:
#   pip install playwright
#   pip install browser-use
# 
# Plus whatever API key you need for your selected LLM model.

agent = Agent(
    name="OSS Operator",
    welcome="I am your open source Operator. What task would you like me to perform?",
    instructions="You have a browsing tool function which can browse websites and take actions.",
    #model="gemini/gemini-2.0-flash",
    #model="openai/gpt-4o-mini",
    model="openai/gpt-4o",

    tools=[
        BrowserUseTool(
            chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            model="gemini/gemini-2.0-flash",
        ),
    ],
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
