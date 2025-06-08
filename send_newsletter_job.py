# BittyNews/send_newsletter_job.py

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Assuming utils are in a 'utils' subdirectory from where this script is run (project root)
# If you run this script from project root, these imports should work directly.
# If your project structure or run location is different, adjust sys.path if necessary.
try:
    from utils import db_utils
    from utils import email_utils # Contains send_email_via_brevo
    from utils.llm_utils import loaded_env # To check if .env was loaded by llm_utils (optional check)
except ImportError as e:
    print(f"ERROR: Could not import utility modules. Make sure they are in the 'utils' directory and PYTHONPATH is set if needed. Details: {e}")
    # For direct execution when utils is in a subdirectory from project root:
    import sys
    PROJECT_ROOT_FOR_DIRECT_RUN = os.path.abspath(os.path.dirname(__file__)) # BittyNews/
    if PROJECT_ROOT_FOR_DIRECT_RUN not in sys.path:
         sys.path.insert(0, PROJECT_ROOT_FOR_DIRECT_RUN) # Add BittyNews/ to path
    
    # Retry imports
    from utils import db_utils
    from utils import email_utils
    from utils.llm_utils import loaded_env # Check if llm_utils loaded .env (it should have)


def format_published_date(date_str):
    """Helper to format published_at date string for display."""
    if not date_str:
        return "N/A"
    try:
        # Attempt to parse common datetime formats that might come from RSS or DB
        # This might need adjustment based on how you store/retrieve published_at
        dt_obj = None
        possible_formats = [
            '%Y-%m-%d %H:%M:%S',             # Common SQLite format from strftime
            '%a, %d %b %Y %H:%M:%S %z',     # Common RSS format with timezone
            '%a, %d %b %Y %H:%M:%S %Z',     # Another RSS format
            '%Y-%m-%dT%H:%M:%SZ',           # ISO 8601 UTC
            '%Y-%m-%dT%H:%M:%S%z',          # ISO 8601 with offset
        ]
        for fmt in possible_formats:
            try:
                dt_obj = datetime.strptime(date_str, fmt)
                # If it has timezone info, convert to local or just format.
                # For simplicity, just format as is if parsed.
                break 
            except ValueError:
                continue
        
        if dt_obj:
            return dt_obj.strftime('%B %d, %Y') # e.g., June 10, 2025
        return date_str # Return original if no format matched
    except Exception:
        return date_str # Fallback to original string on any error

def generate_and_send_newsletter():
    print(f"\n--- Starting BittyNews Newsletter Job at {datetime.now()} ---")

    # 1. Load .env (db_utils and email_utils might also do this, but good to ensure here)
    #    If llm_utils already loaded it, this will just confirm.
    if not loaded_env: # Check flag from llm_utils (or just call load_dotenv here)
        print("DEBUG send_newsletter_job: .env not yet loaded by llm_utils, loading now.")
        dotenv_path = os.path.join(os.getcwd(), '.env') # Assumes script run from project root
        load_dotenv(dotenv_path)
        if not os.getenv("BREVO_API_KEY"): # Check crucial var after attempting load
            print("ERROR send_newsletter_job: BREVO_API_KEY not found after .env load. Exiting.")
            return
    else:
        print("DEBUG send_newsletter_job: .env likely already loaded by another module.")


    # 2. Ensure database tables exist
    print("Ensuring database tables exist...")
    db_utils.create_tables_if_not_exist() # Safe to call; does nothing if tables exist

    # 3. Fetch articles for the newsletter
    num_articles_in_newsletter = int(os.getenv("NEWSLETTER_ARTICLE_COUNT", 5)) # Default to 5 articles
    print(f"Fetching up to {num_articles_in_newsletter} AI-relevant, summarized articles for the newsletter...")
    articles_for_newsletter = db_utils.get_articles_for_newsletter(limit=num_articles_in_newsletter)

    if not articles_for_newsletter:
        print("No new articles to include in this newsletter run. Exiting.")
        print("--- BittyNews Newsletter Job Complete (No email sent) ---")
        return

    print(f"Found {len(articles_for_newsletter)} articles to include.")

    # 4. Prepare data for the template (e.g., format dates)
    template_data = []
    for article in articles_for_newsletter:
        template_data.append({
            "title": article["title"],
            "link": article["link"],
            "source_name": article["source_name"],
            "published_at_formatted": format_published_date(article["published_at"]),
            "llm_summary": article["llm_summary"]
        })

    # 5. Render the HTML email template
    print("Rendering HTML template...")
    try:
        # Assuming 'templates' directory is in the same directory as this script (project root)
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        if not os.path.isdir(template_dir): # Basic check
             template_dir = 'templates' # Fallback if __file__ is not reliable (e.g. interactive)
        
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('newsletter.html') # Your template file name
        
        current_date_str = datetime.now().strftime('%B %d, %Y')
        html_content = template.render(
            date=current_date_str,
            articles=template_data
        )
        # print(f"\n--- Rendered HTML (Snippet) ---\n{html_content[:500]}...\n----------------------------") # For debugging template
    except Exception as e:
        print(f"❌ ERROR: Failed to render email template: {e}")
        import traceback
        traceback.print_exc()
        return

    # 6. Send the email
    recipient_email = os.getenv("NEWSLETTER_RECIPIENT_EMAIL")
    sender_email = os.getenv("NEWSLETTER_SENDER_EMAIL") # Should be verified with Brevo
    
    if not recipient_email:
        print("❌ ERROR: NEWSLETTER_RECIPIENT_EMAIL not set in .env. Cannot send newsletter.")
        return
    if not sender_email:
        print("❌ ERROR: NEWSLETTER_SENDER_EMAIL not set in .env. Cannot send newsletter.")
        return

    email_subject = f"BittyNews AI Digest - {current_date_str}"
    
    print(f"Sending newsletter to {recipient_email}...")
    email_sent_successfully = email_utils.send_email_via_brevo(
        recipient_email=recipient_email,
        subject=email_subject,
        html_content=html_content
    )

    # 7. Update database if email was sent successfully
    if email_sent_successfully:
        print("Newsletter email reported as sent successfully by Brevo.")
        article_ids_sent = [article["id"] for article in articles_for_newsletter]
        db_utils.mark_articles_as_sent(article_ids_sent)
        print(f"Marked {len(article_ids_sent)} articles as sent in the database.")
    else:
        print("⚠️ Newsletter email sending failed. Articles will not be marked as sent.")

    print(f"--- BittyNews Newsletter Job Complete at {datetime.now()} ---")


if __name__ == "__main__":
    # This allows you to run `python send_newsletter_job.py` directly
    generate_and_send_newsletter()
