# BittyNews/utils/db_utils.py
import sqlite3
import os
import time # For time.strftime if used with published_parsed
from datetime import datetime # For sent_in_newsletter_at if you implement it

# --- Database Configuration ---
# Assumes utils/db_utils.py and BittyNews/.env & bittynews.db are in BittyNews/ (project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_NAME = os.getenv("DATABASE_NAME", "bittynews.db") # Allow DB name to be configurable
DB_PATH = os.path.join(PROJECT_ROOT, DB_NAME)

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Access columns by name (e.g., row['title'])
    return conn

def create_tables_if_not_exist():
    """Creates the articles table with necessary columns and indexes if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT UNIQUE NOT NULL,
                title TEXT,
                source_name TEXT,          -- Populated by scraper
                original_summary TEXT,     -- Populated by scraper (newspaper3k or RSS content)
                published_at TEXT,       -- From RSS feed, stored as ISO8601 string ideally
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_ai_relevant BOOLEAN,    -- Updated by AIFilterAgent
                ai_filter_model_used TEXT, -- Updated by AIFilterAgent
                llm_summary TEXT,          -- Updated by SummarizerAgent
                summarizer_model_used TEXT,-- Updated by SummarizerAgent
                sent_in_newsletter_at TIMESTAMP, -- For future newsletter feature
                user_saved BOOLEAN DEFAULT FALSE,            -- For future web app
                user_marked_interesting BOOLEAN DEFAULT FALSE -- For future web app
            );
        ''')
        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_link ON articles (link);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_needs_filtering ON articles (is_ai_relevant);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_needs_summarization ON articles (is_ai_relevant, llm_summary);')
        # For newsletter (Phase 2)
        # cursor.execute('CREATE INDEX IF NOT EXISTS idx_newsletter_candidates ON articles (is_ai_relevant, sent_in_newsletter_at, published_at);')
        conn.commit()
        print(f"DEBUG db_utils: Database tables ensured in '{DB_PATH}'!")
    except Exception as e:
        print(f"❌ ERROR db_utils: Error creating tables: {e}")
    finally:
        conn.close()

def add_article(article_data: dict) -> bool: # Changed return to bool: True if added, False if exists/error
    """
    Adds a new article to the database if its link doesn't already exist.
    Expects 'link', 'title', 'source_name', 'original_summary', 
    'published' (string), and 'published_parsed' (time.struct_time) in article_data.
    Returns True if the article was newly inserted, False otherwise (already exists or error).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    published_iso_str = None
    published_parsed_struct = article_data.get("published_parsed")
    if published_parsed_struct:
        try:
            # Format: YYYY-MM-DD HH:MM:SS (UTC is good practice if not specified by feed)
            published_iso_str = time.strftime('%Y-%m-%d %H:%M:%S', published_parsed_struct)
        except Exception as e_time:
            print(f"DEBUG db_utils: Error formatting published_parsed for '{article_data.get('link')}': {e_time}. Using raw 'published' string.")
            published_iso_str = article_data.get("published") # Fallback to original string
    elif article_data.get("published"): # If no struct_time, use the published string as is if it exists
        published_iso_str = article_data.get("published")

    link_val = article_data.get("link")
    title_val = article_data.get("title", "No Title Provided")
    source_name_val = article_data.get("source_name", "Unknown Source") # Key from ScraperAgent
    original_summary_val = article_data.get("original_summary", "")    # Key from ScraperAgent

    if not link_val: # Should have been caught by scraper, but good to check
        print("DEBUG db_utils: Attempted to add article with no link. Skipping.")
        return False

    try:
        cursor.execute('''
            INSERT INTO articles (link, title, source_name, original_summary, published_at, fetched_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            link_val,
            title_val,
            source_name_val,
            original_summary_val,
            published_iso_str
        ))
        conn.commit()
        # print(f"DEBUG db_utils: Inserted article ID {cursor.lastrowid}: {title_val[:50]}...")
        return True # Indicates a new article was added
    except sqlite3.IntegrityError: # This means UNIQUE constraint on 'link' failed (already exists)
        # print(f"DEBUG db_utils: Article already exists (link: {link_val}). Skipping insert.")
        return False
    except Exception as e:
        print(f"❌ ERROR db_utils: Error inserting article '{link_val}': {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def update_article_ai_relevance(link: str, is_relevant: bool, model_used: str | None):
    """Updates the AI relevance status and model used for an article."""
    if not link: return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE articles 
            SET is_ai_relevant = ?, ai_filter_model_used = ?
            WHERE link = ?
        ''', (is_relevant, model_used, link))
        conn.commit()
        # print(f"DEBUG db_utils: Updated AI relevance for '{link}': {is_relevant}")
    except Exception as e:
        print(f"❌ ERROR db_utils: Error updating AI relevance for '{link}': {e}")
    finally:
        conn.close()

