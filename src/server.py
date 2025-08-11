from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import logging, os, joblib, gdown, numpy as np
from threadpoolctl import threadpool_limits

load_dotenv()
logger = logging.getLogger("uvicorn.error")

MODEL_PATH = os.getenv("MODEL_PATH", "./notebook/language_detection_model.pkl")
GOOGLE_DRIVE_ID = os.getenv("GOOGLE_DRIVE_ID", "1z4fQnZVXC4CxfWF-kc-fGX_sD29oi4UF")

ALLOWED = [o.strip() for o in os.getenv(
    "ALLOW_ORIGINS",
    "http://localhost:3000,http://localhost:5173,https://language-scanner.vercel.app"
).split(",")]

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextInput(BaseModel):
    text: str

@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}")
    return JSONResponse(status_code=500, content={"detail": f"Internal error: {exc}"})

model = None

def ensure_model():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_ID}"
        gdown.download(url, MODEL_PATH, quiet=False)
    return joblib.load(MODEL_PATH)

@app.on_event("startup")
def load_model_on_startup():
    global model
    model = ensure_model()
    assert hasattr(model, "predict_proba")
    assert hasattr(model, "classes_")
    print("Model loaded successfully.")

@app.get("/")
def root():
    return {"service": "language-detector", "status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ping")
def ping(payload: dict):
    return {"ok": True, "echo": payload}

@app.get("/model-info")
def model_info():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"classes": [str(c) for c in list(getattr(model, "classes_", []))]}

@app.post("/predict-dry")
def predict_dry(input_data: TextInput):
    return {"ok": True, "len": len(input_data.text)}

@app.post("/predict")
@app.post("/predict/")
def predict_language(input_data: TextInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    text = input_data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Texto vazio")

    try:
        print("predict: calling predict_proba...")
        probs = model.predict_proba([text])[0]
        print("predict: predict_proba done.")

        labels = [str(x) for x in getattr(model, "classes_", [])]
        idx = np.argsort(probs)[::-1][:5]
        top5 = [[labels[i], round(float(probs[i]) * 100, 2)] for i in idx]
        return {"predictions": top5}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")