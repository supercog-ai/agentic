
from agentic.common import Agent, AgentRunner
from agentic.tools import AuthorizedRestApiTool, PodcastTool, TextToSpeechTool

from agentic.models import GPT_4O
from agentic.common import Agent, AgentRunner

from datetime import datetime
from pydub import AudioSegment
import json
import traceback
import os


def create_combined_podcast():
    """
    Generates a combined podcast audio file by scraping articles from the given list of news segment URLs,
    summarizing their content, converting them to audio, and concatenating them into one MP3 file.
    """
    segment_sites=["https://www.nbcnews.com/news/us-news", "https://www.nbcnews.com/news/world", "https://www.nbcnews.com/tech"]
    base_url='https://<your-ngrok-id>.ngrok-free.app'
    
    ast = PodcastTool()

    audio_dir = os.path.join(os.path.dirname(__file__), "audios")
    os.makedirs(audio_dir, exist_ok=True)

    file_path = os.path.dirname(os.getcwd()) + "/article_scraper_transcript.txt"
    audio_files = []
    try:
        for site in segment_sites:
            ast.news_scrape_and_download(news_site=site, save_file=file_path, num_articles=4, is_summarize=True, sum_wc=500)
            audio_file = ast.create_podcast_from_text(file_path)
            audio_files.append(audio_file)
        combined = AudioSegment.empty()
        for f in audio_files:
            file_info = json.loads(f)
            audio_url = file_info["audio_url"]
            audio_url = audio_url.split("file:///")[-1]
            combined += AudioSegment.from_mp3(audio_url)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_podcast_{timestamp}.mp3"

        output_path = os.path.join(audio_dir, filename)
        combined.export(output_path, format="mp3")

        #devtunnel
        public_audio_url = f"{base_url}/{filename}"

        return json.dumps(
            {"content_type": "audio/mpeg", "audio_url": public_audio_url}
        )

    except Exception as e:
        traceback.print_exc()
        error_message = f"Error generating combined podcast: {str(e)}"
        return json.dumps({"error": error_message})


#transistor fm agent
tfm_inst = """
  You are a helpful assistant. You can call the Transistor API which is used for managing a podcast.
  Here are the API endpoints:

  The top level object is a "Show", and each show contains Episodes.

  GET https://api.transistor.fm/v1 - Return the current authorized user
  GET /v1/shows - Gets the list of Shows
  GET /v1/episodes - Gets a list episodes for a show. Takes show_id parameter, and optional "status" filter parameter (one of draft, scheduled, published)

  POST /v1/episodes - To create a new episode. Takes these parameters:
    episode[show_id] 
    episode[audio_url]
    episode[title]

  PATCH /v1/episodes/{id}/publish - To publish an episode. Takes these parameters:
    id - episode ID
    episode[status] - one of draft, published, scheduled
"""
#transistor fm agent
upload_agent = Agent(
    name="TransistorFM",
    welcome="I can work with podcast episodes via the Transistor.fm API.",
    instructions=tfm_inst,
    tools=[AuthorizedRestApiTool("header", "TRANSISTOR_API_KEY", "x-api-key")],
    memories=["Default show ID is 60214"],
    model=GPT_4O,
    )


inst_comb = """
When started, immedietly execute the following:
1. Call create_combined_podcast to create a combined audio and get the public audio link
2. Call the upload agent, ask it to create and then publish a DRAFT episode using the public audio link on Transistor FM and naming the episode "News Recap from <date> and add the date.
"""

agent = Agent(
    name="Podcast Agent",
    instructions=inst_comb,
    model=GPT_4O,
    tools=[PodcastTool(), TextToSpeechTool(), upload_agent, create_combined_podcast]
)


if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
        