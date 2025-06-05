# utils/llm_utils.py

import os
import requests
import json
from dotenv import load_dotenv

# --- Environment Variable Loading ---
# Construct the absolute path to the .env file, assuming it's in the parent directory
# (e.g., if this file is in BittyScout/utils/, .env is in BittyScout/)
actual_dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
print(f"DEBUG: Attempting to load .env from: {actual_dotenv_path}")

# Load .env file. override=True ensures .env vars take precedence over existing os env vars.
# verbose=True provides output from python-dotenv about its actions.
found_dotenv = load_dotenv(dotenv_path=actual_dotenv_path, override=True, verbose=True)
print(f"DEBUG: load_dotenv() result (found and loaded .env?): {found_dotenv}")

# --- Global Configuration Variables ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "mistralai/mistral-7b-instruct") # Default model

# Debug prints for loaded variables
print(f"DEBUG: Value of OPENROUTER_API_KEY from os.getenv: '{OPENROUTER_API_KEY}'")
if OPENROUTER_API_KEY:
    print(f"DEBUG: Length of OPENROUTER_API_KEY: {len(OPENROUTER_API_KEY)}")
else:
    print("DEBUG: WARNING! OPENROUTER_API_KEY is None or empty after attempting to load .env.")

print(f"DEBUG: Value of OPENROUTER_BASE_URL: '{OPENROUTER_BASE_URL}'")
print(f"DEBUG: Initial MODEL_NAME: '{MODEL_NAME}'")

AVAILABLE_MODELS = {
    "openai/gpt-3.5-turbo": "Fast and affordable general-purpose model.",
    "openai/gpt-4-turbo": "Advanced reasoning and context retention.",
    "anthropic/claude-3-opus": "High-end Claude 3 model, great for reasoning.",
    "anthropic/claude-3-sonnet": "Mid-range Claude 3 with good balance.",
    "anthropic/claude-3-haiku": "Fastest Claude 3, good for lightweight tasks.",
    "meta-llama/llama-3-8b-instruct": "LLaMA 3 8B, solid open-source performance.",
    "meta-llama/llama-3-70b-instruct": "LLaMA 3 70B, larger and more accurate.",
    "mistralai/mistral-7b-instruct": "Small, fast open-source model.",
    "mistralai/mixtral-8x7b-instruct": "Mixture of experts for efficiency.",
    "google/gemini-pro": "Multimodal model from Google.",
}

def set_model(model_name: str):
    """
    Sets the global MODEL_NAME to be used for LLM calls.
    Falls back to the default if the provided model_name is not in AVAILABLE_MODELS.
    """
    global MODEL_NAME # Declare that we are modifying the global variable
    if model_name not in AVAILABLE_MODELS:
        print(f"⚠️  Unknown model '{model_name}'. Falling back to current default: {MODEL_NAME}")
    else:
        MODEL_NAME = model_name
        print(f"✅ Using model: {MODEL_NAME}")

def call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Makes a call to the OpenRouter API with the given prompt and system prompt.
    Uses the globally set MODEL_NAME and OPENROUTER_API_KEY.
    """
    global MODEL_NAME # Ensure we're using the potentially updated global MODEL_NAME
    target_url = f"{OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"

    print(f"DEBUG: API Key inside call_llm before header creation: '{OPENROUTER_API_KEY}'")

    if not OPENROUTER_API_KEY:
        print("❌ ERROR: OPENROUTER_API_KEY is not set. Cannot make LLM call.")
        return "⚠️ Failed to generate response: API key missing or not loaded."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://xuecodex.tech",  # Optional, but helps OpenRouter track usage
        "X-Title": "BittyScout CLI",              # Optional: Helps with dashboard stats
        "Content-Type": "application/json"
    }
    print(f"DEBUG: Headers being sent: {json.dumps(headers, indent=2)}")

    messages = []
    if system_prompt: # Only add system message if system_prompt is not empty
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL_NAME, # Use the globally (potentially updated) MODEL_NAME
        "messages": messages,
        "temperature": 0.7
    }
    print(f"DEBUG: Payload being sent: {json.dumps(payload, indent=2)}")
    print(f"ℹ️  Attempting LLM call to: {target_url} with model {MODEL_NAME}")


    response_text = None  # Initialize to store response text for logging
    try:
        response = requests.post(target_url, headers=headers, json=payload, timeout=30) # Added timeout
        response_text = response.text # Store text for logging in all cases

        print(f"ℹ️  Response Status Code: {response.status_code}")
        # Print only the beginning of the response text to avoid flooding logs if it's huge
        print(f"ℹ️  Response Text (first 500 chars): {response_text[:500] if response_text else 'N/A'}")

        response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses

        result = response.json() # This is where "Expecting value" error might occur if not JSON
        
        if "choices" not in result or not result["choices"]:
            print(f"❌ LLM call failed: 'choices' array missing or empty in response.")
            print(f"Full Response JSON: {result}")
            return "⚠️ Failed to generate response: No choices returned."
        
        choice = result["choices"][0]
        if "message" not in choice or "content" not in choice["message"]:
            print(f"❌ LLM call failed: 'message' or 'content' missing in response structure.")
            print(f"Full Response JSON: {result}")
            return "⚠️ Failed to generate response: Malformed response structure."
            
        return choice["message"]["content"].strip()

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ LLM call failed with HTTP error: {http_err}")
        print(f"Full Response Text (if available): {response_text if response_text else 'N/A'}")
        return "⚠️ Failed to generate response due to HTTP error."
    except requests.exceptions.JSONDecodeError as json_err:
        print(f"❌ LLM call failed to decode JSON: {json_err}")
        print(f"Full Response Text (that was not JSON): {response_text if response_text else 'N/A'}")
        return "⚠️ Failed to generate response due to invalid JSON from server."
    except KeyError as key_err:
        print(f"❌ LLM call failed: Unexpected JSON structure. Missing key: {key_err}")
        # We assume `result` is defined if we reach here from the main try block after response.json()
        print(f"Full Response JSON: {result if 'result' in locals() else 'Response was not parsed as JSON or result not available.'}")
        return "⚠️ Failed to generate response due to unexpected data structure."
    except Exception as e:
        print(f"❌ LLM call failed with an unexpected error: {type(e).__name__} - {e}")
        if response_text:
             print(f"Full Response Text (at time of error): {response_text}")
        return "⚠️ Failed to generate response."

def list_available_models():
    """Prints a list of available LLM models and their descriptions."""
    print("\n🧠 Available LLM Models via OpenRouter:\n")
    for model_id, description in AVAILABLE_MODELS.items():
        print(f"- {model_id:<40}  # {description}")
    print()
