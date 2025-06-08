# BittyNews/main.py
import os
import time
from dotenv import load_dotenv

# Import utility and agent classes
from utils import db_utils # For direct DB interactions from main if needed, and table creation
from agents.scraper.scraper_agent import ScraperAgent
from agents.aifiltering.ai_filter_agent import AIFilterAgent
from agents.summarizer.summarizer_agent import SummarizerAgent

def load_environment_and_debug():
    """Loads .env and prints some initial debug info."""
    # .env loading is also handled by llm_utils and db_utils,
    # but calling it here ensures any main.py specific .env vars are loaded early.
    # python-dotenv is safe to call multiple times.
    dotenv_path = os.path.join(os.getcwd(), '.env')
    loaded = load_dotenv(dotenv_path)
    
    print("--- Initial Environment Debug ---")
    if loaded:
        print(f"DEBUG main: .env successfully loaded from {dotenv_path}")
    else:
        print(f"DEBUG main: WARNING - .env file not found or not loaded from {dotenv_path}")
        
    print(f"DEBUG main: GROQ_API_KEY Loaded: {'Yes' if os.getenv('GROQ_API_KEY') else 'No'}")
    print(f"DEBUG main: OPENROUTER_API_KEY Loaded: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
    print(f"DEBUG main: PRIMARY_GROQ_MODEL: '{os.getenv('PRIMARY_GROQ_MODEL')}'")
    print(f"DEBUG main: FALLBACK_OPENROUTER_MODEL: '{os.getenv('FALLBACK_OPENROUTER_MODEL')}'")
    print("---------------------------------")

def main():
    load_environment_and_debug()

    # --- 1. Scrape and Store New Articles ---
    scraper = ScraperAgent()
    print("\n🔍 Fetching and storing new articles...")
    total_feed_items, newly_added_to_db = scraper.fetch()
    print(f"ℹ️  Scraper processed {total_feed_items} items from feeds, added {newly_added_to_db} new articles to the database.")

    # --- 2. AI Relevance Filtering ---
    ai_filter = AIFilterAgent() # Uses defaults from its __init__ or .env via call_llm
    articles_to_filter = db_utils.get_articles_for_filtering()

    if not articles_to_filter:
        print("\n✅ No new articles to filter for AI relevance.")
    else:
        print(f"\n🔍 Filtering {len(articles_to_filter)} articles for AI relevance...")
        retained_count = 0
        for i, article_dict in enumerate(articles_to_filter):
            article_title = article_dict.get('title', 'No Title')
            print(f"  Filtering article {i+1}/{len(articles_to_filter)}: {article_title[:70]}...")
            
            title_for_filter = article_dict.get("title", "")
            content_for_filter = article_dict.get("original_summary", "") # Use original_summary from DB

            is_relevant = ai_filter.is_about_ai(title_for_filter, content_for_filter)
            
            # Update the database with the filtering result
            db_utils.update_article_ai_relevance(
                link=article_dict["link"], 
                is_relevant=is_relevant,
                model_used=(ai_filter.primary_groq_model_for_agent or os.getenv("PRIMARY_GROQ_MODEL")) # Log model used
            )
            if is_relevant:
                retained_count +=1
            
            # Configurable delay to respect API rate limits
            time.sleep(float(os.getenv("FILTER_DELAY_SECONDS", 1.5)))
        
        print(f"✅ AI relevance filtering complete. {retained_count} articles marked as AI-relevant.")

    # --- 3. Summarization of AI-Relevant Articles ---
    summarizer = SummarizerAgent() # Uses defaults from its __init__ or .env via call_llm
    
    # Determine how many articles to summarize
    # We query for articles that are AI-relevant AND not yet summarized
    # TOP_N_SUMMARIES refers to how many we want to process in this run.
    top_n_to_summarize_config = int(os.getenv("TOP_N_SUMMARIES", 5))
    articles_needing_summary = db_utils.get_articles_for_summarization(limit=top_n_to_summarize_config)

    if not articles_needing_summary:
        print("\n✅ No new AI-relevant articles to summarize.")
    else:
        actual_to_summarize_count = len(articles_needing_summary)
        print(f"\n🧠 Summarizing {actual_to_summarize_count} AI-relevant articles (up to configured top {top_n_to_summarize_config})...\n")

        for i, article_dict in enumerate(articles_needing_summary):
            article_title = article_dict.get('title', 'No Title')
            print(f"  Summarizing article {i+1}/{actual_to_summarize_count}: {article_title[:70]}...")
            
            generated_summary = summarizer.summarize(article_dict) # Pass the whole dict
            
# Update the database with the summary
            db_utils.update_article_llm_summary(
                link=article_dict["link"],
                summary_text=generated_summary,  # <--- Corrected to 'summary_text'
                model_used=(summarizer.primary_model or os.getenv("PRIMARY_GROQ_MODEL"))
            )

            print(f"📄 Article: {article_title}")
            print(f"   Link: {article_dict.get('link')}")
            print(f"   Summary by LLM: {generated_summary}\n")
            
            time.sleep(float(os.getenv("SUMMARY_DELAY_SECONDS", 2.0)))
        
        print(f"✅ Summarization complete for {actual_to_summarize_count} articles.")

    print("\n🎉 BittyNews run complete!")

if __name__ == "__main__":
    # 0. Ensure DB tables are created before anything else
    # This should be called once when the application is first set up,
    # or at the start of each run if it's safe (CREATE TABLE IF NOT EXISTS).
    print("--- Ensuring database schema ---")
    db_utils.create_tables_if_not_exist()
    print("------------------------------\n")
    main()
