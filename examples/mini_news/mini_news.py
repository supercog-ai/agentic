from agentic.common import Agent, AgentRunner
from agentic.events import Event, ChatOutput, Prompt, PromptStarted, TurnEnd
from agentic.models import GPT_4O_MINI
from agentic.tools import GoogleNewsTool, OpenAIWebSearchTool, ImageGeneratorTool

import os
from datetime import datetime
from typing import Generator, Any
import yaml
import sys
import webbrowser
import subprocess

MODEL=GPT_4O_MINI

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
            welcome="Say 'run' to run the agent.",
            model=model,
        )
        
        # Initialize tools
        self.news_tool = GoogleNewsTool()
        self.search_tool = OpenAIWebSearchTool()
        self.image_tool = ImageGeneratorTool()
        
        # Initialize file attributes
        self.filename = ""
        self.html_filename = ""
    
        # Initialize Headline news reporter with MODEL model
        self.headline_news_reporter = Agent(
            name="Headline News Reporter",
            instructions=prompts['HEADLINE_REPORTER'],
            model=MODEL,
            max_tokens=8192,
            tools=[self.news_tool, self.search_tool, self.image_tool]
        )

        # Initialize news formatter agent
        self.news_formatter = Agent(
            name="News Formatter",
            instructions=f'''You are a professional broadcast news editor and HTML formatter. Your task is to convert the provided news content into clean, readable, and visually appealing HTML. Follow these instructions carefully:
            1. For each news item:
                - Start with a **bold headline**.
                - Generate a uniue and relevant image using the image generation tool that captures the essence of the news story.
                - Present the story as **five concise bullet points** that summarize all key facts.
                - Use broadcast-style tone: professional, clear, and engaging.
            2. Maintain the **original story’s accuracy and details**.
            3. Each bullet point should be a complete sentence, delivering one important idea.
            4. Include an **HTML link to the source article** at the end of each story, using standard `<a href>` formatting.
            5. DO NOT fabricate or infer content — only use what was summarized.
            6. The final output must be a complete HTML document using the provided CSS (in `{prompts['WEBSITE_FORMAT']}`).
                - DO NOT add your own CSS or `<style>` tags.
                - DO NOT output anything besides the final HTML file.
            7. The goal is to replicate a modern digital newsroom’s headline feed (e.g., CNN, NPR, AP).
            8. For each news item, generate an image to match the article.
            9. When generating images:
                - Use the image generation tool to create a unique and relevant image for each news story.
                - The image should capture the essence of the news story with a photo realistic style.
                - Ensure the image is appropriate for the news content and audience.
            ''',
            model=MODEL,
            max_tokens=8192,
            tools=[self.image_tool]
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
        
        print("\n----------------\n Starting Mini News Production\n----------------")
        print(f"Request received at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if request:
            command = request.payload if isinstance(request, Prompt) else request
            print(f"Command received: {command}")
            if command.lower() not in ["run", "create and publish mini news"]:
                print("Invalid command - requesting correct command")
                yield ChatOutput(self.name, {"content": "Say 'run' to rerun the agent"})
                return

        # 1. Yield the initial prompt
        print("\n1. Initializing Mini News production...")
        yield PromptStarted(self.name, {"content": "Starting Mini News production..."})

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
        raw_combined_news = headline_news
        
        f"""
        Supercog Mini News Report

        Headline News:
        {headline_news}

        Supercog Mini News
        """

        
        print(f"\n-----------\nRaw combined news: {raw_combined_news}\n")

        print("   ✓ News segments combined")
        
        # 4. Format news for website
        print("\n4. Website Formatting")
        print("   -- Applying website-style formatting")
        yield ChatOutput(self.name, {"content": "Formatting news for website..."})
        formatted_news = yield from self.news_formatter.final_result(
            f"Format this news content for news summaries for a social media style news website:\n\n{raw_combined_news}"
        )
        print("   --  Website formatting complete")
       
        # Save HTML to file in current directory with date
        current_date = datetime.now().strftime("%Y-%m-%d")

        final = f"Mini news for {current_date}:/n/n---/n{formatted_news} published successfully"
        #print(final)
        file_path = self.write_file(formatted_news, current_date)
        print(f"\nNews file created at: file:///{file_path}")
        
        # Only open in browser on Mac systems
        import platform
        if platform.system() == 'Darwin':  # Darwin is the system name for Mac OS
            webbrowser.open(f'file:///{file_path}', new=2)
        elif platform.system() == 'Linux':
            subprocess.Popen(['python', '-m', 'http.server', '8080'], cwd='/home/sheat/src/supercog/agentic/examples/mini_news')
            # Remove 'agentic/' prefix and handle Windows path separators
            relative_path = file_path.replace('/home/sheat/src/supercog/agentic/examples/mini_news/', '')
            webbrowser.open(f'http://localhost:8080/{relative_path}', new=2)
        else:
            print(f"\nDETECTED SYSTEM: {platform.system()}")
            print("\nUnable to open file in browser. Please open the file manually.")
        yield TurnEnd(
            self.name,
            [{"role": "assistant", "content": final}],
            thread_context=None,
        )
            
        
mini_news_agent = MiniNewsAgent(name="Mini News Producer")

if __name__ == "__main__":
    AgentRunner(mini_news_agent).repl_loop()