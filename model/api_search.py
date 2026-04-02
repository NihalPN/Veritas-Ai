# paste all your search_* functions here

import requests
import xml.etree.ElementTree as ET
from pprint import pprint
from time import sleep

# ==============================
# Helper Functions for Each API
# ==============================

def search_semantic_scholar(title):
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={title}&limit=1&fields=title,authors,year,url,venue,externalIds"
        res = requests.get(url).json()

        if not res.get("data"):
            return None

        p = res["data"][0]
        return {
            "source": "Semantic Scholar",
            "title": p.get("title"),
            "authors": [a["name"] for a in p.get("authors", [])],
            "year": p.get("year"),
            "doi": p.get("externalIds", {}).get("DOI"),
            "arxiv": p.get("externalIds", {}).get("ArXiv"),
            "link": p.get("url"),
            "pdf": f"https://arxiv.org/pdf/{p['externalIds']['ArXiv']}.pdf" if p.get("externalIds", {}).get("ArXiv") else None
        }
    except:
        return None


def search_crossref(title):
    try:
        url = f"https://api.crossref.org/works?query.title={title}&rows=1"
        res = requests.get(url).json()

        items = res.get("message", {}).get("items", [])
        if not items:
            return None

        p = items[0]
        return {
            "source": "CrossRef",
            "title": p.get("title", [None])[0],
            "authors": [a.get("family") for a in p.get("author", [])] if p.get("author") else None,
            "year": p.get("published-print", {}).get("date-parts", [[None]])[0][0],
            "doi": p.get("DOI"),
            "arxiv": None,
            "link": f"https://doi.org/{p.get('DOI')}",
            "pdf": None
        }
    except:
        return None


def search_openalex(title):
    try:
        url = f"https://api.openalex.org/works?search={title}&per-page=1"
        res = requests.get(url).json()

        if "results" not in res or len(res["results"]) == 0:
            return None

        p = res["results"][0]
        return {
            "source": "OpenAlex",
            "title": p.get("title"),
            "authors": [a["author"]["display_name"] for a in p.get("authorships", [])],
            "year": p.get("publication_year"),
            "doi": p.get("doi"),
            "arxiv": None,
            "link": p.get("id"),
            "pdf": p.get("open_access", {}).get("oa_url")
        }
    except:
        return None


def search_arxiv(title):
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{title}&start=0&max_results=1"
        res = requests.get(url).text

        if "entry" not in res:
            return None

        import xml.etree.ElementTree as ET
        root = ET.fromstring(res)
        ns = {"arxiv": "http://www.w3.org/2005/Atom"}

        entry = root.find("arxiv:entry", ns)
        if entry is None:
            return None

        paper_id = entry.find("arxiv:id", ns).text
        title_txt = entry.find("arxiv:title", ns).text.strip()

        return {
            "source": "arXiv",
            "title": title_txt,
            "authors": [a.text for a in entry.findall("arxiv:author/arxiv:name", ns)],
            "year": None,
            "doi": None,
            "arxiv": paper_id,
            "link": f"https://arxiv.org/abs/{paper_id}",
            "pdf": f"https://arxiv.org/pdf/{paper_id}.pdf"
        }
    except:
        return None


def search_core(title):
    try:
        url = f"https://core.ac.uk/api-v2/articles/search/{title}?page=1&pageSize=1&apiKey=core_api_key_here"
        # ← Replace with your free CORE API key
        res = requests.get(url).json()

        if "results" not in res or len(res["results"]) == 0:
            return None

        p = res["results"][0]

        return {
            "source": "CORE",
            "title": p.get("title"),
            "authors": None,
            "year": None,
            "doi": p.get("doi"),
            "arxiv": None,
            "link": p.get("links", [None])[0],
            "pdf": p.get("fullTextLink")
        }
    except:
        return None
def search_elsevier(title):
    try:
        API_KEY = "e8864f542c1ffb028da719f5b8d939ee"

        # -----------------------------
        # 1. Try SCOPUS Search API
        # -----------------------------
        scopus_url = (
            f"https://api.elsevier.com/content/search/scopus?"
            f"query=TITLE({title})&apiKey={API_KEY}"
        )

        scopus_res = requests.get(scopus_url).json()

        entries = scopus_res.get("search-results", {}).get("entry", [])

        if entries:
            p = entries[0]
            return {
                "source": "Elsevier Scopus",
                "title": p.get("dc:title"),
                "authors": p.get("dc:creator"),
                "year": p.get("prism:coverDate", "").split("-")[0],
                "doi": p.get("prism:doi"),
                "arxiv": None,
                "link": p.get("prism:url"),
                "pdf": None  # Scopus usually doesn't give PDF links
            }

        # -----------------------------
        # 2. Try ScienceDirect API
        # -----------------------------
        sd_url = (
            f"https://api.elsevier.com/content/search/sciencedirect?"
            f"query=title({title})&apiKey={API_KEY}"
        )

        sd_res = requests.get(sd_url).json()
        sd_entries = sd_res.get("search-results", {}).get("entry", [])

        if sd_entries:
            p = sd_entries[0]
            return {
                "source": "Elsevier ScienceDirect",
                "title": p.get("dc:title"),
                "authors": p.get("dc:creator"),
                "year": p.get("prism:coverDate", "").split("-")[0],
                "doi": p.get("prism:doi"),
                "arxiv": None,
                "link": p.get("prism:url"),
                "pdf": None
            }

        return None

    except Exception as e:
        print("Elsevier error:", e)
        return None


