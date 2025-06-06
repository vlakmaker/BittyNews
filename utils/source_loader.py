import yaml
import os

def load_sources(yaml_path="config/sources.yaml"):
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Missing source config: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        sources = yaml.safe_load(f)

    # Only return enabled sources
    return [src for src in sources if src.get("enabled", True)]
