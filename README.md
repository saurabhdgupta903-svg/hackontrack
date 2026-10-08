# Sach? (सच?) — "Is this forward true?"

An evidence-grounded, multimodal GenAI fact-checking web application built for the Indian information ecosystem. It allows users to verify forwarded WhatsApp texts, screenshots, voice notes, PDFs, and news URLs against authoritative government archives (PIB, RBI, MOHFW) and certified fact-checkers (Alt News, BOOM, Factly).

---

## Live Links & Local Ports

- **Web Application**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 1. What It Does

1. **Multimodal Ingestion**:
   - **Forwarded text**: Strips forward greetings and chains ("share with 10 groups").
   - **Screenshot / Image**: Google Gemini Multimodal OCR extracts text, language, and WhatsApp UI metadata.
   - **Voice Note (.ogg, .opus, .mp3, .m4a, .wav)**: Sarvam AI Saarika STT (with Gemini audio fallback).
   - **PDF Document**: PyMuPDF parses digital circulars; scanned notices undergo Gemini vision parsing.
   - **Web Links**: Trafilatura extracts clean main article text without ads or navigation clutter.
2. **Claim Extraction**: Decomposes input into atomic, testable propositions while preserving the exact original message span.
3. **Strict Allowlist Retrieval**: Queries Google Fact Check Tools API and targeted live searches restricted strictly to allowlisted domains (`pib.gov.in`, `rbi.org.in`, `mohfw.gov.in`, `boomlive.in`, `altnews.in`, `factly.in`, `newschecker.in`, `who.int`, `ptinews.com`, etc.).
   - *Hard Rule*: If no source clears the allowlist, the answer is `"Cannot be confirmed"`, never a guess.
4. **Structured Judging**: Gemini evaluates the claim against only the retrieved passages, outputting strict JSON schema with one of 5 verdicts:
   - `Verified`: Sources confirm it (Green)
   - `False`: Sources contradict it (Red)
   - `Outdated`: Was true once, no longer is (Amber, shows date changed)
   - `Partly supported`: Some parts right, some wrong or missing (Yellow)
   - `Cannot be confirmed`: No reliable source found (Slate)
5. **Citation Verification**: Validates that every cited URL was in the retrieved set and that quoted text exists verbatim in the scraped page.
6. **Multilingual Explanation**: Generates simple ~6th-grade explanations in the user's native Indic language (Hindi, Marathi, Tamil, Bengali, Telugu, Gujarati, plus English) with audio readout.

---

## 2. Project Architecture

```
hackontrack/
├── backend/
│   ├── config.py             # Strict domain allowlist, constants, API keys
│   ├── main.py               # FastAPI app, rate limiter, CORS, lifespan
│   ├── models/
│   │   └── db.py             # SQLAlchemy models, SQLite/Postgres async DB, 24h cache
│   ├── routers/
│   │   ├── check.py          # /api/check/text, /upload, /url, /stream (SSE)
│   │   ├── history.py        # /api/history (list & delete checks)
│   │   ├── feedback.py       # /api/feedback (report wrong verdict)
│   │   └── webhook.py        # /api/webhook/whatsapp (WhatsApp Cloud API channel)
│   ├── schemas/
│   │   └── fact_check.py     # Strict Pydantic models for claims, evidence, verdict
│   └── services/
│       ├── gemini_client.py  # Gemini Multimodal client with fallback cascade
│       ├── ingest.py         # Ingestion for text, image, audio, PDF, URL
│       ├── claim_extractor.py# Atomic claim extraction
│       ├── retriever.py      # Allowlist search + Trafilatura + 24h cache
│       ├── judge.py          # Evidence-grounded JSON schema judging
│       ├── verifier.py       # Citation & passage matching validation
│       ├── explainer.py      # Multilingual explanation & audio generation
│       └── pipeline.py       # Async pipeline orchestrator with SSE streaming
├── frontend/                 # Next.js 14 App Router, TypeScript, Tailwind CSS
│   ├── app/
│   │   ├── page.tsx          # Home Check page (Tabbed input, SSE bar, Results)
│   │   ├── how-it-works/     # 5-step interactive vertical pipeline
│   │   ├── history/          # Saved check history with delete action
│   │   └── about/            # Tech stack, architecture, SDG mapping, limitations
│   └── components/
│       ├── Navbar.tsx        # Top nav with language switcher & WhatsApp status
│       ├── CheckInput.tsx    # 5 tabs, browser MediaRecorder, drag-and-drop
│       ├── ProgressBar.tsx   # Real SSE pipeline stage progress bar
│       ├── ResultView.tsx    # Claim breakdown, audio playback, citations
│       ├── VerdictBadge.tsx  # Icon + color + text accessible badges
│       └── FeedbackModal.tsx # Report incorrect verdict modal
├── prompts/                  # Plain text prompt templates
├── tests/
│   └── test_forwards.py      # Benchmark test suite with 10 real viral forwards
└── demo_samples/             # Test samples (screenshot, voice note, PDF)
```

---

## 3. Environment Variables (`.env`)

```ini
# LLM & Vision
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
GEMINI_PRO_MODEL=gemini-3.1-pro-preview

# Indian Language Speech (Optional)
SARVAM_API_KEY=your_sarvam_key_here

# Existing Fact Checks (Optional)
FACTCHECK_API_KEY=your_google_factcheck_api_key_here

# Evidence Search (Optional, falls back to allowlist web search)
TAVILY_API_KEY=your_tavily_key_here

# Database (local SQLite or Supabase Postgres)
DATABASE_URL=sqlite+aiosqlite:///./data/sach.db

# WhatsApp Cloud API (Optional Channel)
WHATSAPP_VERIFY_TOKEN=sach_verify_token_dev
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
```

---

## 4. Run Locally

### Start Backend (Port 8000)
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start Frontend (Port 3000)
```powershell
cd frontend
npm run dev
```

### Run Accuracy Benchmark (10 Real Forwards)
```powershell
$env:PYTHONPATH="."
python tests/test_forwards.py
```

### Run Demo Checklist Across 5 Modalities
```powershell
$env:PYTHONPATH="."
python scripts/run_demo_checklist.py
```

---

## 5. UN SDG Mapping
- **SDG 4 (Quality Education)**: Digital literacy in 7+ Indian languages.
- **SDG 9 (Industry, Innovation & Infrastructure)**: Hallucination-resilient generative AI architectures.
- **SDG 16 (Peace, Justice & Strong Institutions)**: Preventing viral panic, communal rumors, and economic disinformation.
