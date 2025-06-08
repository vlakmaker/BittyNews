import sqlite3

def init_db():
    conn = sqlite3.connect("bittynews.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE NOT NULL,
            title TEXT,
            source_name TEXT,
            original_summary TEXT,
            published_at TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_ai_relevant BOOLEAN,
            ai_filter_model_used TEXT,
            llm_summary TEXT,
            summarizer_model_used TEXT,
            sent_in_newsletter_at TIMESTAMP,
            user_saved BOOLEAN DEFAULT FALSE,
            user_marked_interesting BOOLEAN DEFAULT FALSE
        );
    ''')
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

if __name__ == "__main__":
    init_db()
