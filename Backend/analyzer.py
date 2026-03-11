# ═══════════════════════════════════════════
# analyzer.py — Resume analysis via Ollama
# Streaming version: yields tokens one by one
# ═══════════════════════════════════════════

import requests
import json
import re
from fastapi import HTTPException
from prompts import build_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME  = "llama3.2:3b"   # ← Change to your model


def stream_analyze_resume(resume_text: str, domain: str):
    """
    Yields raw tokens from Ollama as they are generated.
    Frontend accumulates all tokens then parses the final JSON.
    """
    prompt = build_prompt(resume_text, domain)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,           # stream tokens one by one
        "options": {
            "temperature": 0.1,   # low = consistent JSON output
            "num_predict": 1024,  # enough for full JSON response
            "num_ctx": 4096,      # context window for long resumes
        }
    }

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=180) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Ollama is not running. Start with: ollama serve")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Ollama timed out. Try a smaller model.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))