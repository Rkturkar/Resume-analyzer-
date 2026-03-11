// ═══════════════════════════════════════════
// app.js — ResumeAI (Groq-powered)
// ═══════════════════════════════════════════

const API_BASE = "https://resume-analyzer-w44t.onrender.com";

// ── State ──
let selectedDomain = null;
let selectedFile   = null;

// ═══════════════════════════════════════════
// TYPING ANIMATION — hero headline
// Cycles through phrases with realistic typing
// ═══════════════════════════════════════════
const PHRASES = [
  "Check Resume Score",
  "Find Your Skill Gaps",
  "Beat the ATS System",
  "Get Hired Faster",
];

let phraseIdx = 0;
let charIdx   = 0;
let deleting  = false;

const typedEl  = document.getElementById("typedText"); 
const cursorEl = document.getElementById("cursor");

function typeLoop() {
  const phrase = PHRASES[phraseIdx];

  if (!deleting) {
    // Typing forward
    charIdx++;
    typedEl.textContent = phrase.slice(0, charIdx);

    if (charIdx === phrase.length) {
      // Pause at full phrase, then start deleting
      deleting = true;
      setTimeout(typeLoop, 2200);
      return;
    }
    // Typing speed: vary slightly for natural feel
    setTimeout(typeLoop, 60 + Math.random() * 40);
  } else {
    // Deleting
    charIdx--;
    typedEl.textContent = phrase.slice(0, charIdx);

    if (charIdx === 0) {
      deleting  = false;
      phraseIdx = (phraseIdx + 1) % PHRASES.length;
      setTimeout(typeLoop, 400);  // pause before typing next phrase
      return;
    }
    setTimeout(typeLoop, 28);  // deleting faster than typing
  }
}

// Start after a short initial delay
setTimeout(typeLoop, 600);

// ═══════════════════════════════════════════
// DOMAIN SELECTION
// ═══════════════════════════════════════════
const domainCards = document.querySelectorAll(".d-card");
domainCards.forEach(card => {
  card.addEventListener("click", () => {
    domainCards.forEach(c => c.classList.remove("active"));
    card.classList.add("active");
    selectedDomain = card.dataset.domain;
    checkReady();
  });
});

// ═══════════════════════════════════════════
// FILE UPLOAD — drag/drop + click
// ═══════════════════════════════════════════
const dropzone  = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const dzName    = document.getElementById("dzName");
const dzNameTxt = document.getElementById("dzNameText");

dropzone.addEventListener("click",    () => fileInput.click());
dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("over"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("over"));
dropzone.addEventListener("drop", e => {
  e.preventDefault();
  dropzone.classList.remove("over");
  const f = e.dataTransfer.files[0];
  if (f) handleFile(f);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showError("Only PDF files are supported."); return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showError("File too large. Maximum 10MB."); return;
  }
  selectedFile = file;
  dropzone.classList.add("has-file");
  dzName.classList.remove("hidden");
  dzNameTxt.textContent = file.name;
  hideError();
  checkReady();
}

function checkReady() {
  document.getElementById("analyzeBtn").disabled = !(selectedDomain && selectedFile);
}

// ═══════════════════════════════════════════
// ANALYSIS STEPS for progress bar
// ═══════════════════════════════════════════
const STEPS = [
  [8,  "Reading PDF..."],
  [22, "Extracting resume text..."],
  [38, "Sending to Groq LLM..."],
  [54, "AI analyzing your resume..."],
  [68, "Scoring sections..."],
  [80, "Detecting skill gaps..."],
  [90, "Building action plan..."],
  [96, "Finalizing results..."],
];
let stepTimer = null;

