import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
import os

# Optional: import MeTTa if used
try:
    from hyperon import MeTTa
except Exception:
    MeTTa = None  # allow fallback if hyperon unavailable

# ----------------------------------------------------------------------------- 
# Initialize
# ----------------------------------------------------------------------------- 
app = FastAPI(title="DocZaddy Diagnosis API")
log = logging.getLogger("doczaddy")
logging.basicConfig(level=logging.INFO)

# ----------------------------------------------------------------------------- 
# CORS setup (frontend access)
# ----------------------------------------------------------------------------- 
# CORRECTED: use exact allowed origin(s) and no wildcard for credentials
ALLOWED_ORIGINS = [
    "https://doc-zaddy.onrender.com",  # <--- your deployed frontend origin (no trailing slash)
    # add other frontend origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------------- 
# Strict CORS middleware: always echo allowed Origin and remove any wildcard
# This replaces/augments the standard CORSMiddleware to ensure proxies/caches
# can't cause responses to include 'Access-Control-Allow-Origin: *'.
# ----------------------------------------------------------------------------- 
@app.middleware("http")
async def ensure_cors_strict(request: Request, call_next):
    origin = request.headers.get("origin")

    # Short-circuit preflight explicitly so proxies see a proper preflight response
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }
        if origin and origin in ALLOWED_ORIGINS:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        else:
            # minimal safe preflight if origin not allowed
            headers["Access-Control-Allow-Methods"] = "OPTIONS"
            headers["Access-Control-Allow-Headers"] = "Content-Type"
        return Response(content="OK", status_code=200, headers=headers)

    # For non-OPTIONS requests, call handler and then override headers
    resp = await call_next(request)

    # If a proxy injected a wildcard header, remove it first
    # Normalize header check to lower-case as some servers may normalize names
    if "access-control-allow-origin" in resp.headers and resp.headers["access-control-allow-origin"] == "*":
        try:
            del resp.headers["access-control-allow-origin"]
        except KeyError:
            pass

    # Echo explicit origin if it's allowed
    if origin and origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Vary"] = "Origin"

    return resp

# ----------------------------------------------------------------------------- 
# Load MeTTa Knowledge Base (best-effort)
# ----------------------------------------------------------------------------- 
metta = None
if MeTTa is not None:
    try:
        metta = MeTTa()
        if os.path.exists("reasoning.metta"):
            metta.run("!(include reasoning.metta)")
            log.info("✅ Loaded reasoning.metta successfully")
        else:
            log.warning("⚠️ reasoning.metta not found, MeTTa loaded but no KB included")
    except Exception as e:
        log.error("❌ Failed to load reasoning.metta: %s", e)
        metta = None
else:
    log.warning("⚠️ hyperon.MeTTa not available; running with simple fallback matcher")

# ----------------------------------------------------------------------------- 
# Simple in-memory disease–symptom reference (fallback / fast scan)
# ----------------------------------------------------------------------------- 
DISEASE_SYMPTOMS = {
    "flu": ["fever", "cough", "sore_throat"],
    "covid19": ["fever", "cough", "loss_of_smell"],
    "cold": ["sneezing", "cough", "runny_nose"],
    "malaria": ["fever", "chills", "headache"],
    "typhoid": ["fever", "abdominal_pain", "weakness"]
}

# ----------------------------------------------------------------------------- 
# Core diagnosis logic (fallback if MeTTa not used)
# ----------------------------------------------------------------------------- 
def score_diseases(symptoms):
    norm = [str(s).strip().lower().replace(" ", "_") for s in symptoms]
    results = []
    for disease, known_symptoms in DISEASE_SYMPTOMS.items():
        matched = len(set(norm) & set(known_symptoms))
        total = len(known_symptoms)
        results.append((disease, matched, total))
    results.sort(key=lambda x: (x[1], (x[1] / x[2] if x[2] else 0), -x[2]), reverse=True)
    return results


def _compute_diagnosis_from_symptoms(symptoms):
    try:
        scores = score_diseases(symptoms)
        results = []
        for disease, matched, total in scores:
            if matched == 0:
                continue
            confidence = matched / total if total else 0
            results.append({
                "disease": disease,
                "matched": matched,
                "total": total,
                "confidence": round(confidence, 2)
            })
        return results
    except Exception as e:
        log.exception("Diagnosis computation failed: %s", e)
        return []

# ----------------------------------------------------------------------------- 
# API Endpoints
# ----------------------------------------------------------------------------- 
@app.post("/api/diagnose")
async def diagnose_api(request: Request):
    data = await request.json()
    symptoms = data.get("symptoms", [])
    log.info(f"[POST /api/diagnose] Symptoms: {symptoms}")
    if not isinstance(symptoms, list):
        return JSONResponse({"error": "symptoms must be a JSON array"}, status_code=400)
    results = _compute_diagnosis_from_symptoms(symptoms)
    return JSONResponse({"results": results})


@app.post("/diagnose")
async def diagnose_alias(request: Request):
    data = await request.json()
    symptoms = data.get("symptoms", [])
    log.info(f"[POST /diagnose] Symptoms: {symptoms} (alias)")
    if not isinstance(symptoms, list):
        return JSONResponse({"error": "symptoms must be a JSON array"}, status_code=400)
    results = _compute_diagnosis_from_symptoms(symptoms)
    return JSONResponse({"results": results})

# ----------------------------------------------------------------------------- 
# Serve React build (static frontend)
# ----------------------------------------------------------------------------- 
PROJECT_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
FRONTEND_BUILD_DIR = os.path.join(FRONTEND_DIR, "build")

if os.path.exists(FRONTEND_BUILD_DIR):
    static_root = FRONTEND_BUILD_DIR
    log.info(f"✅ Serving React from {FRONTEND_BUILD_DIR}")
elif os.path.exists(FRONTEND_DIR) and os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
    static_root = FRONTEND_DIR
    log.info(f"✅ Serving React from {FRONTEND_DIR}")
else:
    static_root = None
    log.warning("⚠️ Frontend build not found in either frontend/build or frontend/")

if static_root:
    static_dir = os.path.join(static_root, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/", StaticFiles(directory=static_root, html=True), name="frontend")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index_file = os.path.join(static_root, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"error": "Frontend index.html not found"}, status_code=404)
else:
    @app.get("/")
    async def api_root():
        return {"message": "DocZaddy API active (no frontend present)"}

# ----------------------------------------------------------------------------- 
# Run manually (use `uvicorn doc_zaddy:app --reload --port 8001`)
# ----------------------------------------------------------------------------- 
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8001"))
    # use 0.0.0.0 so Render / containers can bind correctly
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
