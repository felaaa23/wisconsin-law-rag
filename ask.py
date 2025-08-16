# ask.py
import os
from config import TOP_K_VECTOR, TOP_K_BM25, FINAL_CONTEXT_TOKENS, EMBED_MODEL
from retriever import hybrid_search
from chunker import estimate_tokens
from context import expand_crossrefs, pack_context
from db import get_collection

def fetch_by_section(sec_str: str):
    # Pull by metadata exact section match
    col = get_collection()
    res = col.get(where={"section": {"$eq": sec_str}})
    items = []
    for i in range(len(res.get("ids", []))):
        items.append({
            "id": res["ids"][i],
            "text": res["documents"][i],
            "meta": res["metadatas"][i],
        })
    return items[:3]

def format_answer(ans: str):
    print("\n" + ans + "\n")

def main():
    from generator import answer
    print("Wisconsin Law RAG (terminal). Ctrl+C to exit.")
    while True:
        try:
            q = input("\nEnter your question: ").strip()
            if not q:
                continue
            # Hybrid search with sensible filters: prefer WI
            where = {"jurisdiction": {"$eq": "WI"}}
            ranked = hybrid_search(q, where=where, vector_k=TOP_K_VECTOR, bm25_k=TOP_K_BM25)
            # Expand cross-refs
            ranked = expand_crossrefs(ranked, fetch_by_section, limit=2)
            # Pack into context window
            ctx = pack_context(ranked, lambda s: estimate_tokens(s, EMBED_MODEL), FINAL_CONTEXT_TOKENS)
            # Generate final
            out = answer(q, ctx)
            format_answer(out)
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break

if __name__ == "__main__":
    main()
