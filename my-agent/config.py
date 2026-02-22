import os
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).parent / ".env"


def get_api_key() -> str:
    load_dotenv(ENV_FILE)
    return os.getenv("ANTHROPIC_API_KEY", "").strip()


def save_api_key(key: str):
    with open(ENV_FILE, "w") as f:
        f.write(f"ANTHROPIC_API_KEY={key}\n")
