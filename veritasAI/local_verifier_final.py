import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss

LOAD_DIR = "/content/drive/MyDrive/model"

# Load BM25
with open(f"{LOAD_DIR}/bm25_index.pkl", "rb") as f:
    bm25 = pickle.load(f)

bm25_df = pd.read_csv(f"{LOAD_DIR}/bm25_doc_map.csv")

# Load FAISS
index = faiss.read_index(f"{LOAD_DIR}/faiss_index.bin")
dense_df = pd.read_csv(f"{LOAD_DIR}/dense_doc_map.csv")

# Load models
dense_model = SentenceTransformer("all-MiniLM-L6-v2")
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def bm25_retrieve(query, k=50):
    tokens = query.lower().split()
    scores = bm25.get_scores(tokens)

    top_idx = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:k]

    results = bm25_df.iloc[top_idx].copy()
    return results


def dense_retrieve(query, k=50):
    q_emb = dense_model.encode([query], normalize_embeddings=True)
    scores, idx = index.search(q_emb, k)
    results = dense_df.iloc[idx[0]].copy()
    return results


def verify_paper_existence(query, tau=6):
    bm25_res = bm25_retrieve(query, 50)
    dense_res = dense_retrieve(query, 50)

    combined = (
        pd.concat([bm25_res, dense_res])
        .drop_duplicates(subset="paper_id")
        .reset_index(drop=True)
    )

    pairs = [
        (query, row["title"] + " " + row["abstract"])
        for _, row in combined.iterrows()
    ]

    scores = cross_encoder.predict(pairs)

    best_score = float(np.max(scores))
    decision = "EXISTS" if best_score >= tau else "NOT EXISTS"

    return {
        "decision": decision,
        "score": best_score
    }
