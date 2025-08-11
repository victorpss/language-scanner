from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import joblib
import os
import gdown
import numpy as np

load_dotenv()

MODEL_PATH = "./notebook/language_detection_model.pkl"
GOOGLE_DRIVE_ID = "1z4fQnZVXC4CxfWF-kc-fGX_sD29oi4UF"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

class TextInput(BaseModel):
    text: str

model = None

def ensure_model():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        print("Downloading model from Google Drive...")
        url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_ID}"
        gdown.download(url, MODEL_PATH, quiet=False)
    return joblib.load(MODEL_PATH)

@app.lifespan("startup")
def load_model_on_startup():
    global model
    try:
        model = ensure_model()
        # sanity check
        _ = getattr(model, "predict_proba", None)
        _ = getattr(model, "classes_", None)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

@app.get("/")
def root():
    return {"service": "language-detector", "status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/predict")
def predict_language(input_data: TextInput):
    text = input_data.text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texto vazio")
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        probabilities = model.predict_proba([text])[0] 
        language_labels = model.classes_
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    top_5_indices = np.argsort(probabilities)[::-1][:5]  
    top_5_languages = [(language_labels[i], round(probabilities[i] * 100, 2)) for i in top_5_indices]

    return {"predictions": top_5_languages}