// ═══════════════════════════════════════════
// ANALYZE — main action
// ═══════════════════════════════════════════
document.getElementById("analyzeBtn").addEventListener("click", async () => {
  if (!selectedDomain || !selectedFile) return;

  setLoading(true);
  hideError();
  showProgress();

  const formData = new FormData();
  formData.append("domain", selectedDomain);
  formData.append("file",   selectedFile);

  try {
    const response = await fetch(`${API_BASE}/analyze-stream`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let detail = "Server error. Please try again.";
      try { detail = (await response.json()).detail; } catch {}
      throw new Error(detail);
    }

    // Stream tokens
    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let fullText  = "";
    let chunks    = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      fullText += decoder.decode(value, { stream: true });
      chunks++;
      if (chunks % 15 === 0) setProgStatus("⚡ Receiving AI response...");
    }
    fullText += decoder.decode();

    console.log("📦 Groq output (first 500):", fullText.slice(0, 500));

    const result = parseJSON(fullText);
    if (!result) throw new Error("AI returned invalid data. Please try again.");

    hideProgress();
    renderResults(result);

  } catch (err) {
    hideProgress();
    if (err.message.includes("fetch") || err.message.includes("Failed to fetch")) {
      showError("Cannot connect to backend. Make sure FastAPI is running on port 8000.");
    } else {
      showError(err.message);
    }
  } finally {
    setLoading(false);
  }
});

// ═══════════════════════════════════════════
// JSON PARSER — robust 4-layer
// ═══════════════════════════════════════════
function parseJSON(raw) {
  let s = raw
    .replace(/```json/gi, "").replace(/```/g, "")
    .replace(/^(here is|sure[,!]?|below is|output:)[^\n]*\n/gim, "")
    .trim();

  try { return JSON.parse(s); } catch {}
  const a = s.indexOf("{"), b = s.lastIndexOf("}");
  if (a !== -1 && b > a) { try { return JSON.parse(s.slice(a, b + 1)); } catch {} }
  if (a !== -1)           { try { return JSON.parse(forceClose(s.slice(a))); } catch {} }
  console.error("❌ JSON parse failed:", raw.slice(0, 400));
  return null;
}

function forceClose(str) {
  const stack = [];
  let inStr = false, esc = false;
  for (const ch of str) {
    if (esc) { esc = false; continue; }
    if (ch === "\\" && inStr) { esc = true; continue; }
    if (ch === '"') { inStr = !inStr; continue; }
    if (inStr) continue;
    if (ch === "{" || ch === "[") stack.push(ch === "{" ? "}" : "]");
    if ((ch === "}" || ch === "]") && stack.length) stack.pop();
  }
  return str + stack.reverse().join("");
}

// ═══════════════════════════════════════════
// RENDER RESULTS
// ═══════════════════════════════════════════
function renderResults(d) {
  const resultsEl = document.getElementById("results");
  resultsEl.classList.remove("hidden");
  setTimeout(() => resultsEl.scrollIntoView({ behavior: "smooth", block: "start" }), 80);

  // ── Ring + score ──
  const score = d.ats_score ?? 0;
  const circ  = 2 * Math.PI * 74;   // r=74
  const dash  = (score / 100) * circ;
  const col   = scoreColor(score);
  const ring  = document.getElementById("ringFg");
  ring.style.stroke = col;
  ring.style.filter = `drop-shadow(0 0 10px ${col}55)`;
  setTimeout(() => ring.setAttribute("stroke-dasharray", `${dash} ${circ}`), 120);
  const scoreEl = document.getElementById("ringScore");
  scoreEl.textContent = score;
  scoreEl.style.color = col;

  // ── Verdict ──
  const vEl  = document.getElementById("rVerdict");
  const vKey = (d.overall_verdict || "").replace(/\s+/g, "-");
  vEl.textContent = d.overall_verdict || "--";
  vEl.className   = `r-verdict v-${vKey}`;

  // ── Meta ──
  document.getElementById("mDomain").textContent  = d.domain            || "--";
  document.getElementById("mExp").textContent     = d.experience_level  || "--";
  document.getElementById("mKw").textContent      = `${(d.keywords_found || []).length} found`;
  document.getElementById("rSummary").textContent = d.summary           || "--";

  // ── Section scores ──
  const SEC = {
    contact_info:"Contact Info", professional_summary:"Professional Summary",
    work_experience:"Work Experience", education:"Education",
    skills_section:"Skills Section", projects:"Projects", formatting:"Formatting"
  };
  const barsEl = document.getElementById("sectionBars");
  barsEl.innerHTML = "";
  Object.entries(d.section_scores || {}).forEach(([k, v]) => {
    const c = scoreColor(v);
    barsEl.innerHTML += `
      <div class="bar-row">
        <span class="bar-label">${SEC[k] || k}</span>
        <div class="bar-track">
          <div class="bar-fill" style="width:${v}%;background:${c};box-shadow:0 0 6px ${c}44"></div>
        </div>
        <span class="bar-val" style="color:${c}">${v}</span>
      </div>`;
  });

  // ── Skills ──
  const skEl = document.getElementById("skillsGrid");
  skEl.innerHTML = "";
  (d.skills_quality || []).forEach(s => {
    const c = scoreColor(s.score);
    skEl.innerHTML += `
      <div class="sk-item">
        <div class="sk-top">
          <span class="sk-name">${s.skill}</span>
          <span class="sk-badge ${s.found ? "sb-y" : "sb-n"}">${s.found ? "✓ FOUND" : "✗ MISSING"}</span>
        </div>
        <div class="sk-track">
          <div class="sk-bar" style="width:${s.score}%;background:${c};box-shadow:0 0 5px ${c}44"></div>
        </div>
      </div>`;
  });

  // ── Lists ──
  renderList("strengthsList",  d.strengths        || []);
  renderList("missingSections", d.missing_sections || []);
  renderList("missingKeywords", d.missing_keywords || []);

  // ── Keywords found ──
  document.getElementById("kwFound").innerHTML =
    (d.keywords_found || []).map(k => `<span class="kw-tag">${k}</span>`).join("");

  // ── Action plan ──
  const actEl = document.getElementById("actionList");
  actEl.innerHTML = "";
  (d.suggestions || []).forEach(s => {
    const cls = (s.priority || "low").toLowerCase();
    actEl.innerHTML += `
      <div class="act-item act-${cls}">
        <span class="act-pri">${(s.priority || "").toUpperCase()}</span>
        <span class="act-txt">${s.text}</span>
      </div>`;
  });
}

