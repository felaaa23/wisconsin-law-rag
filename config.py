# config.py
import os
from dotenv import load_dotenv

load_dotenv()


DATA_DIR = os.path.abspath(os.getenv("DATA_DIR", "./pdfs"))
CHROMA_DIR = os.path.abspath(os.getenv("CHROMA_DIR", "./chroma"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "wi_law")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
JURISDICTION = "WI"
MAX_CHUNK_TOKENS = int(os.getenv("MAX_CHUNK_TOKENS", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K_VECTOR = int(os.getenv("TOP_K_VECTOR", "12"))
TOP_K_BM25 = int(os.getenv("TOP_K_BM25", "20"))
FINAL_CONTEXT_TOKENS = int(os.getenv("FINAL_CONTEXT_TOKENS", "6000"))
