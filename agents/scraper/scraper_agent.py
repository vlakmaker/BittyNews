import feedparser
from utils.source_loader import load_sources

class ScraperAgent:
    def __init__(self):
        self.sources = load_sources()
        print(f"🔎 Loaded {len(self.sources)} sources.")

    def fetch(self):
        all_articles = []

        for source in self.sources:
            feed_url = source.get("url")
            source_name = source.get("name", "Unknown Source")
            if not feed_url:
                continue

            print(f"📡 Fetching from: {source_name} ({feed_url})")
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                article = {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "source": source_name
                }
                all_articles.append(article)

        print(f"✅ Retrieved {len(all_articles)} articles.")
        return all_articles
