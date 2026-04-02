# api_server.py

import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid

from pdf_pipeline import verify_pdf_references
from text_pipeline import run_text_pipeline

app = FastAPI(title="VeritasAI API")

# Allow everything (for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------
# Health Check
# -----------------------------------
@app.get("/")
def root():
    return {"status": "VeritasAI API running"}


# -----------------------------------
# TEXT ENDPOINT
# -----------------------------------
@app.post("/verify-text")
def verify_text(data: dict):
    text = data.get("text", "")

    if not text:
        return {"error": "No text provided"}

    results = run_text_pipeline(text)
    return {"results": results}


# -----------------------------------
# PDF ENDPOINT
# -----------------------------------
@app.post("/verify-pdf")
async def verify_pdf(file: UploadFile = File(...)):

    temp_filename = f"{uuid.uuid4()}.pdf"

    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    results = verify_pdf_references(temp_filename)

    os.remove(temp_filename)

    return {"results": results}