function renderList(id, items) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = (items?.length ? items : ["None detected"])
    .map(i => `<li>${i}</li>`).join("");
}

function scoreColor(v) {
  if (v >= 75) return "#34d399";   // green
  if (v >= 50) return "#fbbf24";   // amber
  return "#f87171";                // red
}

// ═══════════════════════════════════════════
// RESET
// ═══════════════════════════════════════════
document.getElementById("resetBtn").addEventListener("click", () => {
  selectedDomain = null; selectedFile = null;
  domainCards.forEach(c => c.classList.remove("active"));
  dropzone.classList.remove("has-file", "over");
  dzName.classList.add("hidden");
  fileInput.value = "";
  document.getElementById("analyzeBtn").disabled = true;
  document.getElementById("results").classList.add("hidden");
  hideError(); hideProgress();
  document.getElementById("tool").scrollIntoView({ behavior: "smooth" });
});

// ═══════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════
function setLoading(on) {
  const btn     = document.getElementById("analyzeBtn");
  const label   = document.getElementById("btnLabel");
  const spinner = document.getElementById("btnSpinner");
  btn.disabled  = on;
  label.classList.toggle("hidden", on);
  spinner.classList.toggle("hidden", !on);
}

function showProgress() {
  const block = document.getElementById("progressBlock");
  block.classList.remove("hidden");
  let i = 0;
  setProgFill(STEPS[0][0]); setProgStatus(STEPS[0][1]);
  stepTimer = setInterval(() => {
    i = Math.min(i + 1, STEPS.length - 1);
    setProgFill(STEPS[i][0]); setProgStatus(STEPS[i][1]);
    if (i === STEPS.length - 1) clearInterval(stepTimer);
  }, 2200);
}
function hideProgress() {
  clearInterval(stepTimer);
  document.getElementById("progressBlock").classList.add("hidden");
  setProgFill(0);
}
function setProgFill(p)   { document.getElementById("progFill").style.width = p + "%"; }
function setProgStatus(m) { document.getElementById("progStatus").textContent = m; }
function showError(msg)   { const b = document.getElementById("errorBanner"); b.classList.remove("hidden"); document.getElementById("errorText").textContent = msg; }
function hideError()      { document.getElementById("errorBanner").classList.add("hidden"); }  
