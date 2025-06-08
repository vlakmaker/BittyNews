# BittyNews/agents/scraper/scraper_agent.py

import feedparser
from bs4 import BeautifulSoup
from newspaper import Article, Config
import time
import os

# Assuming utils are in the parent directory of 'agents' (i.e., BittyNews/utils/)
# This relative import style works if 'agents' is a package and this is run as part of it.
# For direct script running (python agents/scraper/scraper_agent.py), sys.path needs BittyNews/.
try:
    from utils.source_loader import load_sources
    from utils.db_utils import add_article
except ImportError:
    # Fallback for direct execution if sys.path isn't set up yet by a top-level script
    # This assumes scraper_agent.py is in agents/scraper/ and utils is in ../../utils
    import sys
    # Go up two levels from scraper_agent.py (scraper -> agents -> BittyNews)
    # then into utils
    project_root_for_direct_run = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    utils_path = os.path.join(project_root_for_direct_run, 'utils')
    if utils_path not in sys.path:
        sys.path.insert(0, utils_path)
    if project_root_for_direct_run not in sys.path: # Also add project root for other potential relative imports
        sys.path.insert(0, project_root_for_direct_run)
    
    from source_loader import load_sources # Now should work if utils_path was added
    from db_utils import add_article


class ScraperAgent:
    def __init__(self):
        self.sources = load_sources()
        self.user_agent = os.getenv("SCRAPER_USER_AGENT", "BittyNewsFetcher/1.0 (+https://your-project-url.com)") # Update your project URL
        self.request_timeout = int(os.getenv("SCRAPER_REQUEST_TIMEOUT", 15))
        self.article_fetch_delay = float(os.getenv("ARTICLE_FETCH_DELAY_SECONDS", 2.0))
        self.rss_fallback_threshold = int(os.getenv("RSS_CONTENT_FALLBACK_THRESHOLD", 150)) # Min chars from newspaper3k

        if not self.sources:
            print("DEBUG ScraperAgent: No sources loaded. Check utils/source_loader.py and sources.yml.")
        print(f"DEBUG ScraperAgent: Initialized with {len(self.sources)} configured sources.")

    def _get_text_from_html(self, html_content: str) -> str:
        """Safely extracts plain text from HTML content using BeautifulSoup."""
        if not html_content: return ""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception: return ""

    def _get_content_from_rss_entry(self, entry) -> str:
        """Extracts and cleans text from RSS entry's content, summary, or description."""
        content_html = ""
        if hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list) and len(entry.content) > 0:
                for item in entry.content:
                    if hasattr(item, 'type') and ('html' in item.type.lower() or 'text' in item.type.lower()) and hasattr(item, 'value'):
                        content_html = item.value; break
                    elif hasattr(item, 'value') and not content_html: content_html = item.value
        if not content_html and hasattr(entry, 'summary') and entry.summary: content_html = entry.summary
        if not content_html and hasattr(entry, 'description') and entry.description: content_html = entry.description
        return self._get_text_from_html(content_html)

    def _fetch_full_article_text_with_newspaper3k(self, url: str) -> str:
        """Attempts to download and parse full article text using newspaper3k."""
        if not url: return ""
        try:
            config = Config()
            config.browser_user_agent = self.user_agent
            config.request_timeout = self.request_timeout
            config.fetch_images = False
            config.memoize_articles = False

            article_parser = Article(url, config=config)
            article_parser.download()
            if not article_parser.html: return "" # Download failed or no HTML
            article_parser.parse()
            return article_parser.text.strip() if article_parser.text else ""
        except Exception as e:
            print(f"WARNING ScraperAgent: newspaper3k EXCEPTION for URL '{url}'. Error: {type(e).__name__} - {e}")
            return ""

    def fetch(self) -> tuple[int, int]:
        """Fetches articles, gets content, adds new ones to DB. Returns (total_items, new_items)."""
        newly_added_count, total_items_from_feeds = 0, 0
        if not self.sources: return 0, 0

        print(f"🔎 ScraperAgent: Starting fetch from {len(self.sources)} sources...")
        for source_config in self.sources:
            feed_url, source_name = source_config.get("url"), source_config.get("name", "Unknown Source")
            if not feed_url: continue

            print(f"📡 Fetching RSS: {source_name} ({feed_url})")
            try:
                feed = feedparser.parse(feed_url, agent=self.user_agent)
                if feed.bozo: print(f"WARNING ScraperAgent: Malformed feed for {source_name}: {feed.get('bozo_exception', 'Unknown')}")
                if not feed.entries: continue
                
                total_items_from_feeds += len(feed.entries)
                for entry in feed.entries:
                    article_link = entry.get("link")
                    entry_title = entry.get('title', 'No Title Provided').strip()
                    if not article_link: continue

                    print(f"  Processing: {entry_title[:60]}...")
                    time.sleep(self.article_fetch_delay)

                    main_content = self._fetch_full_article_text_with_newspaper3k(article_link)
                    if not main_content or len(main_content) < self.rss_fallback_threshold:
                        rss_content = self._get_content_from_rss_entry(entry)
                        if len(rss_content) > len(main_content if main_content else ""):
                            main_content = rss_content
                            # print(f"DEBUG ScraperAgent: Used RSS fallback for {article_link[:50]}...") # Optional debug

                    article_data = {
                        "link": article_link, "title": entry_title, "source_name": source_name,
                        "original_summary": main_content,
                        "published": entry.get("published"), "published_parsed": entry.get("published_parsed")
                    }
                    if add_article(article_data): newly_added_count += 1
            except Exception as e:
                print(f"❌ ERROR ScraperAgent: Processing feed for {source_name}. Error: {e}")
        
        print(f"✅ ScraperAgent: Processed {total_items_from_feeds} feed items. Added {newly_added_count} new articles.")
        return total_items_from_feeds, newly_added_count

# To test this script directly (e.g., python agents/scraper/scraper_agent.py):
# 1. Make sure you have a .env file in the BittyNews project root.
# 2. Make sure you have a sources.yml file in the BittyNews project root.
# 3. Ensure utils/db_utils.py and utils/source_loader.py are correct.
if __name__ == '__main__':
    print("--- Running ScraperAgent Test (Direct Execution) ---")
    # The sys.path modification at the top handles imports for direct run.
    try:
        from utils import db_utils
        db_utils.create_tables_if_not_exist()
    except Exception as e_db:
        print(f"ERROR setting up database for test: {e_db}")
        exit()

    scraper = ScraperAgent()
    if not scraper.sources:
        print("Test aborted: No sources loaded. Check configuration.")
    else:
        # Optional: Clear DB for a totally fresh test run
        # print("Clearing articles from DB for test...")
        # db_utils.clear_all_articles() # You'd need to implement this in db_utils

        total, new = scraper.fetch()
        print(f"\n--- ScraperAgent Test Summary ---")
        print(f"Total items from feeds: {total}")
        print(f"New articles added to DB: {new}")

        if new > 0: # Show some proof if new articles were added
            conn = db_utils.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, source_name, length(original_summary) as summary_len FROM articles ORDER BY id DESC LIMIT ?", (min(3, new),))
            for row in cursor.fetchall():
                print(f"  DB Sample: ID={row['id']}, Source='{row['source_name']}', Title='{row['title'][:40]}...', SummaryLen={row['summary_len']}")
            conn.close()
