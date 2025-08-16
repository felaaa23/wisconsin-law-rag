import argparse
from pathlib import Path
from typing import List
from tqdm import tqdm

from loaders import walk_pdfs, Doc
from chunker import chunk_legal, attach_meta_chunks
from db import upsert
from config import DATA_DIR, MAX_CHUNK_TOKENS, CHUNK_OVERLAP, EMBED_MODEL


def doc_to_chunks(doc: Doc):
    chunks = chunk_legal(doc.text, MAX_CHUNK_TOKENS, CHUNK_OVERLAP, EMBED_MODEL)
    base = {
        "source": doc.source,
        "doctype": doc.doctype,
        "chapter": doc.chapter,
        "section": doc.section,
        "citation": doc.citation,
        "date": doc.date,
        "jurisdiction": doc.jurisdiction,
        "superseded": doc.superseded,
    }
    return attach_meta_chunks(chunks, base)


def count_pdfs(root: Path) -> int:
    # Count upfront for a proper progress bar (walk_pdfs loads PDFs, so we count paths first)
    return sum(1 for _ in root.rglob("*.pdf"))


def main(batch_size: int, limit: int | None):
    root = Path(DATA_DIR)
    assert root.exists(), f"DATA_DIR not found: {root}"

    total_pdfs = count_pdfs(root)
    if limit is not None:
        total_pdfs = min(total_pdfs, limit)

    all_chunks: List[dict] = []

    # --- Process PDFs -> chunks (progress bar) ---
    processed = 0
    pbar = tqdm(total=total_pdfs, desc="Processing PDFs", unit="pdf")
    for doc in walk_pdfs(root, doctype="statute"):
        if limit is not None and processed >= limit:
            break
        try:
            chunks = doc_to_chunks(doc)
            all_chunks.extend(chunks)
            processed += 1
            pbar.set_postfix({"last_pdf_chunks": len(chunks), "total_chunks": len(all_chunks)})
            pbar.update(1)
        except Exception as e:
            pbar.write(f"Error processing {doc.source}: {e}")
            processed += 1
            pbar.update(1)
    pbar.close()

    print(f"Prepared {len(all_chunks)} chunks from {processed} PDF(s).")

    if not all_chunks:
        print("No chunks to upsert. Exiting.")
        return

    # --- Upsert to Chroma in batches (progress bar) ---
    upbar = tqdm(total=len(all_chunks), desc="Upserting to Chroma", unit="chunk")
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        try:
            upsert(batch)
            upbar.update(len(batch))
        except Exception as e:
            upbar.write(f"Upsert failed for batch {i}-{i+len(batch)}: {e}")
    upbar.close()

    print("Upserted to ChromaDB. Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build ChromaDB from local PDFs with progress bars.")
    parser.add_argument("--batch-size", type=int, default=256, help="Number of chunks per upsert batch.")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N PDFs.")
    args = parser.parse_args()

    main(batch_size=args.batch_size, limit=args.limit)
