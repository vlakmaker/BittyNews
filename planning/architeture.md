bittynews/
│
├── main.py                    # Entry point to run the full pipeline
├── requirements.txt           # Dependencies
├── README.md                  # Project overview
│
├── config/
│   └── sources.yaml           # List of news/blog sources to scrape
│
├── agents/
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── scraper_agent.py   # Fetches articles from sources
│   │
│   ├── summarizer/
│   │   ├── __init__.py
│   │   └── summarizer_agent.py  # Summarizes content using LLM
│   │
│   ├── classifier/
│   │   ├── __init__.py
│   │   └── classifier_agent.py  # Optional: tags article types (e.g. research, product)
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── storage_agent.py   # Saves articles to JSON or SQLite
│   │
│   ├── output/
│   │   ├── __init__.py
│   │   └── web_output_agent.py  # Web display or export
│   │
│   └── manager/
│       ├── __init__.py
│       └── manager_agent.py   # Orchestrates full pipeline
│
└── data/
    └── articles.json          # Stored news summaries
:wq