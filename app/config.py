import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_KEY = os.getenv("API_KEY")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "menu_cache.db")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing in .env file")

if not API_KEY:
    raise RuntimeError("API_KEY is missing in .env file")
