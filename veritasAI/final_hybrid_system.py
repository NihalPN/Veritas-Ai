from external_verifier_final import verify_external
from local_verifier_final import verify_paper_existence
import sys

# Make sure path is available when imported externally
sys.path.append("/content/drive/MyDrive/veritasAI")


def verify_hybrid(query,
                  local_threshold=6.0,
                  external_threshold=7.0):

    # 1️⃣ Local verification
    local_result = verify_paper_existence(query, tau=local_threshold)

    if local_result["decision"] == "EXISTS":
        return {
            "decision": "REAL",
            "source": "LOCAL",
            "score": local_result["score"]
        }

    # 2️⃣ External fallback
    external_result = verify_external(query,
                                      threshold=external_threshold)

    if external_result["decision"] == "REAL":
        return {
            "decision": "REAL",
            "source": "EXTERNAL",
            "score": external_result["score"]
        }

    return {
        "decision": "HALLUCINATED",
        "source": "NONE",
        "score": external_result["score"]
    }