def search_ads(title):
    try:
        API_KEY = "dswFNRPdTnRV3A1O97ZKqKNpflSAB18E83TbtXdV"

        url = "https://api.adsabs.harvard.edu/v1/search/query"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        params = {
            "q": f"title:\"{title}\"",
            "fl": "title,author,year,doi,bibcode,property,identifier",
            "rows": 1
        }

        res = requests.get(url, params=params, headers=headers).json()

        docs = res.get("response", {}).get("docs", [])
        if not docs:
            return None

        p = docs[0]

        return {
            "source": "NASA ADS",
            "title": p.get("title", [""])[0],
            "authors": p.get("author", []),
            "year": p.get("year"),
            "doi": p.get("doi", [None])[0] if p.get("doi") else None,
            "arxiv": next((i for i in p.get("identifier", []) if i.startswith("arXiv")), None),
            "link": f"https://ui.adsabs.harvard.edu/abs/{p.get('bibcode')}",
            "pdf": (
                f"https://arxiv.org/pdf/{p.get('identifier')[0].replace('arXiv:', '')}.pdf"
                if p.get("identifier") and p.get("identifier")[0].startswith("arXiv:")
                else None
            )
        }

    except Exception as e:
        print("ADS error:", e)
        return None

def search_loc(title, endpoint="search"):
    """
    Search the Library of Congress for the given title.
    Uses loc.gov/{endpoint}/?q=title:"<title>"&fo=json
    Default endpoint 'search' covers many collections; you can also try 'photos', 'prints', 'manuscripts', etc.
    """
    try:
        base = f"https://www.loc.gov/{endpoint}/"
        params = {"q": f'title:"{title}"', "fo": "json", "page": 1}
        # polite headers
        headers = {"User-Agent": "UnifiedPaperChecker/1.0 (your-email@example.com)"}
        r = requests.get(base, params=params, headers=headers, timeout=12)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data.get("results") or data.get("items") or []
        if not items:
            return None
        # take the first good match
        it = items[0]
        return {
            "source": "Library of Congress",
            "title": it.get("title"),
            "authors": it.get("contributor") or it.get("creator") or it.get("author") or None,
            "year": it.get("date"),
            "doi": None,
            "arxiv": None,
            "link": it.get("url") or it.get("id"),
            "pdf": it.get("download") or it.get("fullText") or None
        }
    except Exception as e:
        # print("LOC error:", e)
        return None

# testing code form pmc

def search_pubmed(title):
    API_KEY = "d040971fe489eb3bfb6cba4114da29798908"
    """
    Searches PubMed by title using NCBI E-Utilities (esearch + esummary).
    Returns a dictionary of paper metadata or None if not found.
    """

    # --- STEP 1: ESearch (Title -> PMID) ---
    try:
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        esearch_params = {
            "db": "pubmed",
            "term": f"{title}[Title]", # Search by title field
            "retmax": 1,
            "retmode": "xml",         # Request XML for reliable parsing
            "api_key": API_KEY
        }

        # The 'requests' library handles URL encoding of the 'term' parameter
        r = requests.get(esearch_url, params=esearch_params, timeout=12)
        r.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Parse the XML response
        root = ET.fromstring(r.content)

        # Look for the IdList tag and get the first ID
        id_element = root.find(".//IdList/Id")
        if id_element is None:
            return None # Paper not found

        pmid = id_element.text

    except Exception:
        # Catch connection errors, XML parsing errors, etc.
        return None

    # --- STEP 2: ESummary (PMID -> Metadata) ---
    try:
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        esummary_params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "json", # Request JSON for easier metadata extraction
            "api_key": API_KEY
        }

        r = requests.get(esummary_url, params=esummary_params, timeout=12)
        r.raise_for_status()
        summary_data = r.json()

        # The metadata is nested under result[pmid]
        summary = summary_data.get("result", {}).get(pmid, {})

        # Extract authors
        authors = [a["name"] for a in summary.get("authors", [])]

        # Extract DOI
        doi = next(
            (i["value"] for i in summary.get("articleids", [])
             if i.get("idtype") == "doi"),
            None
        )

        return {
            "source": "PubMed",
            "title": summary.get("title"),
            "authors": authors,
            # pubdate is typically "YYYY Mon DD", split to get YYYY
            "year": summary.get("pubdate", "").split(" ")[0],
            "doi": doi,
            "arxiv": None, # PubMed primarily focuses on published biomedical literature
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "pdf": None
        }

    except Exception:
        return None

# ==============================
# Master Function (Combines All)
# ==============================

def check_research_paper(title):
    print("🔎 Searching for:", title)
    sources = [
        search_elsevier,
        search_semantic_scholar,
        search_crossref,
        search_openalex,
        search_arxiv,
        search_ads,
        search_loc,
        search_pubmed,

    ]

    results = []

    for fn in sources:
        try:
            r = fn(title)
            if r:
                results.append(r)
                print(f"✔ Found in {r['source']}")
        except:
            pass

    if not results:
        return {"exists": False, "message": "Paper not found in any database"}

    # Remove duplicates by title
    unique = {}
    for r in results:
        unique[r["title"]] = r
    results = list(unique.values())

    return {
        "exists": True,
        "matches": results,
        "best_match": results[0]  # top one
    }


# ==============================
# Example Test
# ==============================

# paper = "heterogeneous low band width pre training of llms"
# result = check_research_paper(paper)
# result
