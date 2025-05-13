## Podcast Agents

Podcast agents automate the process of producing and publishing podcasts. They combine AI tools and external APIs to collect, process, and convert content into audio, then publish it online. This makes it easy to build daily or weekly shows from dynamic data sources.

### Short Podcast Agent

The Short Podcast Agent uses a multi-agent pipeline to generate a concise daily news update in AI, Sports, and Finance.

**How it works:**
- Three domain-specific reporter agents (AI, Sports, Finance) use the Google News and Tavily search tools to gather recent headlines and articles and summarizes articles
- A News Formatter agent composes a single, polished audio-ready script
- Text-to-speech tool converts the script to audio
- Final MP3 is uploaded and published via Transistor.fm API
---

### Long Podcast Agent

The Long Podcast Agent compiles full-length podcast episodes from scraped news content

**How it works:**
- Given a list of base URLs for each segment (e.g. https://www.nbcnews.com/news/us-news), it scrapes links to download and summarize news articles
- Text-to-speech tool converts the script to audio
- Combines all audio files using `pydub` into one long podcast episode
- Final MP3 is uploaded to a dev-hosted URL and published via Transistor.fm

### Customization and Environment Variables

To adjust podcast length or summarization depth in the Long Podcast Agent, edit the parameters of the `news_scrape_and_download` function in `create_combined_podcast`:

```python
ast.news_scrape_and_download(
    news_site=site,
    save_file=file_path,
    num_articles=4,
    is_summarize=True,
    sum_wc=500
)
```

- num_articles: number of articles to include per domain segment
- is_summarize: whether or not the article should be summarized
- sum_wc: target word count for each summary

Steps to set up ngrok devtunnel (to host audio url):
1. [Download ngrok](https://ngrok.com/downloads/mac-os)
2. Login, retrieve auth token and run `ngrok config add-authtoken <your_auth_token>`
3. Start local server by running `python -m http.server 8000`
4. In a separate terminal, run `ngrok http 8000`
5. Use the output url as the base_url (e.g. https://0551-135-180-147-242.ngrok-free.app)

---