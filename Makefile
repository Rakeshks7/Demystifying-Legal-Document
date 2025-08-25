run-api:
	uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload

run-web:
	streamlit run web/app.py
