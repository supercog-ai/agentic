from agentic.common import Agent, AgentRunner
from agentic.events import Event, ChatOutput, Prompt, PromptStarted, TurnEnd
from agentic.models import GPT_4O_MINI, CLAUDE
from agentic.tools import GoogleNewsTool, TavilySearchTool, TextToSpeechTool
import os
from datetime import datetime
from typing import Generator, Any
import requests
import yaml
import sys
import json

# Load prompts from YAML file
prompts_file = os.path.join(os.path.dirname(__file__), 'podcast_short.prompts.yaml')
try:
    with open(prompts_file, 'r') as f:
        prompts = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Error: Could not find prompts file at {prompts_file}")
    print("Please ensure podcast_short.prompts.yaml exists in the examples directory")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error: Invalid YAML in prompts file: {e}")
    sys.exit(1)

class PodcastAgent(Agent):
    def __init__(self, name: str="Podcast Producer", model: str=GPT_4O_MINI):
        super().__init__(
            name,
            welcome="I am the Podcast Producer. Say 'run' to create and publish a new podcast episode.",
            model=model,
        )
        
        # Initialize tools
        self.news_tool = GoogleNewsTool()
        self.search_tool = TavilySearchTool()
        self.tts_tool = TextToSpeechTool()
        
        # Initialize AI news reporter with CLAUDE model
        self.ai_news_reporter = Agent(
            name="AI News Reporter",
            instructions=prompts['AI_NEWS_REPORTER'],
            model=CLAUDE,
            max_tokens=8192,
            tools=[self.news_tool, self.search_tool]
        )
        
        self.sports_reporter = Agent(
            name="Sports Reporter",
            instructions=prompts['SPORTS_REPORTER'],
            model=CLAUDE,
            max_tokens=8192,
            tools=[self.news_tool, self.search_tool]
        )
        
        self.finance_reporter = Agent(
            name="Finance Reporter",
            instructions=prompts['FINANCE_REPORTER'],
            model=CLAUDE,
            max_tokens=8192,
            tools=[self.news_tool, self.search_tool]
        )

        # Initialize news formatter agent
        self.news_formatter = Agent(
            name="News Formatter",
            instructions="""You are an expert broadcast news editor. Your role is to format news content for audio presentation, following these guidelines:
            1. Structure content like professional broadcast news (NPR/BBC style)
            2. Add clear transitions between segments
            3. Format numbers and technical terms for easy speaking
            4. Use broadcast-style sentence structures and pacing
            5. Add natural pauses with appropriate punctuation
            6. Maintain a professional yet conversational tone
            7. Ensure proper emphasis on key information
            8. Remove any visual formatting (bullet points, etc.)
            9. Keep the original information intact while making it more audio-friendly
            10.It should start with: This is supercog news
            11.It should not end with a note saying for example: This version eliminates visual formatting...
            12.It should not say anything that is not related to the news.
            13.If ever it wants to say the anchor, it should say: This is supercog news""",
            model=CLAUDE,
            max_tokens=8192
        )

    def publish_to_transistor(self, audio_file_path: str) -> Generator[Event, Any, Any]:
        """Publish the episode to Transistor.fm"""
        print("\n9. Transistor.fm Publication")
        yield ChatOutput(self.name, {"content": "\n=== Publishing to Transistor.fm ==="})
        
        try:
            print("   - Checking API credentials")
            api_key = os.getenv("TRANSISTOR_API_KEY")
            if not api_key:
                print("   ✗ API key not found")
                raise Exception("TRANSISTOR_API_KEY environment variable not set")
                
            headers = {
                "x-api-key": api_key,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Step 1: Get authorized upload URL
            print("   - Getting upload authorization")
            filename = os.path.basename(audio_file_path)
            auth_response = requests.get(
                "https://api.transistor.fm/v1/episodes/authorize_upload",
                headers=headers,
                params={"filename": filename}
            )
            
            if auth_response.status_code == 200:
                print("   ✓ Upload authorized")
            else:
                print(f"   ✗ Authorization failed: {auth_response.status_code}")
                raise Exception("Failed to get upload authorization")
            
            auth_data = auth_response.json()
            upload_url = auth_data['data']['attributes']['upload_url']
            audio_url = auth_data['data']['attributes']['audio_url']
            
            # Step 2: Upload the audio file
            print("   - Uploading audio file")
            with open(audio_file_path, 'rb') as audio_file:
                upload_response = requests.put(
                    upload_url,
                    data=audio_file,
                    headers={"Content-Type": "audio/mpeg"}
                )
            
            if upload_response.status_code == 200:
                print("   ✓ Audio file uploaded")
            else:
                print(f"   ✗ Upload failed: {upload_response.status_code}")
                raise Exception("Failed to upload audio file")
            
            # Step 3: Create the episode
            print("   - Creating episode")
            current_date = datetime.now().strftime("%Y-%m-%d")
            episode_data = {
                "episode": {
                    "show_id": os.getenv("TRANSISTOR_SHOW_ID", "60214"),
                    "title": f"Supercog News: AI, Sports & Finance Update - {current_date}",
                    "summary": f"Your daily briefing covering the latest in AI technology, sports highlights, and financial market updates for {current_date}",
                    "description": f"Your daily briefing covering the latest in AI technology, sports highlights, and financial market updates for {current_date}",
                    "audio_url": audio_url
                }
            }
            
            create_response = requests.post(
                "https://api.transistor.fm/v1/episodes",
                headers=headers,
                json=episode_data
            )
            
            if create_response.status_code == 201:
                episode_id = create_response.json()['data']['id']
                print(f"   ✓ Episode created with ID: {episode_id}")
            else:
                print(f"   ✗ Episode creation failed: {create_response.status_code}")
                raise Exception(f"Failed to create episode: {create_response.text}")
            
            # Step 4: Publish the episode
            print("   - Publishing episode")
            publish_data = {
                "episode": {
                    "status": "published"
                }
            }
            
            publish_response = requests.patch(
                f"https://api.transistor.fm/v1/episodes/{episode_id}/publish",
                headers=headers,
                json=publish_data
            )
            
            if publish_response.status_code == 200:
                print(f"   ✓ Episode {episode_id} published successfully")
            else:
                print(f"   ✗ Publishing failed: {publish_response.status_code}")
                raise Exception(f"Failed to publish episode: {publish_response.text}")
            
            print("\n=== Podcast Production Complete ===")
            return episode_id
            
        except Exception as e:
            print(f"\n   ✗ Error in publication process: {str(e)}")
            raise

    def next_turn(
        self,
        request: str|Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
        """Main workflow orchestration"""
        
        print("\n=== Starting Podcast Production Workflow ===")
        print(f"Request received at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if request:
            command = request.payload if isinstance(request, Prompt) else request
            print(f"Command received: {command}")
            if command.lower() not in ["run", "create and publish podcast"]:
                print("Invalid command - requesting correct command")
                yield ChatOutput(self.name, {"content": "Please say 'run' or 'create and publish podcast' to start."})
                return

        # Yield the initial prompt
        print("\n1. Initializing podcast production...")
        yield PromptStarted(self.name, {"content": "Starting podcast production..."})

        # Step 1: Generate AI News
        print("\n2. AI News Generation")
        print("   - Requesting AI news from CLAUDE model")
        yield ChatOutput(self.name, {"content": "Generating AI News segment..."})
        ai_news = yield from self.ai_news_reporter.final_result(
            "Generate AI news segment"
        )
        print("   ✓ AI News generation complete")

        # Step 2: Generate Sports News
        print("\n3. Sports News Generation")
        print("   - Requesting sports news from CLAUDE model")
        yield ChatOutput(self.name, {"content": "Generating Sports News segment..."})
        sports_news = yield from self.sports_reporter.final_result(
            "Generate sports news segment"
        )
        print("   ✓ Sports News generation complete")

        # Step 3: Generate Finance News
        print("\n4. Finance News Generation")
        print("   - Requesting finance news from CLAUDE model")
        yield ChatOutput(self.name, {"content": "Generating Finance News segment..."})
        finance_news = yield from self.finance_reporter.final_result(
            "Generate finance news segment"
        )
        print("   ✓ Finance News generation complete")

        # Step 4: Combine and format news
        print("\n5. News Combination")
        print("   - Combining all news segments")
        yield ChatOutput(self.name, {"content": "Combining news segments..."})
        raw_combined_news = f"""
Welcome to Supercog News, your daily briefing on AI, Sports, and Finance.

AI News:
{ai_news}

Sports News:
{sports_news}

Finance News:
{finance_news}

Thank you for listening to Supercog News. Stay informed, stay ahead.
"""
        print("   ✓ News segments combined")
        
        # Step 4b: Format news for broadcast
        print("\n6. Broadcast Formatting")
        print("   - Applying broadcast-style formatting")
        yield ChatOutput(self.name, {"content": "Formatting news for broadcast..."})
        formatted_news = yield from self.news_formatter.final_result(
            f"Format this news content for professional broadcast presentation:\n\n{raw_combined_news}"
        )
        print("   ✓ Broadcast formatting complete")
        
        # Step 5: Text to Speech
        print("\n7. Text-to-Speech Conversion")
        print("   - Converting to audio using Nova voice")
        yield ChatOutput(self.name, {"content": "Converting formatted news to speech..."})
        result = self.tts_tool.generate_speech_file_from_text(
            voice="nova",
            text=formatted_news
        )
        print("   ✓ Text-to-speech conversion complete")
        
        # Parse the JSON response
        print("\n8. Processing Audio File")
        result_dict = json.loads(result)
        if "error" in result_dict:
            print("   ✗ Error in audio generation")
            raise Exception(f"Error generating speech: {result_dict['error']}")

        print("   ✓ Audio file generated successfully")
        
        # Clean up temporary files
        temp_files = [f for f in os.listdir('.') if f.startswith('chunk_') and f.endswith('.mp3')]
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                print(f"   ! Warning: Could not delete temporary file {temp_file}")
        
        # Handle local file path
        if result_dict["audio_url"].startswith("file:///"):
            local_path = result_dict["audio_url"][8:]  # Remove file:/// prefix
            try:
                with open(local_path, "rb") as f:
                    audio_data = f.read()
                os.unlink(local_path)  # Clean up the temporary file
            except Exception as e:
                print(f"   ! Warning: Issue processing audio file: {e}")
                raise
        else:
            raise Exception(f"Unexpected audio URL format: {result_dict['audio_url']}")
        
        # Save audio to file in current directory with date
        current_date = datetime.now().strftime("%Y-%m-%d")
        audio_filename = f"supercog_news_{current_date}.mp3"
        yield ChatOutput(self.name, {"content": f"Generated filename: {audio_filename}"})
        with open(audio_filename, 'wb') as audio_file:
            audio_file.write(audio_data)

        try:
            # Step 6: Publish to Transistor
            episode_id = yield from self.publish_to_transistor(audio_filename)
            
            # Step 7: Notify user
            yield ChatOutput(
                self.name,
                {
                    "content": f"""
Podcast episode published successfully!
Episode ID: {episode_id}
Title: Supercog News: AI, Sports & Finance Update - {datetime.now().strftime("%Y-%m-%d")}
Audio file: {audio_filename}
"""
                }
            )

            yield TurnEnd(
                self.name,
                [{"role": "assistant", "content": f"Podcast episode {episode_id} published successfully"}],
                run_context=None,
            )
            
        except Exception as e:
            # Clean up audio file if there was an error
            try:
                os.unlink(audio_filename)
            except:
                pass
            raise

podcast_agent = PodcastAgent(name="Podcast Producer")

if __name__ == "__main__":
    AgentRunner(podcast_agent).repl_loop()
