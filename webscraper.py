import os
import time
import re
import pathlib
import urllib.parse as urlparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

#page we are sourcing our information from
START_URL = "https://docs.legis.wisconsin.gov/statutes/prefaces/toc"  
OUTPUT_DIR = "data"
DOMAIN = "docs.legis.wisconsin.gov"

DELAY_SEC = 0.5       
TIMEOUT = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WIStatutePDFBot/1.0; +https://example.org/)"
}

# limit which non-pdf pages we follow
FOLLOW_PATH_PREFIXES = (
    "/statutes",         
    "/document/statutes",
    "/statutes/prefaces",
    "/document/constitution",
    "/code",             
)

def is_same_domain(url: str) -> bool:
    try:
        return urlparse.urlparse(url).netloc == DOMAIN
    except Exception:
        return False

def absolutize(base: str, href: str) -> str:
    if not href:
        return ""
    return urlparse.urljoin(base, href)

def is_pdf_url(u: str) -> bool:
    if not u:
        return False
    parsed = urlparse.urlparse(u)
    # obvious .pdf
    if parsed.path.lower().endswith(".pdf"):
        return True
    # finding hidden pdfs in params
    if "pdf" in parsed.path.lower() or "pdf" in (parsed.query or "").lower():
        return True
    return False

def allowed_to_follow(u: str) -> bool:
    # stay within the website
    if not is_same_domain(u):
        return False
    path = urlparse.urlparse(u).path or ""
    return path.startswith(FOLLOW_PATH_PREFIXES)

def fetch(url: str) -> requests.Response:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r

def collect_links(page_url: str) -> tuple[set[str], set[str]]:
    # fetches all the pdf links from HTML files
    pdfs, follows = set(), set()
    try:
        resp = fetch(page_url)
    except Exception as e:
        print(f"[WARN] Failed to fetch {page_url}: {e}")
        return pdfs, follows

    ct = resp.headers.get("Content-Type", "")
    if "pdf" in ct.lower():
        pdfs.add(page_url)
        return pdfs, follows

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        u = absolutize(page_url, href)
        # normalize fragment away
        u = u.split("#", 1)[0]
        if not is_same_domain(u):
            continue
        if is_pdf_url(u):
            pdfs.add(u)
        elif allowed_to_follow(u):
            follows.add(u)

    return pdfs, follows

def filename_from_url(u: str, resp: requests.Response | None = None) -> str:
    # content-disposition
    if resp is not None:
        cd = resp.headers.get("Content-Disposition", "")
        m = re.search(r'filename="?([^"]+)"?', cd, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    # last path segment
    path = urlparse.urlparse(u).path
    name = os.path.basename(path) or "document.pdf"
    if not name.lower().endswith(".pdf"):
        # e.g., /statutes/46 -> 46.pdf
        name = (name or "document") + ".pdf"
    return name

def download_pdf(u: str, out_dir: str) -> None:
    try:
        with requests.get(u, headers=HEADERS, timeout=TIMEOUT, stream=True) as r:
            r.raise_for_status()
            name = filename_from_url(u, r)
            safe_name = re.sub(r"[^A-Za-z0-9_\-\.]+", "_", name)
            path = pathlib.Path(out_dir) / safe_name

            # ignores if is already in collection
            if path.exists() and path.stat().st_size > 0:
                return

            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        print(f"[WARN] Failed to download {u}: {e}")

def main():
    pathlib.Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # grabs from website
    pdfs, follows = collect_links(START_URL)

    # collects all links
    to_visit = sorted(follows)
    seen_pages = set([START_URL])
    for page in tqdm(to_visit, desc="Scanning linked pages"):
        if page in seen_pages:
            continue
        seen_pages.add(page)
        p_pdfs, p_follows = collect_links(page)
        pdfs.update(p_pdfs)
        # so website doesnt think were botting this
        time.sleep(DELAY_SEC)

    # normalize
    pdf_list = sorted(pdfs)
    print(f"Found {len(pdf_list)} PDF links under {DOMAIN}")

    # download
    for u in tqdm(pdf_list, desc="Downloading PDFs"):
        download_pdf(u, OUTPUT_DIR)
        time.sleep(DELAY_SEC)

    print(f"Done. Files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
