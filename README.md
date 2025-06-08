
# 📰 BittyNews: Your AI-Curated Feed of What Actually Matters

**Welcome to BittyNews**, the AI-powered news pipeline that skips the fluff and surfaces what *actually* matters in tech and AI. Built by a curious mind tired of RSS rot and summarization hell, BittyNews combines smart scraping, LLM filtering, and clear summarization to keep you informed — no doomscrolling required.

---

## 🧠 What Is BittyNews?

BittyNews is a fully automated news curation engine designed to:

- 🛰️ **Scrape** trusted tech and AI sources via RSS
- 🧽 **Clean and extract** full article content with `newspaper3k`
- 🧠 **Filter** for relevance using LLM-based AI tagging (e.g. "is this article about AI?")
- ✍️ **Summarize** in 1–2 clear, contextual sentences using an LLM
- 💾 **Store** everything locally in SQLite for later presentation/export

It's a builder's project. Minimal fluff. Maximal learning. Zero hype cycles.

---

## 🔧 Pipeline Overview

```mermaid
flowchart TD
    A[RSS Feed] --> B[ScraperAgent]
    B --> C[Full Article Extraction (newspaper3k)]
    C --> D[Database Storage]
    D --> E[AI Filtering Agent]
    E --> F[Summarizer Agent (LLM)]
    F --> G[Summaries Stored in DB]
```

Each stage is modular. You can swap LLMs, reroute storage, or use the summaries in your frontend/newsletter/agent project.

---

## ⚙️ Tech Stack

- **Python 3.10+**
- `feedparser` for RSS
- `newspaper3k` for full-article extraction
- `sqlite3` for local persistence
- LLMs via:
  - [GROQ](https://groq.com/) (e.g. LLaMA 3)
  - [OpenRouter](https://openrouter.ai/) fallback
- Custom Agents:
  - `ScraperAgent`
  - `AIFilterAgent`
  - `SummarizerAgent`

---

## 🛠️ Setup

```bash
git clone https://github.com/your-repo/bittynews.git
cd bittynews
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then, set up your `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_fallback_key
PRIMARY_GROQ_MODEL=llama3-8b-8192
FALLBACK_OPENROUTER_MODEL=mistralai/mistral-7b-instruct
```

Run the news engine:

```bash
python main.py
```

---

## 📂 Folder Structure

```
BittyNews/
├── agents/
│   ├── scraper_agent.py
│   ├── ai_filter_agent.py
│   └── summarizer_agent.py
├── utils/
│   └── db_utils.py
├── config/
│   └── sources.yaml
├── bittynews.db
├── main.py
├── .env
└── README.md
```

---

## 🗂️ Article Schema

Each article in `bittynews.db` contains:

- `id`
- `title`
- `link`
- `source_name`
- `published_at`
- `original_summary` (extracted full content)
- `is_ai_relevant` (bool)
- `ai_filter_model_used`
- `llm_summary` (1–2 sentence output)

---

## 🧪 Example Output

```text
📄 Article: Manus has kick-started an AI agent boom in China
Link: https://www.technologyreview.com/...
Summary: Manus, a Chinese AI agent, has sparked a boom in China's AI market, with strong competitors and global ambitions.
```

---

## 🧰 Roadmap Ideas

- [ ] Add source `tags` and `weights` for smarter filtering
- [ ] Export summaries to Markdown, JSON, or Notion
- [ ] Add CI/CD job for daily scraping + summary dump
- [ ] Web frontend or newsletter-friendly export
- [ ] Add retry + error handling for malformed feeds

---

## 🤖 Built With Curiosity, Not Clout

BittyNews was created as part of an experimental AI builder journey — practical tools, minimal dependencies, maximum control. It's not a product. It’s a thinking tool, a feed tuner, and a personal info radar.

**Make it your own.**

---

## 📬 Questions or Ideas?

This project is part of the [BittyGPT](https://bittygpt.com/) ecosystem. Want to build your own AI-powered feed? Got ideas to improve filtering, summarization, or agent design?

→ Open an issue. Or fork and riff.
