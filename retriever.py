from typing import List, Dict
from rank_bm25 import BM25Okapi
import re
from db import vector_search
from query_expand import expand

def tokenize(s: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9§\.\-]+", s.lower())

def bm25_rank(query: str, corpus_items: List[Dict], top_k: int) -> List[Dict]:
    corpus = [it["text"] for it in corpus_items]
    tokenized = [tokenize(c) for c in corpus]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(tokenize(query))
    ranked = []
    for it, sc in zip(corpus_items, scores):
        it2 = dict(it)
        it2["bm25"] = float(sc)
        ranked.append(it2)
    ranked.sort(key=lambda x: x["bm25"], reverse=True)
    return ranked[:top_k]

def score_blend(item):
    v = item.get("vector", 0.0)
    b = item.get("bm25", 0.0)
    s = 0.5*b + 0.5*v
    if item["meta"].get("jurisdiction") == "WI":
        s += 0.1
    if item["meta"].get("superseded"):
        s -= 0.3
    if item["meta"].get("doctype") == "policy":
        s += 0.05
    return s

def hybrid_search(query: str, where: Dict, vector_k=12, bm25_k=20) -> List[Dict]:
    #vector
    vec_items_all = []
    for q in expand(query):
        items = vector_search(q, k=vector_k, where=where)
        for idx, it in enumerate(items):
            it = dict(it)
            it["vector"] = 1.0 - float(it.get("distance") or 0.0)  # higher is better
            vec_items_all.append(it)
    # dedupe by id
    byid = {}
    for it in vec_items_all:
        byid[it["id"]] = max(byid.get(it["id"], it), it, key=lambda x: x["vector"])
    vec_items = list(byid.values())

    #bm25 over the vector candidates
    bm = bm25_rank(query, vec_items, top_k=bm25_k)

    #blend
    blended = []
    for it in bm:
        blended.append(it)
    blended.sort(key=score_blend, reverse=True)
    return blended
