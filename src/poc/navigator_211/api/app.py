from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .routes import router

app = FastAPI(title="Navigator 211 POC", version="0.1.0")

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

templates = Jinja2Templates(directory="api/templates")

@app.get("/client", response_class=HTMLResponse)
def client_page(request: Request):
    return templates.TemplateResponse("client.html", {"request": request})

class AssistRequest(BaseModel):
    description: str
    consent: bool

@app.post("/client/assist")
def client_assist(req: AssistRequest):
    if not req.consent:
        return JSONResponse({"error": "Consent required"}, status_code=400)
    text = (req.description or "").strip()
    if not text:
        return JSONResponse({"error": "Please enter a description"}, status_code=400)

    summary = "Summary:\n- " + "\n- ".join([s.strip() for s in text.splitlines() if s.strip()][:6])
    questions = [
        "What is your ZIP code and where are you staying right now?",
        "Is there a deadline (eviction notice date, shutoff date, appointment date)?",
        "How many people are in your household and are any minors involved?",
        "Do you feel safe right now? If you are in immediate danger, call 911."
    ]
    return {"suggested_description": summary, "follow_up_questions": questions}

class ClientIntakeRequest(BaseModel):
    description: str
    consent: bool

@app.post("/client/intake")
def client_intake(req: ClientIntakeRequest):
    if not req.consent:
        return JSONResponse({"error": "Consent required"}, status_code=400)
    return {"case_id": "NAV-LOCAL-001", "status": "received"}


# Optional: a tiny landing page so you can demo without Swagger
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
      <body style="font-family: sans-serif">
        <h2>Navigator 211 POC</h2>
        <ul>
          <li><a href="/docs">Swagger UI</a></li>
          <li><a href="/health">Health</a></li>
          <li><a href="/intakes">List intakes</a></li>
          <li><a href="/queues">List queues</a></li>
        </ul>
      </body>
    </html>
    """

# API routes
app.include_router(router)
