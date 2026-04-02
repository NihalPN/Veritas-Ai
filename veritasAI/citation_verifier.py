import sys
import requests
import io
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from sentence_transformers import CrossEncoder

# -----------------------------------
# Make sure hybrid module is accessible
# -----------------------------------
sys.path.append("/content/drive/MyDrive/veritasAI")

from final_hybrid_system import verify_hybrid
from functools import lru_cache   # add this import

# ... (rest of your imports and global cross_encoder)


# -----------------------------------
# Load CrossEncoder ONLY ONCE (global)
# -----------------------------------
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


# =========================================================
# 1️⃣ URL Handshake Check
# =========================================================
def check_url_exists(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)

        if response.status_code < 400:
            return True

        # Some academic sites block HEAD → fallback to GET
        response = requests.get(url, allow_redirects=True, timeout=5)
        return response.status_code < 400

    except:
        return False


# =========================================================
# 2️⃣ Detect PDF URL
# =========================================================
def is_pdf_url(url):
    return url.lower().endswith(".pdf")


# =========================================================
# 3️⃣ Extract First Page Text from PDF
# =========================================================
def extract_pdf_text(url):
    try:
        response = requests.get(url, timeout=10)
        pdf_bytes = io.BytesIO(response.content)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        if len(doc) == 0:
            return ""

        first_page = doc[0]
        text = first_page.get_text()

        # Usually title is in first ~15 lines
        lines = text.split("\n")
        top_text = " ".join(lines[:15])

        return top_text.strip()

    except:
        return ""


# =========================================================
# 4️⃣ Content Match (HTML + PDF)
# =========================================================
def check_content_match(url, claimed_title, threshold=6.0):
    try:

        # ---------------- PDF CASE ----------------
        if is_pdf_url(url):

            pdf_text = extract_pdf_text(url)

            if not pdf_text:
                return False

            score = cross_encoder.predict([(claimed_title, pdf_text)])[0]

            return score >= threshold

        # ---------------- HTML CASE ----------------
        else:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")

            page_title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else ""
            )

            if not page_title:
                return False

            score = cross_encoder.predict([(claimed_title, page_title)])[0]

            return score >= threshold

    except:
        return False


# =========================================================
# 5️⃣ Main Citation Verification Function
# =========================================================
import time

@lru_cache(maxsize=128) 
def verify_citation(
    title,
    citation_url,
    local_threshold=6.0,
    external_threshold=7.0,
    content_threshold=6.0,
    allow_recovery=True
):
    """
    Multi-layer citation verification with timing:
    1. URL handshake + content match
    2. Hybrid title verification fallback
    """
    total_start = time.time()
    print(f"\n--- verify_citation started for: {title[:50]}... ---")

    # -------------------------
    # Step A: Check URL and content
    # -------------------------
    step_start = time.time()
    url_valid = check_url_exists(citation_url)
    url_time = time.time() - step_start
    print(f"  URL check: {url_time:.2f}s -> valid={url_valid}")

    if url_valid:
        step_start = time.time()
        content_valid = check_content_match(citation_url, title, threshold=content_threshold)
        content_time = time.time() - step_start
        print(f"  Content match: {content_time:.2f}s -> valid={content_valid}")

        if content_valid:
            total_time = time.time() - total_start
            print(f"  ✅ REAL_CITATION (URL+content) total: {total_time:.2f}s")
            return {
                "decision": "REAL_CITATION",
                "method": "URL + CONTENT_MATCH"
            }
        # else: fall through
    else:
        content_valid = False
        content_time = 0

    # -------------------------
    # Step B: Hybrid Fallback
    # -------------------------
    step_start = time.time()
    hybrid_result = verify_hybrid(
        title,
        local_threshold=local_threshold,
        external_threshold=external_threshold
    )
    hybrid_time = time.time() - step_start
    print(f"  Hybrid verification: {hybrid_time:.2f}s -> decision={hybrid_result['decision']}")

    if hybrid_result["decision"] == "REAL":
        total_time = time.time() - total_start
        print(f"  ⚠ HALLUCINATED_CITATION (hybrid found title) total: {total_time:.2f}s")
        return {
            "decision": "HALLUCINATED_CITATION",
            "method": "HYBRID_TITLE_VERIFICATION",
            "title_location": hybrid_result["source"]
        }
    else:
        total_time = time.time() - total_start
        print(f"  ❌ HALLUCINATED_CITATION (not found anywhere) total: {total_time:.2f}s")
        return {
            "decision": "HALLUCINATED_CITATION",
            "method": "NO_URL + HYBRID_FAILED",
            "title_location": "NOT_FOUND_ANYWHERE"
        }