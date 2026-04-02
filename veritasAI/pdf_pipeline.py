# pdf_pipeline.py

import sys
import fitz
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import logging

sys.path.append("/content/drive/MyDrive/veritasAI")
from citation_service import process_citation_form

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Enhanced Reference Extraction with regex‑based splitting
# ----------------------------------------------------------------------

class ReferenceExtractor:
    """
    Extracts and parses references from academic PDFs. Uses a regex scan
    over the whole reference section to identify entries, making it robust
    to line merging and indentation.
    """

    REFERENCE_HEADERS = [
        r'^\s*references\s*$',
        r'^\s*bibliography\s*$',
        r'^\s*works?\s+cited\s*$',
        r'^\s*references\s+and\s+notes\s*$',
        r'^\s*literature\s+cited\s*$',
        r'^\s*cited\s+references\s*$',
        r'^\s*reference\s+list\s*$',
    ]

    # Combined pattern for all reference start markers
    # We join them with '|' and make them match at the beginning of a line OR
    # after a newline (but since we'll scan the whole text, we rely on the regex engine)
    START_PATTERNS = [
        r'\[\d+\]\s+',                 # [10]
        r'\(\d+\)\s+',                  # (10)
        r'\d+\.\s+',                     # 10.
        r'\d+\)\s+',                      # 10)
        # Author‑year styles (simplified for the scanner)
        r'[A-Z][a-z]+(?:,\s+[A-Z]\.?)?(?:,\s+[A-Z][a-z]+)?,\s+\d{4}\b',
        r'[A-Z][a-z]+\s+[A-Z]\.?,\s+\d{4}\b',
        r'[A-Z]{2,}(?:,\s+[A-Z]\.?)?,\s+\d{4}\b',
    ]
    # We'll compile these into one big regex with re.MULTILINE so '^' matches line starts
    START_REGEX = re.compile('|'.join(f'^(?:{p})' for p in START_PATTERNS), re.MULTILINE)

    DOI_PATTERN = r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+'
    ARXIV_PATTERN = r'(?:arXiv|arXiv preprint|arXiv:)\s*(\d{4}\.\d{4,5}(?:v\d+)?)'
    URL_PATTERN = r'https?://[^\s\)\]\}]+'

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.reference_text = ""

    def locate_reference_section(self) -> str:
        """Find the reference section by scanning headers; return concatenated text."""
        full_text = ""
        in_ref = False
        for page in self.doc:
            text = page.get_text()
            lower = text.lower()
            if not in_ref:
                if any(re.search(h, lower, re.MULTILINE) for h in self.REFERENCE_HEADERS):
                    in_ref = True
                    full_text += text
            else:
                # Stop if we hit another section header that likely ends references
                if re.search(r'^\s*(appendix|acknowledgements?|supplementary|supporting information)\s*$', lower, re.MULTILINE):
                    break
                full_text += text
        self.reference_text = full_text
        if not full_text:
            logger.warning("No reference section found.")
        return full_text

    def split_references(self, text: str) -> List[str]:
        """
        Use the combined START_REGEX to find all reference start positions,
        then extract the text between them.
        """
        if not text:
            return []
        # Find all matches of the start pattern
        matches = list(self.START_REGEX.finditer(text))
        if not matches:
            # Fallback: try a simpler heuristic – split by lines that start with a number or bracket
            logger.debug("No reference starts found with pattern; falling back to line‑based split.")
            lines = text.split('\n')
            refs = []
            current = []
            for line in lines:
                if re.match(r'^\s*(?:\[\d+\]|\(\d+\)|\d+[\.\)])\s', line):
                    if current:
                        refs.append('\n'.join(current))
                        current = [line.strip()]
                    else:
                        current = [line.strip()]
                else:
                    if current:
                        current.append(line.strip())
            if current:
                refs.append('\n'.join(current))
            return [r for r in refs if len(r) > 30]

        references = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            ref_text = text[start:end].strip()
            if len(ref_text) > 30:   # ignore very short fragments
                references.append(ref_text)
        logger.info(f"Split into {len(references)} references")
        return references

    def extract_doi_url(self, text: str) -> Optional[str]:
        """Extract DOI, arXiv ID, or URL from reference text."""
        # DOI
        doi_match = re.search(self.DOI_PATTERN, text)
        if doi_match:
            doi = doi_match.group(0)
            return f"https://doi.org/{doi}"
        # arXiv
        arxiv_match = re.search(self.ARXIV_PATTERN, text, re.IGNORECASE)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            return f"https://arxiv.org/abs/{arxiv_id}"
        # Plain URL
        url_match = re.search(self.URL_PATTERN, text)
        if url_match:
            return url_match.group(0).rstrip(').,;]')
        return None

    def extract_title(self, text: str) -> Optional[str]:
        """
        Attempt to extract the title, with special handling for numbered entries.
        """
        # Remove the leading reference marker (e.g., "[10] ") to simplify
        text_clean = re.sub(r'^\s*(?:\[\d+\]|\(\d+\)|\d+[\.\)])\s*', '', text)

        # Strategy 1: Look for the pattern: Authors. Title. Venue/Year.
        # Often the title ends with a period that is followed by "In", "Proceedings", etc.
        # We'll try to capture everything up to the first occurrence of a journal-like keyword
        # or the year (which often appears near the end).
        # This is heuristic but works for many entries.

        # First, try to find a period that is followed by a typical venue word
        venue_pattern = r'\.\s+(?:(?:In|Proceedings|Journal|Conference|Workshop|Advances|Neural|International|arXiv|preprint))'
        match = re.search(venue_pattern, text_clean, re.IGNORECASE)
        if match:
            # Title is the part before that period
            title_candidate = text_clean[:match.start()+1].strip()
            # Remove trailing period if present
            title_candidate = re.sub(r'\.$', '', title_candidate)
            # Also remove any trailing " et al." that might have been captured
            title_candidate = re.sub(r'\s+et\s+al\.?$', '', title_candidate)
            if title_candidate and len(title_candidate) > 10:
                return title_candidate

        # Strategy 2: If no venue keyword, try to capture the first sentence after authors
        # Assume authors end with a period (common in many styles)
        author_end_pattern = r'[A-Z][a-z]+(?:,?\s+[A-Z]\.?)?(?:,?\s+[A-Z][a-z]+)*\.\s+'
        match = re.search(author_end_pattern, text_clean)
        if match:
            # Everything after that up to the next period might be the title
            after_authors = text_clean[match.end():]
            # Find the first period that is not part of an abbreviation
            # (simple approach: look for a period followed by space and capital letter)
            sent_match = re.search(r'([^\.]+\.)(?=\s+[A-Z]|\s*\()', after_authors)
            if sent_match:
                title_candidate = sent_match.group(1).strip()
                if len(title_candidate) > 10:
                    return title_candidate

        # Strategy 3: Fallback – take everything up to the year if present
        year_match = re.search(r'\b(?:19|20)\d{2}\b', text_clean)
        if year_match:
            before_year = text_clean[:year_match.start()].strip()
            # Find the last period before the year
            last_period = before_year.rfind('.')
            if last_period != -1:
                title_candidate = before_year[last_period+1:].strip()
                if title_candidate and len(title_candidate) > 10:
                    return title_candidate

        return None

    def process_reference(self, ref_text: str) -> Dict:
        """Process a single reference entry."""
        ref_text_norm = re.sub(r'\s+', ' ', ref_text)   # normalize whitespace
        link = self.extract_doi_url(ref_text_norm)
        title = self.extract_title(ref_text_norm)
        return {
            'raw': ref_text,
            'title': title,
            'link': link
        }

    def extract_all(self) -> List[Dict]:
        """Main extraction routine."""
        self.locate_reference_section()
        if not self.reference_text:
            return []
        entries = self.split_references(self.reference_text)
        results = []
        for ent in entries:
            proc = self.process_reference(ent)
            # Keep entries that have at least a link or a title
            if proc['link'] or proc['title']:
                results.append(proc)
        logger.info(f"Extracted {len(results)} references with metadata")
        return results


