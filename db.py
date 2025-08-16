from typing import List, Dict
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from config import CHROMA_DIR, CHROMA_COLLECTION, EMBED_MODEL

_client = None
_embedder = OpenAI()

def get_chroma():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(allow_reset=True))
    return _client

def get_collection():
    client = get_chroma()
    try:
        return client.get_collection(CHROMA_COLLECTION)
    except Exception:
        return client.create_collection(CHROMA_COLLECTION, metadata={"hnsw:space":"cosine"})

def embed_texts(texts: List[str]) -> List[List[float]]:
    resp = _embedder.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

def upsert(chunks: List[Dict]):
    col = get_collection()
    ids = [c["meta"]["chunk_id"] for c in chunks]
    docs = [c["text"] for c in chunks]
    metas = [c["meta"] for c in chunks]
    vecs = embed_texts(docs)
    col.upsert(ids=ids, embeddings=vecs, metadatas=metas, documents=docs)

def vector_search(query: str, k: int, where: Dict = None):
    col = get_collection()
    qvec = embed_texts([query])[0]
    res = col.query(query_embeddings=[qvec], n_results=k, where=where or {})
    # flatten into items
    items = []
    for i in range(len(res["ids"][0])):
        items.append({
            "id": res["ids"][0][i],
            "text": res["documents"][0][i],
            "meta": res["metadatas"][0][i],
            "distance": res["distances"][0][i] if "distances" in res else None
        })
    return items
