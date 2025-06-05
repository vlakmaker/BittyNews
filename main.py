from agents.scraper import ScraperAgent
from agents.summarizer import SummarizerAgent
from config.sources import RSS_SOURCES

def main():
    print("🔍 Fetching articles...")
    scraper = ScraperAgent(RSS_SOURCES)
    articles = scraper.fetch()

    print(f"✅ Retrieved {len(articles)} articles.")
    if not articles:
        return

    print("🧠 Summarizing top 5 articles...")
    summarizer = SummarizerAgent()
    top_articles = articles[:5]

    for article in top_articles:
        summary = summarizer.summarize(article)
        print(f"\n📰 {article['title']}")
        print(f"🔗 {article['link']}")
        print(f"📄 Summary: {summary}")

if __name__ == "__main__":
    main()

