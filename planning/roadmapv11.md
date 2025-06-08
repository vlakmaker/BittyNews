201~200~# BittyNews Roadmap

Your journey from CLI script to a full web-based product will proceed in three solid phases. Each phase builds incrementally on the last, ensuring minimal waste and maximum learning and value delivery. This roadmap outlines all essential steps, tooling, and good practices for each phase.

---

## Phase 1: Persistence Layer + Cronable CLI

### 🎯 Goal

Make BittyNews persistent and automateable, so that it can reliably fetch, filter, and summarize articles on a schedule.

### ✅ Tasks

#### 1. Create `articles.db` (SQLite)

Use SQLite for simplicity.

**Schema Design:**

```sql
articles (
	  id INTEGER PRIMARY KEY AUTOINCREMENT,
	    link TEXT UNIQUE NOT NULL,
	      title TEXT,
	        source_name TEXT,
	          original_summary_or_description TEXT,
	            published_at TEXT,
	              fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	                is_ai_relevant BOOLEAN,
	                  ai_filter_model_used TEXT,
	                    llm_summary TEXT,
	                      summarizer_model_used TEXT,
	                        sent_in_newsletter_at TIMESTAMP,
	                          user_saved BOOLEAN DEFAULT FALSE,
	                            user_marked_interesting BOOLEAN DEFAULT FALSE
	                            )
	                            ```

	                            #### 2. Refactor CLI

	                            * Scraper: Check DB before inserting articles. Skip if link exists.
	                            * AIFilterAgent: Process only `WHERE is_ai_relevant IS NULL`
	                            * SummarizerAgent: Process only `WHERE is_ai_relevant = TRUE AND llm_summary IS NULL`

	                            #### 3. Add `run_pipeline.py`

	                            * Orchestrates fetching → filtering → summarizing
	                            * Can be scheduled via cron

	                            **Sample Cron (Linux/macOS):**

	                            ```
	                            0 7,19 * * * /path/to/env/bin/python /path/to/BittyNews/run_pipeline.py >> /path/to/BittyNews/logs/cron.log 2>&1
	                            ```

	                            ---

	                            ## Phase 2: HTML Newsletter + Delivery

	                            ### 🎯 Goal

	                            Send out a daily (or twice-daily) AI-filtered newsletter containing summarized articles.

	                            ### ✅ Tasks

	                            #### 1. Create a `newsletter_template.html`

	                            Use Jinja2 for rendering HTML emails.

	                            **Structure:**

	                            * Newsletter date
	                            * Intro paragraph
	                            * Loop through articles:

	                              * Title (link), summary, source, published date

	                              #### 2. Pull Unsent Articles

	                              SQL query example:

	                              ```sql
	                              SELECT * FROM articles WHERE is_ai_relevant = TRUE AND sent_in_newsletter_at IS NULL ORDER BY published_at DESC LIMIT 10;
	                              ```

	                              #### 3. Email Sending Utility (`email_utils.py`)

	                              * Render template with articles
	                              * Send via Mailgun/SendGrid
	                              * Store API keys in `.env`
	                              * After successful send, update `sent_in_newsletter_at`
	                              * Ensure atomic update or guard against duplicates

	                              ---

	                              ## Phase 3: Web App (FastAPI Recommended)

	                              ### 🎯 Goal

	                              Allow user interaction through a web UI — browse articles, save/mark them, view history.

	                              ### ✅ Tasks

	                              #### 1. Backend API with FastAPI

	                              **Endpoints:**

	                              * `GET /articles/`
	                              * `POST /articles/{article_id}/save`
	                              * `POST /articles/{article_id}/mark_interesting`
	                              * (Optional) `POST /auth/login` + user preference endpoints

	                              **Data Models:**

	                              * Use Pydantic for defining schemas

	                              #### 2. Frontend

	                              Options:

	                              * Server-rendered HTML with Jinja2 (simplest)
	                              * JS frontend (Svelte/Vue/React) later

	                              Features:

	                              * Article feed view
	                              * Save/mark buttons
	                              * Login functionality

	                              ---

	                              ## Optional Enhancements (Any Phase)

	                              * Structured configuration (e.g., `config.yaml`)
	                              * Logging with `logging` module
	                              * Retry logic for summarization/failures
	                              * Store model version used per entry
	                              * Article tagging or categorization

	                              ---

	                              ## Summary

	                              This roadmap provides a clear and pragmatic path forward:

	                              * **Phase 1** gives you reliability and automation
	                              * **Phase 2** makes BittyNews useful as a real-world content feed
	                              * **Phase 3** expands the project into a full application with users

	                              Each layer enhances the one before it without creating bottlenecks or waste. It’s exactly how lean AI tools should evolve.

	                              Let’s build! 🚀
	                              
)
