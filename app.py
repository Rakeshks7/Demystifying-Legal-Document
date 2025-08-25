
import os, requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8080")

st.set_page_config(page_title="CiviLex — Legal Clarity", layout="centered")
st.title("CiviLex — Legal Clarity")
st.caption("**Disclaimer:** This demo provides informational summaries and is not legal advice.")

with st.sidebar:
    st.markdown("### Settings")
    API_BASE = st.text_input("API Base URL", API_BASE)
    if st.button("Health Check"):
        try:
            r = requests.get(f"{API_BASE}/health", timeout=10)
            st.json(r.json())
        except Exception as e:
            st.error(f"API not reachable: {e}")

uploaded = st.file_uploader("Upload contract (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])

def upload_via_api(filename: str, data: bytes):
    try:
        r = requests.post(f"{API_BASE}/upload-url", params={"filename": filename}, timeout=10)
        info = r.json()
        if "url" in info and info["url"].startswith("/mock"):
            return filename  # mock mode
        else:
            headers = info.get("headers", {})
            put = requests.put(info["url"], data=data, headers=headers, timeout=30)
            put.raise_for_status()
            return filename
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

if uploaded is not None:
    st.info("Uploading…")
    key = upload_via_api(uploaded.name, uploaded.read())
    if key:
        st.success("Uploaded. Processing…")
        with st.spinner("Summarizing and extracting risks…"):
            r = requests.post(f"{API_BASE}/process", json={"filename": key}, timeout=120)
            if r.status_code == 200:
                result = r.json()
                st.subheader("TL;DR")
                st.write(result.get("tldr", ""))

                st.subheader("Risks & Obligations")
                risks = result.get("risks", [])
                if risks:
                    for i, rk in enumerate(risks, 1):
                        st.markdown(f"**{i}. Severity:** {rk.get('severity','')}\n\n- *Clause:* {rk.get('clause_text','')}\n- *Why it matters:* {rk.get('why_it_matters','')}\n- *Deadline:* {rk.get('deadline','')}\n- *Action:* {rk.get('recommended_action','')}")
                else:
                    st.write("No significant risks detected.")

                st.subheader("Checklist")
                for item in result.get("checklist", []):
                    st.markdown(f"- {item}")

                st.subheader("Ask a Question")
                q = st.text_input("Your question about this document")
                if st.button("Ask") and q.strip():
                    qq = {"document_text": result.get("tldr",""), "question": q}
                    ans = requests.post(f"{API_BASE}/qa", json=qq, timeout=60).json()
                    st.markdown("**Answer:** " + ans.get("answer",""))
                    if "evidence" in ans:
                        st.caption("Evidence: " + ans["evidence"])
            else:
                st.error(f"Processing failed: {r.text}")
