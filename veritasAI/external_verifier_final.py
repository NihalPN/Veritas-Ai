import requests
import numpy as np
import concurrent.futures
from sentence_transformers import CrossEncoder

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
SEMANTIC_API_KEY = "Set semantic api"

def score_titles(query, titles):
    if not titles:
        return 0.0
    pairs = [(query, t) for t in titles]
    scores = cross_encoder.predict(pairs)
    return float(np.max(scores))

def search_semantic_scholar(title):
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": title, "limit": 10, "fields": "title"}
        headers = {"x-api-key": SEMANTIC_API_KEY}
        r = requests.get(url, params=params, headers=headers, timeout=(3, 5))
        r.raise_for_status()
        data = r.json()
        return [paper["title"] for paper in data.get("data", [])]
    except Exception:
        return []

def search_openalex(title):
    try:
        url = "https://api.openalex.org/works"
        params = {"search": title, "per-page": 10}
        r = requests.get(url, params=params, timeout=(3, 5))
        r.raise_for_status()
        data = r.json()
        return [w["display_name"] for w in data.get("results", [])]
    except Exception:
        return []

def search_crossref(title):
    try:
        url = "https://api.crossref.org/works"
        params = {"query.title": title, "rows": 10}
        r = requests.get(url, params=params, timeout=(3, 5))
        r.raise_for_status()
        data = r.json()
        results = data.get("message", {}).get("items", [])
        return [item["title"][0] for item in results if "title" in item]
    except Exception:
        return []

def verify_external(query, threshold=7.0):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(search_semantic_scholar, query): "sem",
            executor.submit(search_openalex, query): "open",
            executor.submit(search_crossref, query): "cross"
        }
        titles = {"sem": [], "open": [], "cross": []}
        for future in concurrent.futures.as_completed(futures):
            source = futures[future]
            try:
                titles[source] = future.result()
            except Exception:
                # Silently ignore API failure
                pass

    all_titles = titles["sem"] + titles["open"] + titles["cross"]
    final_score = score_titles(query, all_titles)
    decision = "REAL" if final_score > threshold else "HALLUCINATED"
    return {"decision": decision, "score": final_score}
