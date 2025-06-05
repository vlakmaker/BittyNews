# agents/scraper/scraper_agent.py
import feedparser

class ScraperAgent:
    def __init__(self, sources):
        self.sources = sources

    def fetch(self):
        all_articles = []
        for url in self.sources:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                all_articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", "")
                })
        return all_articles
