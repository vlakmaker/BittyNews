# agents/summarizer/summarizer_agent.py
from utils.llm_utils import call_llm # Assuming call_llm is in BittyNews/utils/llm_utils.py

class SummarizerAgent:
    def __init__(self, 
                 primary_model: str = None, 
                 fallback_model: str = None,
                 max_input_chars: int = 7000 # Default max characters for title + content for summarization
                ):
        self.primary_model = primary_model     # Agent's preferred Groq model
        self.fallback_model = fallback_model   # Agent's preferred OpenRouter fallback
        self.max_input_chars = max_input_chars
        # Default system prompt specific to summarization
        self.system_prompt = "You are an expert news summarizer. Your goal is to provide a concise and informative 1 to 2 sentence summary of the provided article content. Focus on the main topic and key takeaways."

    def summarize(self, article: dict) -> str:
        """
        Summarizes a given article using the configured LLM.
        Handles input truncation and uses primary/fallback models.
        """
        title = article.get("title", "No Title")
        # Prefer 'summary' if available, then 'description', then a default.
        # In your RSS feeds, 'summary' is usually the main content snippet.
        content_to_summarize = article.get("summary", article.get("description", "No content available for summarization."))

        # Truncate title if it's excessively long for the prompt
        if len(title) > 250: # Keep title relatively concise in the prompt
            trimmed_title = title[:250] + "..."
        else:
            trimmed_title = title
        
        # Combine what we're sending (excluding fixed prompt parts for now)
        # and check its length
        input_for_llm = f"Title: {trimmed_title}\n\nContent: {content_to_summarize}"

        if len(input_for_llm) > self.max_input_chars:
            # Calculate how much to take from content_to_summarize
            # Max length for content = max_input_chars - length of "Title: " - length of trimmed_title - length of "\n\nContent: "
            available_chars_for_content = self.max_input_chars - (len("Title: ") + len(trimmed_title) + len("\n\nContent: "))
            if available_chars_for_content > 0:
                trimmed_content = content_to_summarize[:available_chars_for_content] + " [CONTENT TRUNCATED]"
            else: # Title itself is too long, just send a very short truncated content
                trimmed_content = content_to_summarize[:100] + " [CONTENT HEAVILY TRUNCATED]"
            
            input_for_llm = f"Title: {trimmed_title}\n\nContent: {trimmed_content}"
            print(f"[SummarizerAgent] Input content truncated for title: {trimmed_title[:50]}...")
        
        if content_to_summarize == "No content available for summarization." or not content_to_summarize.strip():
            print(f"[SummarizerAgent] No content to summarize for title: {trimmed_title[:50]}")
            return "[Summary N/A - No content provided]"

        prompt = (
            f"{input_for_llm}\n\n"
            f"Please provide a 1-2 sentence summary:"
        )

        # Use the specific parameter names expected by your call_llm function
        summary_text = call_llm(
            prompt=prompt,
            primary_groq_model_override=self.primary_model,
            fallback_openrouter_model_override=self.fallback_model,
            system_prompt=self.system_prompt
        )

        if "Error:" in summary_text:
            print(f"[SummarizerAgent] LLM call failed during summarization. Title: {trimmed_title[:50]}... Details: {summary_text}")
            # Return a more specific error indicating which step failed
            return f"[Summary unavailable due to LLM error: {summary_text.replace('Error: ', '')}]"
        
        return summary_text.strip()
