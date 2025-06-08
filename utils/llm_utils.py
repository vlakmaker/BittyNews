# BittyNews/utils/llm_utils.py
import os
import requests
import json
import time # For sleep/backoff
from dotenv import load_dotenv

# --- Environment Variable Loading ---
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
loaded_env = load_dotenv(dotenv_path=dotenv_path, verbose=False, override=False) # Set verbose=True for .env loading debug

if not loaded_env:
    print(f"DEBUG llm_utils: WARNING - .env file not found or not loaded from {dotenv_path}")
else:
    print(f"DEBUG llm_utils: Successfully loaded .env from {dotenv_path}")

# --- API Configurations ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_API_BASE_URL", "https://api.groq.com/openai/v1") # Groq uses an OpenAI-compatible endpoint

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# --- Helper to make the actual HTTP POST request ---
def _execute_llm_call(
    provider_name: str,
    api_url: str,
    headers: dict,
    payload: dict,
    timeout: int
) -> dict:
    """ Executes the HTTP POST request and returns JSON response or raises error. """
    # print(f"DEBUG llm_utils: [{provider_name}] Sending payload to {api_url}: {json.dumps(payload, indent=2)}")
    response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status() # Will raise HTTPError for 4xx/5xx responses
    return response.json()

# --- Main LLM Call Function ---
def call_llm(
    prompt: str,
    primary_groq_model_override: str = None,
    fallback_openrouter_model_override: str = None,
    system_prompt: str = "You are a helpful assistant."
) -> str:
    """
    Sends a prompt to Groq API first. If it fails after retries, 
    falls back to OpenRouter API.

    Args:
        prompt (str): The input prompt to send to the LLM.
        primary_groq_model_override (str, optional): Specific Groq model ID to use.
        fallback_openrouter_model_override (str, optional): Specific OpenRouter model ID for fallback.
        system_prompt (str, optional): The system message for the LLM.

    Returns:
        str: The content returned by the LLM, or an error message string if issues occur.
    """
    default_groq_model = os.getenv("PRIMARY_GROQ_MODEL", "llama3-8b-8192")
    default_openrouter_fallback_model = os.getenv("FALLBACK_OPENROUTER_MODEL", "mistralai/mistral-7b-instruct") # A valid OpenRouter model
    
    groq_model_to_use = primary_groq_model_override or default_groq_model
    openrouter_model_to_use = fallback_openrouter_model_override or default_openrouter_fallback_model
    
    temperature = float(os.getenv("LLM_TEMPERATURE", 0.7))
    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    max_retries = int(os.getenv("LLM_MAX_RETRIES", 3))
    base_backoff_time = float(os.getenv("LLM_BASE_BACKOFF_SECONDS", 1.0))

    # --- Attempt 1: Groq Direct ---
    if GROQ_API_KEY and groq_model_to_use:
        print(f"DEBUG llm_utils: Attempting Groq Direct call with model: '{groq_model_to_use}'")
        groq_headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        groq_payload = {
            "model": groq_model_to_use,
            "messages": messages_payload,
            "temperature": temperature
        }
        groq_api_url = f"{GROQ_BASE_URL.rstrip('/')}/chat/completions"
        groq_timeout = int(os.getenv("GROQ_TIMEOUT_SECONDS", 15))

        for attempt in range(max_retries):
            try:
                data = _execute_llm_call("Groq", groq_api_url, groq_headers, groq_payload, groq_timeout)
                if data.get("choices") and len(data["choices"]) > 0 and \
                   data["choices"][0].get("message") and \
                   data["choices"][0]["message"].get("content") is not None:
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    print(f"DEBUG llm_utils: [Groq] LLM response structure unexpected: {data}")
                    break # Don't retry on structural issues, proceed to fallback
            except requests.exceptions.HTTPError as http_err:
                error_status = http_err.response.status_code
                error_content = "No response body"
                try: error_content = http_err.response.text
                except: pass
                print(f"DEBUG llm_utils: [Groq] HTTP error {error_status} (Attempt {attempt+1}/{max_retries}): {error_content}")
                
                if error_status == 429: # Rate limit
                    wait_time_from_header = 0
                    try: # Groq specific "retry-after" or similar in message (less standard than header)
                        error_json_ = json.loads(error_content)
                        if "message" in error_json_.get("error", {}) and "try again in" in error_json_["error"]["message"].lower():
                            parts = error_json_["error"]["message"].lower().split("try again in ")
                            if len(parts) > 1:
                                time_str = parts[1].split("s")[0].strip()
                                wait_time_from_header = float(time_str) + 0.5 # Add buffer
                    except: pass

                    if attempt < max_retries - 1:
                        wait_time = wait_time_from_header if wait_time_from_header > 0 else base_backoff_time * (2 ** attempt)
                        print(f"DEBUG llm_utils: [Groq] Rate limit. Waiting {wait_time:.2f}s before retry {attempt+2}...")
                        time.sleep(wait_time)
                        continue 
                    else: break # Max retries for rate limit
                elif error_status in [500, 502, 503, 504]: # Server errors
                    if attempt < max_retries - 1:
                        wait_time = base_backoff_time * (2 ** attempt)
                        print(f"DEBUG llm_utils: [Groq] Server error {error_status}. Waiting {wait_time}s before retry {attempt+2}...")
                        time.sleep(wait_time)
                        continue
                    else: break # Max retries for server error
                else: # Other HTTP errors (400, 401, 403, 404, 413) - likely persistent for this request/config
                    break # Proceed to fallback
            except requests.exceptions.Timeout:
                print(f"DEBUG llm_utils: [Groq] Request timed out (Attempt {attempt+1}/{max_retries}).")
                if attempt < max_retries - 1: continue
                else: break
            except Exception as e: # Includes requests.exceptions.RequestException
                print(f"DEBUG llm_utils: [Groq] Unexpected error (Attempt {attempt+1}/{max_retries}): {e} (Type: {type(e).__name__})")
                import traceback; traceback.print_exc()
                if attempt < max_retries - 1:
                    time.sleep(base_backoff_time * (2 ** attempt))
                    continue
                else: break
        # If Groq attempt loop finished without returning, it means it failed all retries or had a non-retryable error
        print(f"DEBUG llm_utils: Groq direct call failed for model '{groq_model_to_use}'. Proceeding to OpenRouter fallback.")
    else:
        if not GROQ_API_KEY: print("DEBUG llm_utils: GROQ_API_KEY not set. Skipping Groq attempt.")
        if not groq_model_to_use: print("DEBUG llm_utils: No Groq model specified. Skipping Groq attempt.")


    # --- Attempt 2: OpenRouter Fallback ---
    if OPENROUTER_API_KEY and openrouter_model_to_use:
        print(f"DEBUG llm_utils: Attempting OpenRouter fallback call with model: '{openrouter_model_to_use}'")
        openrouter_headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("HTTP_REFERER", "http://localhost:3000"),
            "X-Title": os.getenv("X_TITLE", "BittyNews")
        }
        openrouter_payload = {
            "model": openrouter_model_to_use,
            "messages": messages_payload,
            "temperature": temperature
        }
        openrouter_api_url = f"{OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
        openrouter_timeout = int(os.getenv("OPENROUTER_TIMEOUT_SECONDS", 30))

        # Note: Retries for OpenRouter could also be implemented here if desired, similar to Groq.
        # For simplicity in this example, OpenRouter fallback is a single attempt.
        try:
            data = _execute_llm_call("OpenRouter", openrouter_api_url, openrouter_headers, openrouter_payload, openrouter_timeout)
            if data.get("choices") and len(data["choices"]) > 0 and \
               data["choices"][0].get("message") and \
               data["choices"][0]["message"].get("content") is not None:
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"DEBUG llm_utils: [OpenRouter] LLM response structure unexpected: {data}")
                return f"Error: OpenRouter fallback response format invalid for model {openrouter_model_to_use}."
        except requests.exceptions.HTTPError as http_err:
            error_content = "No response body"
            try: error_content = http_err.response.text
            except: pass
            print(f"DEBUG llm_utils: [OpenRouter] HTTP error {http_err.response.status_code}: {error_content}")
            return f"Error: OpenRouter fallback failed for model {openrouter_model_to_use} with HTTP error {http_err.response.status_code}."
        except Exception as e: # Includes requests.exceptions.Timeout, requests.exceptions.RequestException
            print(f"DEBUG llm_utils: [OpenRouter] Error: {e} (Type: {type(e).__name__})")
            import traceback; traceback.print_exc()
            return f"Error: OpenRouter fallback failed for model {openrouter_model_to_use} with error: {e}"
    else:
        if not OPENROUTER_API_KEY: print("DEBUG llm_utils: OPENROUTER_API_KEY not set. Skipping OpenRouter fallback.")
        if not openrouter_model_to_use: print("DEBUG llm_utils: No OpenRouter fallback model specified. Skipping OpenRouter fallback.")

    return "Error: All LLM attempts failed (Groq and OpenRouter)."


# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    print("\n--- Testing llm_utils.py with Groq Direct + OpenRouter Fallback ---")
    
    if not os.getenv("GROQ_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
        print("\nERROR: Neither GROQ_API_KEY nor OPENROUTER_API_KEY found in .env. Please set at least one for testing.")
        print("--- Test complete ---")
        exit()

    test_prompt = "What is the concept of 'zero-shot learning' in machine learning?"
    
    print(f"\nTest 1: Sending prompt: '{test_prompt}' (Groq primary, OpenRouter fallback from .env)")
    response1 = call_llm(test_prompt, system_prompt="Explain this concept to a beginner.")
    print(f"\nResponse 1:\n{response1}")

    print(f"\nTest 2: Testing Groq failure by overriding with a bad Groq model name...")
    # This expects Groq to fail and then try the OpenRouter fallback.
    # Ensure FALLBACK_OPENROUTER_MODEL in .env is valid.
    response2 = call_llm(test_prompt, primary_groq_model_override="this-groq-model-does-not-exist")
    print(f"\nResponse 2 (should be from OpenRouter or error if OR also fails):\n{response2}")
    
    print(f"\nTest 3: Testing OpenRouter failure by overriding fallback with a bad OR model name (assuming Groq might also fail or be skipped)...")
    # To really test this, you'd also want Groq to fail, e.g. by using a bad Groq key or model.
    # For this example, let's assume Groq will fail (e.g. rate limit hit in real scenario)
    # and then OpenRouter fallback will also fail.
    # To simulate Groq failing you could temporarily comment out GROQ_API_KEY in .env for this test
    # or ensure PRIMARY_GROQ_MODEL points to something that will error out after retries.
    print("      (To fully test OpenRouter failure, ensure Groq call also fails or is skipped, e.g., by temporarily commenting GROQ_API_KEY in .env)")
    response3 = call_llm(test_prompt, 
                         primary_groq_model_override="llama3-8b-8192", # A valid Groq model that might hit rate limits
                         fallback_openrouter_model_override="this-openrouter-model-does-not-exist")
    print(f"\nResponse 3 (should be an error message):\n{response3}")


    print("\n--- Test complete ---")
