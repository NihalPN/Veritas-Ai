# Veritas-Ai


# VeritasAI – AI Citation Verification System

## 🔍 Overview

VeritasAI is an AI-powered system designed to detect hallucinated or incorrect citations in LLM-generated content.
It combines **semantic similarity, hybrid retrieval (FAISS + BM25), and external APIs** to verify citation correctness.

---

## 🚀 Features

* Hybrid retrieval using **FAISS (dense search)** and **BM25 (sparse search)**
* Semantic verification using **cross-encoder models**
* Integration with external APIs
* Modular pipeline for citation verification

---

## 🧠 System Architecture

```
Input Query / Citation
        │
        ▼
Retrieval Layer
 ├── FAISS (Dense Search)
 └── BM25 (Keyword Search)
        │
        ▼
Candidate Documents
        │
        ▼
Semantic Verification
 (Cross-Encoder Model)
        │
        ▼
External Verification
 ├── Semantic Scholar API
 ├── SerpAPI
 └── Groq API
        │
        ▼
Final Verification Result
```

---

## 🔌 API Usage

This project uses the following APIs:

* **Semantic Scholar API** → `external_verifier_final.py`
* **SerpAPI** → `recovery_final.py`
* **Groq API** → `text_pipeline.py`

### ⚠️ Important: Add Your API Keys

You need to manually insert your API keys inside the respective files:

* In `external_verifier_final.py` → add your **Semantic Scholar API key**
* In `recovery_final.py` → add your **SerpAPI key**
* In `text_pipeline.py` → add your **Groq API key**

Example:

```python
API_KEY = "your_api_key_here"
```

---

## 📦 Dataset & Index Files

FAISS and BM25 index files are hosted externally due to size:

👉 Download from Kaggle:
https://www.kaggle.com/datasets/hollownihal/veritas-ai

### Setup:

1. Download dataset
2. Extract files
3. Place them inside the `data/` folder

---

## ⚙️ Installation

```
use the ipynb for requirements
```

---

## ▶️ Usage

```
app.py
```

---

## 🛠️ Rebuilding Index (Optional)

```
python build_index.py
```

---

## 👨‍💻 My Contributions

* Designed system architecture
* Built semantic verification module (cross-encoder)
* Implemented hybrid retrieval (FAISS + BM25)
* Performed dataset preprocessing

---

## 🤝 Credits

This project was developed as a collaborative effort.

* **Muhammed Nihal** – Semantic verification, architecture, preprocessing
* **Shaima** – Retrieval modules, BM25 indexing, optimization
* **Anupama** – Recommendation system, Streamlit UI
* **Midhun** – URL validation and API integration

---

## ⚠️ Notes

* Large index files are not included in the repository
* API keys are required to run the system
* This is a simplified version for demonstration

---

## 🎯 Future Improvements

* Deploy using FastAPI
* Improve ranking accuracy
* Add evaluation metrics

---

## 📜 License

For educational and research purposes.
