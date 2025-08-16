from typing import List, Dict
from openai import OpenAI
from config import CHAT_MODEL
from chunker import estimate_tokens

_client = OpenAI()
# all helper functions in generating an answer
SYSTEM_PROMPT = (
    "You are a legal information assistant for Wisconsin law enforcement. "
    "Answer concisely and include a Sources list with statute numbers/case names. "
    "If uncertain or out-of-scope, say so. This is information, not legal advice."
)

def format_context(chunks: List[Dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        meta = c.get("meta", {})
        tag = meta.get("section") or meta.get("citation") or meta.get("doctype", "")
        src = meta.get("source", "")
        lines.append(f"[{i}] ({tag}) {src}\n{c['text'][:1200]}")
    return "\n\n".join(lines)

def disclaimer(chunks: List[Dict]) -> str:
    flags = []
    if any(c["meta"].get("superseded") for c in chunks):
        flags.append("Some sources may be superseded or amended.")
    return "Information only, not legal advice." + (" " + " ".join(flags) if flags else "")
# provides section, page, and the src
def cite_list(chunks: List[Dict]) -> str:
    cites = []
    for c in chunks[:6]:
        m = c.get("meta", {})
        sec = m.get("section")
        cit = m.get("citation")
        label = sec or cit or m.get("doctype", "doc")
        src = m.get("source", "")
        cites.append(f"- {label} — {src}")
    return "\n".join(cites)
#self explanatory
def answer(query: str, context_chunks: List[Dict]) -> str:
    ctx = format_context(context_chunks)
    prompt = (
        f"{disclaimer(context_chunks)}\n\n"
        f"Question: {query}\n\n"
        f"Context (ranked):\n{ctx}\n\n"
        "Return a short answer, then a list titled 'Sources' with statute numbers/case names.\n"
    )
    resp = _client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":prompt},
        ],
        temperature=0.2,
    )
    text = resp.choices[0].message.content.strip()
    #makes sure there are sources
    if "Sources" not in text:
        text += "\n\nSources\n" + cite_list(context_chunks)
    return text
