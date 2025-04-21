from typing import Callable
import requests
from bs4 import BeautifulSoup
import openai

from agentic.tools.text_to_speech_tool import TextToSpeechTool
from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, ConfigRequirement, Dependency

@tool_registry.register(
    name="PodcastTool",
    description="Tool for downloading and summarizing articles and converting them to podcasts",
    dependencies=[
        Dependency(
            name="beautifulsoup4",
            version="4.13.4",
            type="pip",
        ),
        Dependency(
            name="openai",
            version="1.75.0",
            type="pip",
        ),
    ],
    config_requirements=[
        ConfigRequirement(
            key="OPENAI_API_KEY",
            description="OpenAI API key",
            required=True,
        )
    ],
)

class PodcastTool(BaseAgenticTool):
    def __init__(self):
        super().__init__()

    def get_tools(self) -> list[Callable]:
        return [
            self.download_and_write_article,
            self.gather_urls,
            self.summarize,
            self.news_scrape_and_download,
            self.create_podcast_from_text
        ]
    

    def download_and_write_article(
        self,
        download_url:str,
        save_file: str,
        is_summarize: bool = True,
        sum_wc: int = 500
    ):
        r = requests.get(download_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        content = ""
        success = False
        with open(save_file, "a") as f:
            for title in soup.find_all('title'):
                if len(title.get_text().split()) > 3:
                    ttext = title.get_text()
            for data in soup.find_all("p"):
                content += data.get_text() + '\n'
            if len(content) > 3000:
                if is_summarize:
                    f.write(self.summarize(article=content, wordcount=sum_wc, title=ttext))   
                else:
                    f.write("\n\n"+ ttext + "\n")
                    f.write(content) 
                success = True
        return success
    

    def summarize(
        self,
        article: str,
        wordcount: int,
        title: str, 
        model="gpt-4o"
    ):
        client = openai.OpenAI()
        prompt = "Please summarize the following article titled " + title+ " in detail in " + str(wordcount) + " words in the style of a on-air news reporter. Include a introduction/transition sentence in the beginning: \n"
        prompt += article
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
        res = response.choices[0].message.content
        return res

## PODCAST SPECIFIC FUNCTIONS
    def gather_urls(
        self,
        site_url: str
    ):
        r = requests.get(site_url)
        urls = set()
        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.find_all("a"):
            href = link.get("href")
            if site_url in href: #validates news link
                urls.add(href)
        return urls    
    
    def news_scrape_and_download(
        self,
        news_site: str,
        save_file: str,
        num_articles: int = 5,
        is_summarize: bool = True,
        sum_wc: int = 500
    ):
        with open(save_file, "w") as f:
            f.write("")
        urls = list(self.gather_urls(news_site))
        count = 0
        while count < num_articles and len(urls) > 0:
            curl = urls.pop(0)
            success = self.download_and_write_article(curl, save_file, True)
            if success:
                count += 1
    
    def create_podcast_from_text(
        self,
        save_file: str
    ):
        tts = TextToSpeechTool()
        res = tts.generate_speech_file_from_text(voice="nova", input_file_name=save_file)
        return(res)
