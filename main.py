import os
from dotenv import load_dotenv
from agents.scraper import ScraperAgent
from agents.aifiltering import AIFilterAgent
from utils.llm_utils import call_llm

def load_environment():
    dotenv_path = os.path.join(os.getcwd(), '.env')
    print(f"DEBUG: Attempting to load .env from: {dotenv_path}")
    loaded = load_dotenv(dotenv_path)
    print(f"DEBUG: load_dotenv() result (found and loaded .env?): {loaded}")
    print(f"DEBUG: Value of OPENROUTER_API_KEY from os.getenv: '{os.getenv('OPENROUTER_API_KEY')}'")
    print(f"DEBUG: Value of OPENROUTER_BASE_URL: '{os.getenv('OPENROUTER_BASE_URL')}'")
    print(f"DEBUG: Initial MODEL_NAME: '{os.getenv('MODEL_NAME')}'")

def summarize_article(article):
    title = article.get("title", "")
    summary = article.get("summary", "")
    link = article.get("link", "")

    prompt = f"""Summarize this article in 1-2 sentences:

Title: {title}
Summary: {summary}
Link: {link}"""

    return call_llm(prompt)

def main():
    load_environment()

    print("🔍 Fetching articles...")
    scraper = ScraperAgent()
    articles = scraper.fetch()
    print(f"✅ Retrieved {len(articles)} articles.")

    # Filter AI-relevant articles
    ai_filter = AIFilterAgent()
    relevant_articles = []

    print(f"🔍 Filtering {len(articles)} articles for AI relevance...")

    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")
        if ai_filter.is_about_ai(title, summary):
            relevant_articles.append(article)

    print(f"✅ {len(relevant_articles)} AI-related articles retained.")

    # Summarize top N relevant articles
    top_n = min(5, len(relevant_articles))
    print(f"\n🧠 Summarizing top {top_n} articles...\n")

    for article in relevant_articles[:top_n]:
        result = summarize_article(article)
        print(f"📄 Summary: {result}\n")

if __name__ == "__main__":
    main()
