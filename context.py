from typing import List, Dict, Callable
import re

REF_RX = re.compile(r"§\s*\d+(?:\.\d+)*")

def expand_crossrefs(top_chunks: List[Dict], fetch_by_section: Callable[[str], List[Dict]], limit: int = 2) -> List[Dict]:
    refs = []
    for c in top_chunks:
        refs.extend(list(set(REF_RX.findall(c["text"]))))
    refs = list(dict.fromkeys(refs))[:limit]
    extra = []
    for r in refs:
        extra.extend(fetch_by_section(r))
    #by id
    seen = set()
    out = []
    for c in top_chunks + extra:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        out.append(c)
    return out

def pack_context(chunks: List[Dict], token_fn, max_tokens: int) -> List[Dict]:
    out, total = [], 0
    for c in chunks:
        t = token_fn(c["text"])
        if total + t > max_tokens:
            break
        out.append(c)
        total += t
    return out
