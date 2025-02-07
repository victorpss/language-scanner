from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import os
import gdown
import numpy as np

MODEL_PATH = "./notebook/language_detection_model.pkl"
GOOGLE_DRIVE_ID = "1z4fQnZVXC4CxfWF-kc-fGX_sD29oi4UF"

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

if not os.path.exists(MODEL_PATH):
    print("Downloading model from Google Drive...")
    gdown.download(f"https://drive.google.com/uc?id={GOOGLE_DRIVE_ID}", MODEL_PATH, quiet=False)

model = joblib.load(MODEL_PATH)

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

@app.post("/predict/")
def predict_language(input_data: TextInput):
    text = input_data.text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texto vazio")

    probabilities = model.predict_proba([text])[0]
    
    language_labels = model.classes_

    top_5_indices = np.argsort(probabilities)[::-1][:5]  
    top_5_languages = [(language_labels[i], round(probabilities[i] * 100, 2)) for i in top_5_indices]

    return {"predictions": top_5_languages}
