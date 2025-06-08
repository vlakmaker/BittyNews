# main.py
import os
import time # Import time for potential delays
from dotenv import load_dotenv
from agents.scraper.scraper_agent import ScraperAgent # Assuming this path is correct
from agents.aifiltering.ai_filter_agent import AIFilterAgent # Assuming this path
from agents.summarizer.summarizer_agent import SummarizerAgent # Import the agent

# Remove call_llm import from main.py if it's only used by agents
# from utils.llm_utils import call_llm 

def load_environment():
    # This is good, but your llm_utils.py also loads .env. 
    # One load at the start of the app or in the first module needing it is fine.
    # python-dotenv is usually safe to call multiple times (won't overwrite if already loaded unless override=True).
    dotenv_path = os.path.join(os.getcwd(), '.env')
    # print(f"DEBUG main: Attempting to load .env from: {dotenv_path}")
    # loaded = load_dotenv(dotenv_path)
    # print(f"DEBUG main: load_dotenv() result: {loaded}")
    # These debugs are good for initial setup, can be commented out later
    # print(f"DEBUG main: Value of OPENROUTER_API_KEY: '{os.getenv('OPENROUTER_API_KEY')}'")
    # print(f"DEBUG main: Value of GROQ_API_KEY: '{os.getenv('GROQ_API_KEY')}'") # Check if Groq key is loaded
    # print(f"DEBUG main: Value of PRIMARY_GROQ_MODEL: '{os.getenv('PRIMARY_GROQ_MODEL')}'")
    # print(f"DEBUG main: Value of FALLBACK_OPENROUTER_MODEL: '{os.getenv('FALLBACK_OPENROUTER_MODEL')}'")
    pass # llm_utils.py handles .env loading for LLM vars. 
         # If main.py needs other .env vars, load_dotenv() here is fine.

def main():
    load_environment() # Call it once if main or other non-LLM parts need .env vars directly

    print("🔍 Fetching articles...")
    scraper = ScraperAgent()
    # Ensure your ScraperAgent has a method like fetch() or get_jobs()
    # Based on previous files, it was get_jobs()
    articles = scraper.fetch() # Use the correct method name for your ScraperAgent
    
    # Deduplicate articles based on link or title to avoid processing the same article multiple times
    # if it comes from different feeds or appears multiple times in one feed.
    seen_links = set()
    unique_articles = []
    for article in articles:
        link = article.get("link") or article.get("url") # Handle both possible keys
        if link and link not in seen_links:
            unique_articles.append(article)
            seen_links.add(link)
        elif not link: # Keep articles without links if you want, or decide to discard
            unique_articles.append(article) 
            
    print(f"✅ Retrieved {len(articles)} articles, {len(unique_articles)} unique articles (by link).")
    articles_to_process = unique_articles


    # --- AI Filtering ---
    # You can pass specific models for filtering, or let it use .env defaults from llm_utils
    # ai_filter = AIFilterAgent(primary_groq_model="specific-groq-for-filtering") 
    ai_filter = AIFilterAgent() # Uses defaults defined in its __init__ or .env via call_llm
    relevant_articles = []
    print(f"🔍 Filtering {len(articles_to_process)} articles for AI relevance...")

    for i, article in enumerate(articles_to_process):
        print(f"  Filtering article {i+1}/{len(articles_to_process)}: {article.get('title', 'No Title')[:70]}...")
        title = article.get("title", "")
        # Use 'summary' or 'description' from the article for filtering
        content_for_filtering = article.get("summary", article.get("description", ""))
        
        if ai_filter.is_about_ai(title, content_for_filtering):
            relevant_articles.append(article)
        
        # Add a delay to respect rate limits, especially for Groq
        # Adjust this based on observed behavior and API limits (e.g., Groq free tier)
        time.sleep(float(os.getenv("FILTER_DELAY_SECONDS", 1.5))) # Configurable delay

    print(f"✅ {len(relevant_articles)} AI-related articles retained.")

    # --- Summarization ---
    top_n = min(int(os.getenv("TOP_N_SUMMARIES", 5)), len(relevant_articles))
    print(f"\n🧠 Summarizing top {top_n} articles...\n")

    # summarizer = SummarizerAgent(primary_model="specific-groq-for-summaries")
    summarizer = SummarizerAgent() # Uses defaults defined in its __init__ or .env via call_llm

    for i, article_to_summarize in enumerate(relevant_articles[:top_n]):
        print(f"  Summarizing article {i+1}/{top_n}: {article_to_summarize.get('title', 'No Title')[:70]}...")
        # The SummarizerAgent's summarize method now handles truncation
        generated_summary = summarizer.summarize(article_to_summarize) 
        
        print(f"📄 Article: {article_to_summarize.get('title')}")
        print(f"   Link: {article_to_summarize.get('link') or article_to_summarize.get('url')}") # Show the link
        print(f"   Summary by LLM: {generated_summary}\n")
        
        # Add a delay here as well
        time.sleep(float(os.getenv("SUMMARY_DELAY_SECONDS", 2.0))) # Configurable delay

    print("🎉 BittyNews run complete!")

if __name__ == "__main__":
    main()
