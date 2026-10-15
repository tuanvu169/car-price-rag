import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

EXCEL_FILE = BASE_DIR / "data_base_gia_xe.xlsx"
CHROMA_DB_DIR = BASE_DIR / "chroma_db_cars"
COLLECTION_NAME = "cars"

EMBEDDING_MODEL_NAME = ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_DEVICE = "cpu"

LLM_MODEL_NAME = "gemini-3.5-flash-lite"
TOP_K = 10
REBUILD_VECTOR_DB = False