# ----------------------------------------------------------------------
# Title resolution from DOI or arXiv
# ----------------------------------------------------------------------

def resolve_title_from_doi(doi_url: str) -> Optional[str]:
    """Fetch title from CrossRef API using DOI."""
    try:
        doi = doi_url.split("doi.org/")[-1]
        api_url = f"https://api.crossref.org/works/{doi}"
        resp = requests.get(api_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            titles = data["message"].get("title", [])
            if titles:
                return titles[0]
    except Exception as e:
        logger.debug(f"CrossRef lookup failed: {e}")
    return None

def resolve_title_from_arxiv(arxiv_url: str) -> Optional[str]:
    """Fetch title from arXiv API using arXiv ID."""
    try:
        arxiv_id = arxiv_url.split("/abs/")[-1]
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        resp = requests.get(api_url, timeout=5)
        if resp.status_code == 200:
            # Very simple parsing – extract title from XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('atom:entry', ns)
            if entry is not None:
                title_elem = entry.find('atom:title', ns)
                if title_elem is not None and title_elem.text:
                    return title_elem.text.strip()
    except Exception as e:
        logger.debug(f"arXiv lookup failed: {e}")
    return None


# ----------------------------------------------------------------------
# Main verification function (backward compatible)
# ----------------------------------------------------------------------

def verify_pdf_references(pdf_path: str, process_citation_form):
    """
    Extract references, resolve missing titles via DOI/arXiv, and verify each.
    """
    extractor = ReferenceExtractor(pdf_path)
    extracted = extractor.extract_all()

    verified = []

    def worker(item):
        title = item['title']
        link = item['link']
        if not title and link:
            if "doi.org" in link:
                title = resolve_title_from_doi(link)
            elif "arxiv.org" in link:
                title = resolve_title_from_arxiv(link)
        if title and link:
            return {
                'title': title,
                'link': link,
                'verification': process_citation_form(title, link)
            }
        return None

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(worker, ref) for ref in extracted]
        for f in as_completed(futures):
            res = f.result()
            if res:
                verified.append(res)

    return verified


# ----------------------------------------------------------------------
# Legacy function (optional)
# ----------------------------------------------------------------------

def extract_references_metadata(pdf_path: str) -> List[Dict]:
    """Legacy compatibility wrapper."""
    ext = ReferenceExtractor(pdf_path)
    refs = ext.extract_all()
    return [{'title': r['title'], 'link': r['link']} for r in refs]