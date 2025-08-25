
import os, json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID", "demo")
LOCATION = os.getenv("LOCATION", "asia-south1")
UPLOAD_BUCKET = os.getenv("UPLOAD_BUCKET", "local-uploads")
RESULTS_BUCKET = os.getenv("RESULTS_BUCKET", "local-results")
DOC_PROCESSOR_ID = os.getenv("DOC_PROCESSOR_ID", "processor-id")
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

app = FastAPI(title="CiviLex API", version="0.1.0")

class ProcessReq(BaseModel):
    filename: str

class QAReq(BaseModel):
    document_text: str
    question: str

@app.get("/health")
def health():
    return {"ok": True, "use_mock": USE_MOCK}

@app.get("/schema")
def schema():
    return {
        "tldr": "...",
        "sections": [{"title": "Payment Terms", "original": "...", "plain": "..."}],
        "risks": [{
            "clause_text": "...",
            "why_it_matters": "...",
            "severity": "high",
            "deadline": "YYYY-MM-DD",
            "recommended_action": "Give 30-day notice"
        }],
        "checklist": ["Confirm fees", "Clarify notice period"],
        "qa": [{"question": "What is the notice period?", "answer": "30 days per Clause 7.2", "evidence": "..."}]
    }

@app.post("/upload-url")
def upload_url(filename: str):
    if USE_MOCK:
        return {"url": f"/mock-upload/{filename}", "method": "PUT", "headers": {}}
    try:
        from google.cloud import storage
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(UPLOAD_BUCKET)
        blob = bucket.blob(filename)
        url = blob.generate_signed_url(
            version="v4", expiration=600, method="PUT", content_type="application/octet-stream",
        )
        return {"url": url, "method": "PUT", "headers": {"Content-Type": "application/octet-stream"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signed URL error: {e}" )

def _mock_process():
    return {
        "tldr": "You agree to pay monthly, with a 30-day notice required to terminate. Late payments incur a fee.",
        "sections": [{"title": "Termination", "original": "Either party may terminate with 30 days notice.", "plain": "You or the other side can end this deal if you tell them 30 days ahead."}],
        "risks": [{
            "clause_text": "Agreement auto-renews unless cancelled 30 days before end of term.",
            "why_it_matters": "You might be charged for another term without realizing.",
            "severity": "high",
            "deadline": "2025-12-31",
            "recommended_action": "Set a reminder to cancel if you don't want to continue."
        }],
        "checklist": ["Ask about late fees", "Confirm auto-renewal settings"],
        "qa": [{"question": "What is the notice period?", "answer": "30 days per Termination clause", "evidence": "See 'Termination' section."}]
    }

def _docai_ocr_from_gcs(gcs_uri: str) -> str:
    from google.cloud import documentai_v1 as docai
    client = docai.DocumentProcessorServiceClient()
    name = client.processor_path(PROJECT_ID, LOCATION, DOC_PROCESSOR_ID)
    request = {"name": name, "gcs_document": {"gcs_uri": gcs_uri, "mime_type": "application/pdf"}}
    result = client.process_document(request=request)
    return result.document.text or ""

def _vertex_gemini_summarize(doc_text: str):
    from vertexai import init
    from vertexai.generative_models import GenerativeModel
    init(project=PROJECT_ID, location=LOCATION)
    with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "core_prompt.txt"), "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt = prompt_template.format(doc_text=doc_text[:100000], question="What are the main obligations and risks?")
    model = GenerativeModel("gemini-1.5-pro")
    resp = model.generate_content(prompt, generation_config={"temperature": 0.2, "max_output_tokens": 2048})
    try:
        return json.loads(resp.text)
    except Exception:
        return {"tldr": resp.text, "sections": [], "risks": [], "checklist": [], "qa": []}

@app.post("/process")
def process(req: ProcessReq):
    if USE_MOCK:
        return _mock_process()
    gcs_uri = f"gs://{UPLOAD_BUCKET}/{req.filename}"
    try:
        text = _docai_ocr_from_gcs(gcs_uri)
        result = _vertex_gemini_summarize(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}" )

@app.post("/qa")
def qa(req: QAReq):
    if USE_MOCK:
        return {"answer": "Per the Termination clause, 30 days' notice is required.", "evidence": "Termination section."}
    from vertexai import init
    from vertexai.generative_models import GenerativeModel
    init(project=PROJECT_ID, location=LOCATION)
    with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "core_prompt.txt"), "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt = prompt_template.format(doc_text=req.document_text[:100000], question=req.question)
    model = GenerativeModel("gemini-1.5-pro")
    resp = model.generate_content(prompt, generation_config={"temperature": 0.2, "max_output_tokens": 1024})
    return {"answer": resp.text}
