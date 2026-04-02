from citation_verifier import verify_citation
import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append("/content/drive/MyDrive/veritasAI")

# Import fast hybrid check
from final_hybrid_system import verify_hybrid

SERPAPI_KEY = "YOUR-SERPAPI KEY"

def search_google_scholar(paper_title, limit=5):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_scholar",
        "q": paper_title,
        "api_key": SERPAPI_KEY,
        "num": limit
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        results = []
        for r in data.get("organic_results", []):
            results.append({
                "title": r.get("title", ""),
                "link": r.get("link", "")
            })
        return results
    except:
        return []

def verify_title_only(title):
    """Fast check: does the title exist in local or external sources?"""
    hybrid_result = verify_hybrid(title, local_threshold=6.0, external_threshold=7.0)
    return hybrid_result["decision"] == "REAL"

def recover_and_verify_references(original_title, limit=3):
    print(f"\n🔎 Searching related references for: {original_title}\n")

    candidates = search_google_scholar(original_title, limit)
    if not candidates:
        return {"status": "NO_RESULTS", "message": "No related papers found"}

    verified = []
    with ThreadPoolExecutor(max_workers=limit) as executor:
        future_to_paper = {
            executor.submit(verify_title_only, paper["title"]): paper
            for paper in candidates
        }
        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                if future.result():   # title exists
                    verified.append({
                        "title": paper["title"],
                        "url": paper["link"],
                        "verification_method": "HYBRID_TITLE_VERIFICATION"
                    })
            except Exception as e:
                print(f"Error verifying {paper['title']}: {e}")

    if verified:
        return {"status": "VERIFIED_REFERENCES_FOUND", "verified_references": verified}
    else:
        return {"status": "NO_VERIFIED_REFERENCES"}
