# agents/aifiltering/ai_filter_agent.py
from utils.llm_utils import call_llm

class AIFilterAgent:
    def __init__(self, primary_groq_model="llama3-8b-8192", fallback_or_model=None): # Renamed for clarity
        # self.model is now more specific
        self.primary_groq_model_for_agent = primary_groq_model
        self.fallback_openrouter_model_for_agent = fallback_or_model 
        # If fallback_or_model is None, call_llm will use the .env default for OpenRouter fallback

    def is_about_ai(self, title: str, summary: str) -> bool:
        # Truncate to stay within context limits. Adjust these values as needed.
        # Consider that the prompt itself adds tokens.
        max_title_chars = 200
        max_summary_chars_for_filtering = 3500 # Roughly 1000-1200 tokens. Adjust based on model.
                                              # Llama3 8B has 8192 tokens context.
                                              # Prompt is ~50 tokens. Output is 1 token ("yes"/"no").
                                              # So, you have ~8100 tokens for title+summary.
                                              # 3500 chars for summary + 200 for title is ~1200 tokens. Plenty of room.

        trimmed_title = title[:max_title_chars]
        
        # Truncate summary if it's too long
        if len(summary) > max_summary_chars_for_filtering:
            trimmed_summary = summary[:max_summary_chars_for_filtering] + " [SUMMARY TRUNCATED]"
            print(f"[AIFilterAgent] Summary truncated for title: {trimmed_title[:50]}...")
        else:
            trimmed_summary = summary

        prompt = (
            "You are an AI content filter. Determine whether the following article is primarily about artificial intelligence, machine learning, deep learning, neural networks, or related AI technologies.\n"
            f"Title: {trimmed_title}\n\n"
            f"Summary: {trimmed_summary}\n\n"
            "Respond only with 'yes' or 'no'."
        )
        try:
            # Use the correct parameter names for the call_llm function
            response_content = call_llm(
                prompt,
                primary_groq_model_override=self.primary_groq_model_for_agent,
                fallback_openrouter_model_override=self.fallback_openrouter_model_for_agent
            ).strip().lower()

            if "Error:" in response_content: # Check if call_llm returned an error message
                print(f"[AIFilterAgent] LLM call failed during AI relevance check: {response_content} for title: {trimmed_title[:50]}")
                return False # Default to False on error
            
            return response_content.startswith("yes")
        except Exception as e: # Catch any other unexpected exceptions from strip(), lower() etc.
            print(f"[AIFilterAgent] Unexpected error during AI relevance check: {e} for title: {trimmed_title[:50]}")
            import traceback
            traceback.print_exc()
            return False
