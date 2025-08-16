from typing import List, Dict, Any
import re
import tiktoken

SECTION_SPLIT = re.compile(r"(?:^|\n)(Chapter\s+\d+|Subchapter\s+[A-Z]+|§\s*\d+(?:\.\d+)*[^\n]*)", re.IGNORECASE)

def estimate_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text or ""))

def chunk_legal(text: str, max_tokens: int, overlap: int, model: str) -> List[str]:
    # split by section
    parts = []
    tokens_so_far = 0
    for piece in re.split(SECTION_SPLIT, text):
        if not piece or piece.isspace():
            continue
        parts.append(piece.strip())

    # window by token budget (broke lol)
    chunks: List[str] = []
    for part in parts:
        if not part:
            continue
        if estimate_tokens(part, model) <= max_tokens:
            chunks.append(part)
            continue
        words = part.split()
        start = 0
        while start < len(words):
            lo = start
            hi = min(len(words), start + 400) 
            # while loop runs until token limit
            while hi <= len(words):
                candidate = " ".join(words[lo:hi])
                if estimate_tokens(candidate, model) > max_tokens:
                    hi -= 1
                    break
                hi += 50
            chunks.append(" ".join(words[lo:hi]))
            # step with overlap
            start = max(hi - max(1, overlap // 3), hi)
    return chunks

def attach_meta_chunks(chunks: List[str], base_meta: Dict[str, Any]):
    out = []
    for i, c in enumerate(chunks):
        meta = dict(base_meta)
        meta["chunk_id"] = f'{base_meta.get("source","")}|{i}'
        out.append({"text": c, "meta": meta})
    return out
