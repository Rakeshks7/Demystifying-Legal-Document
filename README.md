# CiviLex — Legal Clarity for Everyone

Minimal, hackathon-ready starter repo that deploys a demo of **CiviLex** — an AI assistant that simplifies legal documents, highlights risks, and supports clause‑aware Q&A.

## Quick Start (Local Mock Mode)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt -r web/requirements.txt

uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
streamlit run web/app.py
```

Open http://localhost:8501 for the web UI.

## Environment Variables

```
PROJECT_ID=<your-project-id>
LOCATION=asia-south1
UPLOAD_BUCKET=<your-uploads-bucket>
RESULTS_BUCKET=<your-results-bucket>
DOC_PROCESSOR_ID=<document-ai-processor-id>
USE_MOCK=true
```
