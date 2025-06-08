# BittyNews/utils/source_loader.py
import yaml
import os

# Define the path to the YAML file relative to this script or project root
# Assuming source_loader.py is in utils/ and sources.yml is in project root BittyNews/
SOURCES_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.yaml')
)

def load_sources() -> list[dict]:
    """
    Loads RSS feed sources from the sources.yml file.
    Each source is expected to be a dictionary.
    Filters sources to include only those that are enabled (defaulting to True if 'enabled' key is missing).
    """
    if not os.path.exists(SOURCES_FILE_PATH):
        print(f"ERROR: Sources file not found at {SOURCES_FILE_PATH}")
        print("WARNING: Using hardcoded default sources as sources.yml was not found.")
        # Example hardcoded defaults if needed
        return [
            {"name": "The Verge (Default)", "url": "https://www.theverge.com/rss/index.xml", "enabled": True, "tags": ["Tech"], "weight": 1.0},
            {"name": "TechCrunch (Default)", "url": "https://techcrunch.com/feed/", "enabled": True, "tags": ["Startups"], "weight": 1.5}
        ]

    raw_sources_list = []
    try:
        with open(SOURCES_FILE_PATH, 'r') as f:
            data = yaml.safe_load(f)
        
        # Ensure data is a dictionary and has the 'sources' key which is a list
        if isinstance(data, dict) and "sources" in data and isinstance(data["sources"], list):
            raw_sources_list = data["sources"] # This is your list of source dictionaries
            print(f"DEBUG source_loader: Successfully parsed {len(raw_sources_list)} raw source entries from {SOURCES_FILE_PATH}")
        else:
            print(f"ERROR: Sources file ({SOURCES_FILE_PATH}) is not in the expected format. Expecting a top-level 'sources' key with a list of source objects.")
            return [] # Return empty list on format error
            
    except yaml.YAMLError as e:
        print(f"ERROR: Could not parse {SOURCES_FILE_PATH}. YAML Error: {e}")
        return [] 
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading sources from {SOURCES_FILE_PATH}: {e}")
        import traceback
        traceback.print_exc()
        return []

    if not raw_sources_list:
        print("WARNING source_loader: No sources found in the YAML data. Scraper will have nothing to fetch.")
        return []

    # Filter for enabled sources and validate structure before returning
    # Each 'src' in 'raw_sources_list' SHOULD be a dictionary here.
    valid_and_enabled_sources = []
    for i, src_dict in enumerate(raw_sources_list):
        if not isinstance(src_dict, dict):
            print(f"WARNING source_loader: Item {i} in sources list is not a dictionary: {src_dict}. Skipping.")
            continue
        
        # Check for essential keys 'name' and 'url'
        if "name" not in src_dict or "url" not in src_dict:
            print(f"WARNING source_loader: Source item {i} is missing 'name' or 'url': {src_dict}. Skipping.")
            continue

        # Check the 'enabled' flag, defaulting to True if missing
        if src_dict.get("enabled", True): # This is where the .get() is safe because src_dict IS a dictionary
            valid_and_enabled_sources.append(src_dict)
        else:
            print(f"DEBUG source_loader: Source '{src_dict.get('name')}' is disabled. Skipping.")
            
    if not valid_and_enabled_sources:
        print("WARNING source_loader: No valid and enabled sources to return after processing.")

    return valid_and_enabled_sources


if __name__ == "__main__":
    # Test the loader
    print("--- Testing source_loader.py ---")
    loaded_sources = load_sources()
    if loaded_sources:
        print(f"\nSuccessfully loaded and filtered {len(loaded_sources)} sources:")
        for i, src in enumerate(loaded_sources):
            print(f"  {i+1}. Name: {src.get('name')}, URL: {src.get('url')}, Enabled: {src.get('enabled', True)}, Tags: {src.get('tags')}, Weight: {src.get('weight')}")
    else:
        print("\nNo sources were loaded by the test, or all were invalid/disabled. Check for errors above or if 'sources.yml' is empty/malformed.")
    print("--- Test complete ---")
