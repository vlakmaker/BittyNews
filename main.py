from agents.scraper_agent import ScraperAgent
from config.sources import RSS_SOURCES

agent = ScraperAgent(RSS_SOURCES)
news = agent.fetch()

for item in news[:5]:
    print(item["title"], "-", item["link"])
