# 🧠 BittyNews: Your AI-Curated Digest From the Future

**BittyNews** is a fully automated AI-powered news digest built by a tinkerer tired of fluff, doomscrolling, and RSS rot. It scrapes, filters, summarizes, and emails only the most relevant AI and tech news — cleanly, locally, and reliably.

No distractions. No clickbait. Just signal.

---

## ✨ What It Does

BittyNews:

- 📡 Scrapes RSS feeds from trusted AI/tech news sources
- 📄 Extracts full article text via `newspaper3k`
- 🧠 Tags articles with AI relevance using a local LLM agent
- 📝 Summarizes with a 1–2 sentence LLM output
- 🧾 Stores everything in SQLite
- 📬 Sends daily email digests (via **Brevo**) straight from your domain

It's built modular, configurable, and hackable — whether you're feeding a research log, training an agent, or just keeping your inbox sharp.

---

## 🧩 Pipeline Overview

```mermaid
flowchart TD
    A[RSS Feed] --> B[ScraperAgent]
    B --> C[Full Article Extraction (newspaper3k)]
    C --> D[SQLite Storage]
    D --> E[AIFilterAgent]
    E --> F[SummarizerAgent (LLM)]
    F --> G[Daily Digest Email via Brevo]
```

---

## ⚙️ Tech Stack

- **Python 3.10+**
- `feedparser` (RSS parsing)
- `newspaper3k` (article extraction)
- `sqlite3` (data storage)
- **LLMs via**:
  - `GROQ` (LLaMA 3)
  - `OpenRouter` (fallback)
- **Email delivery**:
  - [Brevo Transactional API](https://www.brevo.com/)
- Modular agents:
  - `ScraperAgent`
  - `AIFilterAgent`
  - `SummarizerAgent`
  - `MailerAgent`

---

## 🚀 Quickstart

```bash
git clone https://github.com/your-repo/bittynews.git
cd bittynews
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set up your `.env`:

```env
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_fallback_key
PRIMARY_GROQ_MODEL=llama3-8b-8192
FALLBACK_OPENROUTER_MODEL=mistralai/mistral-7b-instruct

BREVO_API_KEY=your_brevo_api_key
EMAIL_SENDER=news@yourdomain.com
EMAIL_RECEIVER=you@yourdomain.com
```

Then run the engine:

```bash
python main.py
```

---

## 🗃️ Folder Structure

```
BittyNews/
├── agents/
│   ├── scraper_agent.py
│   ├── ai_filter_agent.py
│   ├── summarizer_agent.py
│   └── mailer_agent.py
├── utils/
│   ├── db_utils.py
│   └── email_utils.py
├── templates/
│   └── newsletter.html
├── config/
│   └── sources.yaml
├── bittynews.db
├── main.py
├── .env
└── README.md
```

---

## 📐 Article Schema

BittyNews stores each article in a local SQLite DB with:

- `id`
- `title`
- `link`
- `source_name`
- `published_at`
- `original_summary` (full content via `newspaper3k` or fallback)
- `is_ai_relevant` (bool)
- `ai_filter_model_used`
- `llm_summary`
- `summarizer_model_used`
- `sent_in_newsletter_at` (timestamp)

---

## ✉️ Example Digest Output

BittyNews sends an HTML email styled like [bittygpt.com](https://bittygpt.com/), readable and mobile-friendly:

```text
🧠 BittyNews Digest — June 08, 2025

📄 Manus has kick-started an AI agent boom in China
Source: MIT Technology Review | June 5, 2025
Summary: Manus, a Chinese AI agent, has sparked a boom in China's AI market, with strong competitors and global ambitions.

📄 The Download: funding a CRISPR embryo startup, and bad news for clean cement
Source: MIT Technology Review | June 5, 2025
Summary: A startup is using CRISPR to create embryo-level enhancements; meanwhile, setbacks for green cement raise sustainability concerns.
```

---

## 📬 Sending via Brevo (Transactional)

To configure email sending:

1. Create a [Brevo](https://www.brevo.com/) account
2. Verify your sending domain (e.g. `bittygpt.com`)
3. Add your Brevo API key to `.env`
4. Customize the HTML in `templates/newsletter.html`
5. BittyNews will send daily digests using Brevo's REST API

---

## 🧪 Testing

You can manually trigger a full pipeline run:

```bash
python main.py
```

This will:

- Fetch new articles
- Store them
- Filter AI-relevant ones
- Generate summaries
- Send out a digest email

Check logs for status updates or errors.

---

## 🔭 Roadmap

- [ ] Add source `tags` and filtering by topic/weight
- [ ] Web UI to browse recent summaries
- [ ] Export to Notion, Markdown, or JSON
- [ ] API endpoint for live summaries
- [ ] Add CI job for daily execution
- [ ] Feed for BittyGPT assistant to ingest daily

---

## 🧠 Why BittyNews Exists

Because most tech newsfeeds suck. Because you don’t need to read 3,000 words of corporate fluff to get one useful idea. Because agents and people alike need structured, relevant, human-readable summaries. Because building things is better than doomscrolling.

Built by a curious mind as part of the [BittyGPT](https://bittygpt.com/) ecosystem.

---

## 🛠️ License

MIT License. Modify, fork, or build your own radar from it. If you do, let us know!

---

## 💬 Questions?

Open an issue, fork the project, or just vibe with the feed. Bitty’s always listening.
