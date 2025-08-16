from dataclasses import dataclass, asdict
from typing import List, Iterable, Optional
from pathlib import Path
from pypdf import PdfReader
import re

@dataclass
class Doc:
    text: str
    source: str
    doctype: str 
    chapter: Optional[str] = None
    section: Optional[str] = None
    citation: Optional[str] = None
    date: Optional[str] = None
    jurisdiction: str = "WI"
    superseded: Optional[bool] = None

STATUTE_RX = re.compile(r"§\s*([0-9][0-9\.\(\)a-zA-Z-]*)")

def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages)

def guess_statute_meta(text: str):
    m = STATUTE_RX.search(text or "")
    return m.group(1) if m else None

def load_pdf(path: Path, doctype: str) -> Doc:
    txt = extract_pdf_text(path)
    statute = guess_statute_meta(txt) if doctype == "statute" else None
    return Doc(
        text=txt,
        source=str(path),
        doctype=doctype,
        section=statute,
        jurisdiction="WI",
    )

def walk_pdfs(folder: Path, doctype: str) -> Iterable[Doc]:
    for p in folder.rglob("*.pdf"):
        yield load_pdf(p, doctype)
