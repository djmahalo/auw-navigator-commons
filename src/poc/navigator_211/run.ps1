.\.venv\Scripts\Activate.ps1
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
