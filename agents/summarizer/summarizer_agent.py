# agents/summarizer/summarizer_agent.py

from utils.llm_utils import call_llm

class SummarizerAgent:
    def summarize(self, article):
        try:
            title = article.get("title", "")
            summary = article.get("summary", "")
            link = article.get("link", "")

            prompt = f"Summarize the following article in 1-2 sentences:\n\nTitle: {title}\n\nSummary: {summary}\n\nLink: {link}"
            system_prompt = "You are a helpful assistant that summarizes technology and AI news articles."

            result = call_llm(prompt=prompt, system_prompt=system_prompt)
            return result

        except Exception as e:
            print(f"Summarization failed: {e}")
            return None

