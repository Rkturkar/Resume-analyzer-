🧠 AI Resume Analyzer
Analyze resumes locally using FastAPI + Ollama + Vanilla JS. No cloud. No API keys. 100% private.

📁 Project Structure
resume-analyzer/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── backend/
│   ├── main.py          ← FastAPI routes
│   ├── analyzer.py      ← Ollama LLM integration
│   ├── extractor.py     ← PDF text extraction
│   ├── prompts.py       ← Domain-specific prompts
│   └── requirements.txt
│
└── README.md

⚙️ Prerequisites

Python 3.10+
Ollama installed


🚀 Step 1 — Install & Start Ollama
bash# Install Ollama (Mac/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (choose one)
ollama pull llama3        # Recommended — best quality
ollama pull mistral       # Lighter, still great
ollama pull llama3.2      # Smaller, faster

# Start Ollama server
ollama serve

✅ Ollama must be running on http://localhost:11434 before starting the backend.


🐍 Step 2 — Setup Backend
bashcd resume-analyzer/backend

# Create virtual environment
python -m venv venv

# Activate it
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --reload --port 8000

API will be live at: http://localhost:8000
Docs at: http://localhost:8000/docs


🌐 Step 3 — Run Frontend
No build step needed. Just open the file:
bash# Option 1 — Simply open in browser
open frontend/index.html

# Option 2 — Serve with Python (avoids any CORS edge cases)
cd frontend
python -m http.server 3000
# Then open: http://localhost:3000

🔄 Full Usage Flow
1. Open frontend in browser
2. Select your domain (e.g. MERN Stack)
3. Drag & drop your PDF resume into the dropzone
4. Click "Analyze Resume"
5. Wait 20–60 seconds for Ollama to process
6. View full ATS analysis with scores, skills, and suggestions

🤖 Change Model
Edit backend/analyzer.py line 6:
pythonMODEL_NAME = "llama3"     # ← change to: mistral, llama3.2, gemma2, etc.

🔍 Health Check
bashcurl http://localhost:8000/health
Returns Ollama status and available models.

⚠️ Troubleshooting
ProblemFixCannot connect to backendRun uvicorn main:app --reload in /backendOllama is not runningRun ollama serve in a terminalInvalid JSON from LLMSwitch to llama3 model — it's most reliableCould not extract textYour PDF is scanned/image-based. Use a text-based PDFSlow responseNormal — local LLM takes 20–60s depending on hardware