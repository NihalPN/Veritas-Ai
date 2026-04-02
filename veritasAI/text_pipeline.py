import sys
# text_pipeline.py
sys.path.append("/content/drive/MyDrive/veritasAI")

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq
from citation_service import process_citation_form

# =============================
# 🔐 GROQ CLIENT
# =============================
client = Groq(
    api_key="YOUR-GROQ-API-KEY"  # Replace properly (use env variable ideally)
)

# =========================================================
# 🧠 EXTRACTION USING GROQ
# =========================================================
def extract_titles_with_groq(text):
    """
    Extract ALL research paper titles mentioned in the text,
    even if no URL is present. Returns list of (title, url)
    where url may be None.
    """
    # ----- 1. Use Groq to extract titles (strict) -----
    prompt = f"""
Extract ALL research paper titles mentioned in the text below.
- Include EVERY title, even if it looks fake, made‑up, or has no URL.
- For each title, also extract any URL or DOI if present; otherwise set "url" to null.
- Return ONLY a JSON array in this exact format:
  [{{"title": "...", "url": ... or null}}, ...]

TEXT:
{text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict JSON extractor. Output only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )

        raw_output = response.choices[0].message.content.strip()

    except Exception as e:
        print("❌ Groq API error:", e)
        return []

    # -------------------------
    # Safe JSON Parsing
    # -------------------------
    try:
        data = json.loads(raw_output)

    except:
        json_match = re.search(r"\[.*\]", raw_output, re.DOTALL)
        if not json_match:
            print("❌ No JSON detected")
            return []

        try:
            data = json.loads(json_match.group(0))
        except Exception as e:
            print("❌ JSON parsing failed:", e)
            return []

    pairs = []

    for item in data:
        title = item.get("title")
        url = item.get("url")

        if title and isinstance(title, str):
            pairs.append((title.strip(), url))

    return pairs

# =========================================================
# 🧠 VERIFICATION WORKER (for threading)
# =========================================================
def _verify_one(title, url):
    """Wrapper for process_citation_form to be used in threads."""
    try:
        print(f"🔍 Verifying: {title}")
        verification_output = process_citation_form(
            title=title,
            citation_url=url or ""
        )
        return title, url, verification_output, None
    except Exception as e:
        print(f"❌ Verification failed for: {title} - {e}")
        return title, url, None, str(e)

# =========================================================
# 🧠 MAIN TEXT PIPELINE (Threaded)
# =========================================================
def run_text_pipeline(text, max_workers=5):
    """
    Complete pipeline:
    1. Extract citations using Groq
    2. Verify each citation concurrently using a thread pool
    3. Return structured results in the original order
    """
    extracted_pairs = extract_titles_with_groq(text)
    print(f"🧠 Extracted {len(extracted_pairs)} citations")

    results = [None] * len(extracted_pairs)  # pre-allocate to preserve order

    if not extracted_pairs:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {}
        for idx, (title, url) in enumerate(extracted_pairs):
            future = executor.submit(_verify_one, title, url)
            future_to_index[future] = idx

        # Collect as they complete
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            title, url, verification_output, error = future.result()
            if error:
                results[idx] = {
                    "title": title,
                    "url": url,
                    "verification": {"error": error}
                }
            else:
                results[idx] = {
                    "title": title,
                    "url": url,
                    "verification": verification_output
                }

    return results
