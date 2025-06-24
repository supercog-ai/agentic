from agentic.common import Agent, AgentRunner
from agentic.events import Event, ChatOutput, Prompt, PromptStarted, TurnEnd
from agentic.models import GPT_4O_MINI, CLAUDE

from agentic.tools import GoogleNewsTool, TavilySearchTool, OpenAIWebSearchTool
from agentic.tools import GoogleNewsTool, TavilySearchTool, TextToSpeechTool
import os
from datetime import datetime
from typing import Generator, Any
import requests
import yaml
import sys
import json
import webbrowser

MODEL=GPT_4O_MINI

#TO DO:
#   Delete previous file upon usage
#   Automatically open webpage
#   Location tool: news based on location of user


# Load prompts from YAML file
prompts_file = os.path.join(os.path.dirname(__file__), 'mini_news.yaml')
try:
    with open(prompts_file, 'r') as f:
        prompts = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Error: Could not find prompts file at {prompts_file}")
    print("Please ensure mini_news.yaml exists in the examples directory")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error: Invalid YAML in prompts file: {e}")
    sys.exit(1)

class MiniNewsAgent(Agent):
    def __init__(self, name: str="Mini News Producer", model: str=GPT_4O_MINI):
        super().__init__(
            name,
            welcome="I am the Mini News Producer. Say 'run' to create and publish a new mini news segment.",
            model=model,
        )
        
        # Initialize tools
        self.news_tool = GoogleNewsTool()
        self.search_tool = OpenAIWebSearchTool()
        self.search_tool2 = TavilySearchTool()
        
        # Initialize file attributes
        self.filename = ""
        self.html_filename = ""
    
        # Initialize Headline news reporter with MODEL model
        self.headline_news_reporter = Agent(
            name="Headline News Reporter",
            instructions=prompts['HEADLINE_REPORTER'],
            model=MODEL,
            max_tokens=8192,
            tools=[self.news_tool, self.search_tool]
        )

        # Initialize news formatter agent
        self.news_formatter = Agent(
            name="News Formatter",
            instructions=f"""
            You are an expert broadcast news editorm and webite desiner. Your role is to format news content into brief and easily comprehendable snipits in an HTML format, following these guidelines:
            1. Structure content like a concise social media post by a professional media agency such as CNN or NPR.
            2. Start with a concise headline in bold
            3. Use broadcast-style sentence structures and pacing
            4. Provide context and details as a set of 5 bullet points to give the reader full understanding of the critical points of the news story.
            5. Maintain a professional yet conversational tone
            6. Ensure proper emphasis on key information
            7. Keep the original information intact while making it easy to read as a quick info grab.
            8. It should not say anything that is not related to the news.
            9. Your output should be in the form of an HTML file that creates a visually apealling setting for the news that is being presented.
            10. Do not use CSS as the formating will already be provided.
            11. Make sure to only do the HTML portion of the file.
            12. IMPORTANT: You will be provided with {prompts['WEBSITE_FORMAT']} as the format for the HTML file. Use this information and instead of writing CSS yourself simply use this what is given as the <style> for the website.
            13. Use links to the sources where the information was gotten from using HTML link capabilities to bring users to the webpage of the source.
            14. Try to use diverse sources and make sure that significant information is presented in each summary of the source.
            15. NOTE: Do not ouput anything besides the completed HTML file combined with the CSS provided.
            """,
            model=MODEL,
            max_tokens=8192
        )

    def write_file(self, html_data: str, current_date: str):
        filename = f"mini_news_{current_date}.html"
        self.html_filename = filename  # Update the instance variable
         
        # Save to mini_news folder
        mini_news_dir = os.path.dirname(__file__)
        full_path = os.path.join(mini_news_dir, filename)

        print(f"Writing file: {full_path}")
        
        # Remove ```html and ``` markers if present
        if html_data.startswith("```html") and html_data.endswith("```"):
            html_data = html_data[7:-3].strip()  # Remove first 7 and last 3 characters
        with open(full_path, 'w', encoding='utf-8') as html_file:
            html_file.write(f"{html_data}")
        return full_path
    
    def next_turn(
        self,
        request: str|Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
        """Main workflow orchestration"""
        
        print("\n=== Starting Mini News Production Workflow ===")
        print(f"Request received at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if request:
            command = request.payload if isinstance(request, Prompt) else request
            print(f"Command received: {command}")
            if command.lower() not in ["run", "create and publish mini news"]:
                print("Invalid command - requesting correct command")
                yield ChatOutput(self.name, {"content": "Please say 'run' or 'create and publish mini news' to start."})
                return

        # 1. Yield the initial prompt
        print("\n1. Initializing News Snips production...")
        yield PromptStarted(self.name, {"content": "Starting News Snips production..."})

        # 2. Generate Headline News
        print("\n2. Headline News Generation")
        print("   - Requesting Headline news")
        yield ChatOutput(self.name, {"content": "Generating Headline news segment..."})
        headline_news = yield from self.headline_news_reporter.final_result(
            "Generate Headline news segment"
        )
        print("   ✓ Headline News generation complete")

        # 3. Combine and format news
        print("\n3. News Combination")
        print("   - Combining all news segments")
        yield ChatOutput(self.name, {"content": "Combining news segments..."})
        raw_combined_news = f"""
Supercog Mini News Report

Headline News:
{headline_news}

Supercog Mini News
"""
        print("   ✓ News segments combined")
        
        # 4. Format news for website
        print("\n4. Website Formatting")
        print("   - Applying website-style formatting")
        yield ChatOutput(self.name, {"content": "Formatting news for website..."})
        formatted_news = yield from self.news_formatter.final_result(
            f"Format this news content for news summaries for a social media style website:\n\n{raw_combined_news}"
        )
        print("   ✓ Website formatting complete")
       
        # Save HTML to file in current directory with date
        current_date = datetime.now().strftime("%Y-%m-%d")

        final = f"Mini news for {current_date}:/n/n---/n{formatted_news} published successfully"
        #print(final)
        file_path = self.write_file(formatted_news, current_date)
        print(f"\nNews file created at: file:///{file_path}")
        webbrowser.open(f'file:///{file_path}', new=2)
        yield TurnEnd(
            self.name,
            [{"role": "assistant", "content": final}],
            thread_context=None,
        )
            
        
mini_news_agent = MiniNewsAgent(name="Mini News Producer")

if __name__ == "__main__":
    AgentRunner(mini_news_agent).repl_loop()
