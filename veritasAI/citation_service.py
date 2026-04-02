# citation_service.py
import sys
sys.path.append("/content/drive/MyDrive/veritasAI")

from citation_verifier import verify_citation
from recovery_final import recover_and_verify_references



def process_citation_form(title, citation_url):
    """
    Core VeritasAI decision engine.
    Determines citation validity and recovery logic.
    """

    print("\n==============================")
    print("🔎 VeritasAI Citation Analysis")
    print("==============================\n")

    print("Title:", title)
    print("URL:", citation_url)
    print("\n--------------------------------\n")

    verification_result = verify_citation(title, citation_url)
    print(verification_result.get("title_location"))
    # -------------------------------
    # CASE 1: Fully Valid Citation
    # -------------------------------
    if verification_result["decision"] == "REAL_CITATION":
        return {
            "final_status": "VALID_CITATION",
            "details": verification_result
        }
    if not citation_url and verification_result.get("title_location") in ["LOCAL", "EXTERNAL", "FOUND_IN_EXTERNAL_API"]:
        return {
            "final_status": "VALID_CITATION",
            "details": verification_result,
            "message": "Title verified without URL"
        }
    # -------------------------------
    # CASE 2: Title Exists but URL Wrong
    # -------------------------------
    
    if verification_result.get("title_location") in [
        "LOCAL",
        "EXTERNAL",
        "FOUND_IN_EXTERNAL_API"
    ]:
        return {
            "final_status": "HALLUCINATED_CITATION",
            "original_verification": verification_result,
            "message": "Title exists but URL invalid"
        }

    # -------------------------------
    # CASE 3: Title Not Found → Run Recovery
    # -------------------------------
    print("⚠ Title not found anywhere. Activating Reference Recommendation Engine...\n")

    recovery = recover_and_verify_references(title)

    if recovery["status"] == "VERIFIED_REFERENCES_FOUND":
        return {
            "final_status": "HALLUCINATED_WITH_ALTERNATIVES",
            "original_verification": verification_result,
            "verified_alternatives": recovery["verified_references"]
        }

    return {
        "final_status": "HALLUCINATED_NO_ALTERNATIVES",
        "original_verification": verification_result,
        "message": "No verified related references found"
    }