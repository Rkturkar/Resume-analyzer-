# ═══════════════════════════════════════════
# groq_client.py — Groq API streaming client
#
# Uses Groq's OpenAI-compatible REST API to
# stream tokens from llama3-70b-8192 (fastest
# model with best JSON reliability).
# ═══════════════════════════════════════════

import os
import json
import requests
from fastapi import HTTPException

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


GROQ_MODEL = "llama-3.3-70b-versatile"


def stream_groq_response(prompt: str):
    """
    Sends the resume analysis prompt to Groq API and yields
    raw text tokens one at a time using server-sent events.

    Groq uses OpenAI-compatible /chat/completions endpoint
    with stream=True → returns SSE events like:
      data: {"choices":[{"delta":{"content":"{"}}]}
      data: [DONE]
    """

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY environment variable is not set. "
                   "Get your key at https://console.groq.com"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                # System message: force the model into strict JSON output mode
                "role": "system",
                "content": (
                    "You are an expert ATS (Applicant Tracking System) analyst. "
                    "You ALWAYS respond with ONLY a valid JSON object — no markdown, "
                    "no explanation, no preamble. Start your response with { and end with }."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True,          # SSE streaming
        "temperature": 0.1,      # very low = consistent, structured JSON output
        "max_tokens": 2048,      # enough for full analysis JSON
        "top_p": 0.9,
    }

    try:
        # Make streaming HTTP request (don't load whole response at once)
        with requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        ) as resp:

            # Handle API errors
            if resp.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid Groq API key.")
            if resp.status_code == 429:
                raise HTTPException(status_code=429, detail="Groq rate limit hit. Try again in a moment.")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Groq API error: {resp.text[:200]}")

            # Parse SSE (server-sent events) line by line
            for line in resp.iter_lines():
                if not line:
                    continue

                # SSE format: lines start with "data: "
                if isinstance(line, bytes):
                    line = line.decode("utf-8")

                if not line.startswith("data: "):
                    continue

                data_str = line[6:]  # strip "data: " prefix

                # Stream is done
                if data_str.strip() == "[DONE]":
                    break

                # Parse the JSON chunk
                try:
                    chunk = json.loads(data_str)
                    # Extract the text delta from the chunk
                    delta = chunk["choices"][0]["delta"]
                    token = delta.get("content", "")
                    if token:
                        yield token  # send token to frontend immediately
                except (json.JSONDecodeError, KeyError, IndexError):
                    # Skip malformed chunks (can happen at stream boundaries)
                    continue

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot reach Groq API. Check your internet connection.")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Groq API timed out. Try again.")
    except HTTPException:
        raise  # re-raise our own HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")