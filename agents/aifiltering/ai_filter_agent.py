from utils.llm_utils import call_llm

class AIFilterAgent:
    def __init__(self, model=None):
        self.model = model  # Optional: override model if needed

    def is_about_ai(self, title: str, summary: str) -> bool:
        prompt = (
            f"Title: {title}\n"
            f"Summary: {summary}\n\n"
            "Is this article about artificial intelligence, machine learning, or related AI technologies? "
            "Respond only with Yes or No."
        )
        response = call_llm(prompt, model_name=self.model).strip().lower()
        return response.startswith("yes")
