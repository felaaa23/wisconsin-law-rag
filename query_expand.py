from typing import List
#lowk abbreviations are cooked unless if i had to manually search everything up and add it here
ALIASES = {
    "owi": ["dui", "operating while intoxicated"],
    "terry stop": ["stop and frisk", "investigatory stop"],
    "miranda": ["miranda warnings"],
    "probable cause": ["pc"],
    "reasonable suspicion": ["rs"],
}

def expand(query: str) -> List[str]:
    q = query.lower()
    adds = []
    for k, vs in ALIASES.items():
        if k in q:
            adds.extend(vs)
    return [query] + list(dict.fromkeys(adds))
