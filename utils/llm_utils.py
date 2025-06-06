# BittyNews/utils/llm_utils.py

import os
import requests
import json # Good practice to import if you might use it for debugging payloads
from dotenv import load_dotenv

# --- Environment Variable Loading ---
# Construct the absolute path to the .env file, assuming it's in the parent directory
# (e.g., if this file is in BittyNews/utils/, .env is in BittyNews/)
# This makes the script more robust to where it's called from.
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
# verbose=True provides output from python-dotenv about its actions if needed for debugging .env loading.
# override=True can be useful if you want .env to take precedence over existing OS environment variables.
loaded_env = load_dotenv(dotenv_path=dotenv_path, verbose=False, override=False)

if not loaded_env:
    print(f"DEBUG llm_utils: WARNING - .env file not found or not loaded from {dotenv_path}")
else:
    print(f"DEBUG llm_utils: Successfully loaded .env from {dotenv_path}")


# --- LLM Call Function ---
def call_llm(prompt: str, model_name: str = None, system_prompt: str = "You are a helpful assistant."):
    """
    Sends a prompt to the configured LLM endpoint (OpenRouter) and returns the response.

    Args:
        prompt (str): The input prompt to send to the LLM.
        model_name (str, optional): Overrides the default model if provided.
                                    Defaults to None, which then uses MODEL_NAME from .env.
        system_prompt (str, optional): The system message for the LLM.
                                       Defaults to "You are a helpful assistant.".

    Returns:
        str: The content returned by the LLM, or an error message string if an issue occurs.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    # Default model from .env, with a fallback if MODEL_NAME is also not in .env
    default_model_from_env = os.getenv("MODEL_NAME", "openai/gpt-3.5-turbo") 

    # Determine which model to use
    model_to_use = model_name if model_name is not None else default_model_from_env

    # --- Sanity Checks and Debugging ---
    print(f"DEBUG llm_utils: Attempting LLM call with model: '{model_to_use}'")
    if not api_key:
        print("DEBUG llm_utils: ERROR - OPENROUTER_API_KEY is not set in environment variables!")
        return "Error: API Key not configured. Please check your .env file and ensure OPENROUTER_API_KEY is set."
    
    # --- Prepare Request ---
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("HTTP_REFERER", "https://your-app-domain.com"), # Replace with your actual site or app name
        "X-Title": os.getenv("X_TITLE", "BittyNews")  # Replace with your actual app name
    }

    payload = {
        "model": model_to_use,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": float(os.getenv("LLM_TEMPERATURE", 0.7)) # Allow temperature to be configured via .env
    }
    
    # For debugging the exact payload:
    # print(f"DEBUG llm_utils: Payload: {json.dumps(payload, indent=2)}")

    # --- Make API Call ---
    try:
        target_url = f"{base_url.rstrip('/')}/chat/completions"
        response = requests.post(target_url, headers=headers, json=payload, timeout=30) # Added timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        data = response.json()
        
        if data.get("choices") and len(data["choices"]) > 0 and data["choices"][0].get("message") and data["choices"][0]["message"].get("content"):
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"DEBUG llm_utils: ERROR - LLM response structure was unexpected.")
            print(f"DEBUG llm_utils: Full Response JSON: {data}")
            return "Error: LLM response format was invalid."

    except requests.exceptions.HTTPError as http_err:
        error_content = "No response body"
        try:
            error_content = response.text
        except Exception:
            pass # response might not have .text if connection failed earlier
        print(f"DEBUG llm_utils: HTTP error occurred: {http_err} - Status: {response.status_code} - Response: {error_content}")
        return f"Error: LLM call failed with HTTP error {response.status_code}."
    except requests.exceptions.Timeout:
        print(f"DEBUG llm_utils: Request timed out.")
        return "Error: LLM call timed out."
    except requests.exceptions.RequestException as req_err: # Catches other requests-related errors (e.g., connection error)
        print(f"DEBUG llm_utils: Request exception occurred: {req_err}")
        return f"Error: LLM call failed due to a request issue ({req_err})."
    except Exception as e:
        # Catch any other unexpected errors
        print(f"DEBUG llm_utils: An unexpected error occurred during LLM call: {e} (Type: {type(e).__name__})")
        # It's good to see the traceback for truly unexpected errors
        import traceback
        traceback.print_exc()
        return "Error: LLM call failed due to an unexpected error."

# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    print("\n--- Testing llm_utils.py directly ---")
    
    # Ensure your .env file has OPENROUTER_API_KEY and optionally MODEL_NAME
    # If OPENROUTER_API_KEY is not set, this will print the error message from call_llm
    
    test_prompt = "What is the capital of France?"
    print(f"\nSending test prompt: '{test_prompt}' using default model...")
    response_default = call_llm(test_prompt)
    print(f"Response (default model): {response_default}")

    # Test with a specific model override (replace with a valid model you have access to)
    # test_model_override = "mistralai/mistral-7b-instruct" 
    test_model_override = os.getenv("MODEL_NAME") # Use the same default for testing override path
    if test_model_override: # Only test if MODEL_NAME is set, to avoid forcing a specific one here
        print(f"\nSending test prompt using specific model: '{test_model_override}'...")
        response_override = call_llm(test_prompt, model_name=test_model_override)
        print(f"Response (override model '{test_model_override}'): {response_override}")
    else:
        print("\nSkipping model override test as MODEL_NAME is not set in .env for this example.")

    print("\n--- Test complete ---")
