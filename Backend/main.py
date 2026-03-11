# ═══════════════════════════════════════════
# main.py — ResumeAI Backend (FastAPI + Groq)
#
# Endpoints:
#   GET  /           → health info
#   GET  /health     → API connection check
#   POST /analyze-stream → streams JSON from Groq
# ═══════════════════════════════════════════ 

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from extractor import extract_text_from_pdf
from prompts import build_prompt
from groq_client import stream_groq_response
import os
from fastapi import FastAPI, UploadFile

# loading the groq api key 
from dotenv import load_dotenv
load_dotenv()  # ← add this

app = FastAPI(title="ResumeAI — Groq Powered", version="1.0.0")

# Allow all origins for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supported domains (must match frontend)
DOMAINS = [
    "Data Science", "MERN Stack", "Data Analytics",
    "Java Fullstack", "Python Developer", "DevOps Engineer",
]


@app.get("/")
def root():
    return {
        "service": "ResumeAI",
        "version": "1.0.0",
        "status":  "running",
        "groq_key_set": bool(os.getenv("GROQ_API_KEY"))
    }


@app.get("/health")
def health():
    """Quick health check — tells frontend if Groq key is configured."""
    key = os.getenv("GROQ_API_KEY", "")
    return {
        "status": "ok",
        "groq":   "connected" if key else "❌ GROQ_API_KEY not set",
        "model":  "llama3-70b-8192"
    }


@app.post("/analyze-stream")
async def analyze_stream(
    domain: str     = Form(...),
    file:   UploadFile = File(...)
):
    """
    Accepts:  domain (form field) + resume PDF (file upload)
    Returns:  StreamingResponse — raw JSON tokens from Groq LLM

    Frontend reads the stream, accumulates all tokens, then
    parses the final string as JSON to render the results.
    """

    # ── Validate domain ──
    if domain not in DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain '{domain}'. Choose from: {', '.join(DOMAINS)}"
        )

    # ── Validate file type ──
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files (.pdf) are supported.")

    # ── Read file bytes ──
    file_bytes = await file.read()

    # ── Validate size (10MB max) ──
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    # ── Extract text from PDF ──
    resume_text = extract_text_from_pdf(file_bytes)

    # ── Guard: must have readable text (not a scanned image PDF) ──
    if len(resume_text.strip()) < 80:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text. Ensure your PDF is not a scanned image."
        )

    # ── Build domain-specific prompt ──
    prompt = build_prompt(resume_text, domain)

    # ── Stream Groq response back to frontend ──
    def generate():
        for token in stream_groq_response(prompt):
            yield token

    return StreamingResponse(generate(), media_type="text/plain")