def update_article_llm_summary(link: str, summary_text: str, model_used: str | None):
    """Updates the LLM-generated summary and model used for an article."""
    if not link: return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE articles 
            SET llm_summary = ?, summarizer_model_used = ?
            WHERE link = ?
        ''', (summary_text, model_used, link))
        conn.commit()
        # print(f"DEBUG db_utils: Updated LLM summary for '{link}'.")
    except Exception as e:
        print(f"❌ ERROR db_utils: Error updating LLM summary for '{link}': {e}")
    finally:
        conn.close()

def get_articles_for_filtering() -> list[dict]:
    """Retrieves all articles that have not yet been AI-filtered (is_ai_relevant IS NULL)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    articles = []
    try:
        # Fetch all columns needed by AIFilterAgent (title, original_summary, link)
        cursor.execute("SELECT id, link, title, original_summary FROM articles WHERE is_ai_relevant IS NULL ORDER BY fetched_at DESC")
        articles = [dict(row) for row in cursor.fetchall()]
        print(f"DEBUG db_utils: Found {len(articles)} articles for AI filtering.")
    except Exception as e:
        print(f"❌ ERROR db_utils: Error fetching articles for filtering: {e}")
    finally:
        conn.close()
    return articles

def get_articles_for_summarization(limit: int = 5) -> list[dict]:
    """
    Retrieves AI-relevant articles (is_ai_relevant = TRUE) 
    that have not yet been summarized (llm_summary IS NULL).
    Orders by published_at then fetched_at to get newest relevant ones.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    articles = []
    try:
        # Fetch all columns needed by SummarizerAgent (title, original_summary, link, id)
        cursor.execute("""
            SELECT id, link, title, original_summary FROM articles 
            WHERE is_ai_relevant = TRUE AND llm_summary IS NULL 
            ORDER BY published_at DESC, fetched_at DESC 
            LIMIT ?
        """, (limit,))
        articles = [dict(row) for row in cursor.fetchall()]
        print(f"DEBUG db_utils: Found {len(articles)} articles for summarization (limit {limit}).")
    except Exception as e:
        print(f"❌ ERROR db_utils: Error fetching articles for summarization: {e}")
    finally:
        conn.close()
    return articles

# --- Functions for Phase 2: Newsletter (Keep for now, or comment out if not needed immediately) ---
def get_articles_for_newsletter(limit: int = 10) -> list[dict]:
    """Retrieves AI-relevant, summarized articles not yet sent in a newsletter."""
    conn = get_db_connection()
    cursor = conn.cursor()
    articles = []
    try:
        # Ensure you select all necessary fields for the newsletter template
        cursor.execute("""
            SELECT id, link, title, llm_summary, source_name, published_at FROM articles
            WHERE is_ai_relevant = TRUE AND llm_summary IS NOT NULL AND sent_in_newsletter_at IS NULL
            ORDER BY published_at DESC, fetched_at DESC
            LIMIT ?
        """, (limit,))
        articles = [dict(row) for row in cursor.fetchall()]
        print(f"DEBUG db_utils: Found {len(articles)} articles for newsletter (limit {limit}).")
    except Exception as e:
        print(f"❌ ERROR db_utils: Error fetching articles for newsletter: {e}")
    finally:
        conn.close()
    return articles

def mark_articles_as_sent(article_ids: list[int]):
    """Marks a list of articles (by their database IDs) as sent in the newsletter."""
    if not article_ids:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        now_iso = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        update_data = [(now_iso, article_id) for article_id in article_ids]
        cursor.executemany('''
            UPDATE articles
            SET sent_in_newsletter_at = ?
            WHERE id = ? AND sent_in_newsletter_at IS NULL -- Ensure not already marked
        ''', update_data)
        conn.commit()
        print(f"DEBUG db_utils: Marked {cursor.rowcount} articles as sent in newsletter.") # cursor.rowcount for affected rows
    except Exception as e:
        print(f"❌ ERROR db_utils: Error marking articles as sent: {e}")
        conn.rollback()
    finally:
        conn.close()
# --- End of Newsletter Functions ---


if __name__ == "__main__":
    print("--- Running Database Utility Script (db_utils.py) ---")
    print(f"Using database at: {DB_PATH}")
    create_tables_if_not_exist()
    
    print("\nTesting add_article (should skip if already exists):")
    test_article_data = {
        "link": "http://example.com/test-unique-article-" + datetime.now().isoformat(),
        "title": "A Unique Test Article",
        "source_name": "Test Suite",
        "original_summary": "This is the full text of a unique test article.",
        "published_parsed": time.gmtime() # feedparser uses time.struct_time
    }
    if add_article(test_article_data):
        print("Test article ADDED.")
    else:
        print("Test article already existed or failed to add.")

    print("\nTesting get_articles_for_filtering (should find the new one if not filtered):")
    for_filtering = get_articles_for_filtering()
    if any(a['link'] == test_article_data['link'] for a in for_filtering):
        print(f"Test article '{test_article_data['title']}' found for filtering.")
        # Simulate filtering
        update_article_ai_relevance(test_article_data['link'], True, "test_filter_model")
        print("Simulated AI relevance update for test article.")
    else:
        print("Test article not found for filtering (either already filtered or not added).")

    print("\nTesting get_articles_for_summarization (should find it if relevant & not summarized):")
    for_summarization = get_articles_for_summarization(limit=10)
    found_for_summary = False
    for art_s in for_summarization:
        if art_s['link'] == test_article_data['link']:
            print(f"Test article '{art_s['title']}' found for summarization.")
            # Simulate summarization
            update_article_llm_summary(art_s['link'], "This is the LLM summary.", "test_summary_model")
            print("Simulated LLM summary update for test article.")
            found_for_summary = True
            break
    if not found_for_summary and any(a['link'] == test_article_data['link'] for a in get_articles_for_filtering()): # Check if it was filtered but still no summary
         print("Test article was filtered but not picked for summarization yet, or already summarized.")
    elif not found_for_summary:
        print("Test article not found for summarization.")


    print("\n--- Database Utility Script Test Run Complete ---")
