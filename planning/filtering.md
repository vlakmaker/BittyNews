🧠 Strategic Vision: Smarter Filtering for Relevant News
To make the news genuinely useful (and not just a firehose), your scraper → summarizer → filter pipeline needs layered filtering logic. Here's a breakdown of filtering levels and what to consider at each:

🧱 1. Source-Level Filtering (before fetch)
Filter which sources to scrape depending on:

✅ Your interests (e.g., Verge Tech, Ars Technica AI)

🛑 Avoid sites with clickbait or poor signal-to-noise ratio

How:

Maintain a sources.yaml or .json file with tags, source_category, and weight

Ex: Verge could be tagged tech, AI, consumer, and given weight 0.8 if it's often relevant

🪜 2. Pre-Summary Filtering (after fetch, before LLM call)
Decide which articles to summarize based on:

🧹 Basic Heuristics
🚫 Title keyword blacklist (giveaway, sponsored, opinion)

📉 Discard articles with < N characters (usually junk)

⏱️ Ignore if published_date is too old (unless you're doing a digest)

🧲 Keyword Matching / Scoring
Use a scoring system:

+3 if title or summary contains AI, machine learning, genAI, LLM, OpenAI

+2 for startup, release, tool, integration

-5 for deal, coupon, rumor, etc.

Score → Sort → Pick top N

🤖 3. Post-Summary Semantic Filtering (LLM-powered)
Once you have summaries, use an LLM to assess relevance:

“Would this article be relevant for someone interested in applied AI, open-source tooling, and tech product strategy?”

This lets you:

✅ Keep summaries aligned with your current focus

🧠 Tag or cluster news based on categories (e.g. infra, ethics, product, research)

🗂️ 4. Categorization & Tagging
Automatically tag articles into:

AI / GenAI / OpenAI / Claude

Product News / Tooling / Ecosystem

Regulation / Ethics / Privacy

Infra / APIs / Models

How:

Option A: rule-based on keyword + source combo

Option B: LLM-powered classifier (multi-label prompt)

🧠 Future Intelligence Add-ons
🧭 Relevance Learning Loop: You upvote/downvote articles → weights and filters update

🧠 Profile-Based Context Prompt:

“You are my AI News Assistant. Prioritize articles related to applied GenAI tooling, strategy, and product building. Avoid pure academic research or consumer gadgets unless highly relevant.”

🕵️‍♂️ Trend Detection:
Group similar stories, show trending topics over time.

✅ Recommendation: Start with This Filter Stack
Stage	Filter Type	Action
1	Source tags	Tag sources in config
2	Title/summary keyword filter	Add a basic scoring func
3	LLM relevance post-summary	“Is this relevant to V?” prompt
4	LLM-powered categorization	Add tags to each summary
