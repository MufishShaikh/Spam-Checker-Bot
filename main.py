from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pickle
import time
import os
import threading
from fastapi.middleware.cors import CORSMiddleware
import telegram_bot

app = FastAPI(title="Spam Detection API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model at startup
try:
    with open('spam_model.pkl', 'rb') as f:
        model = pickle.load(f)
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

@app.on_event("startup")
def startup_event():
    # Only start bot if token is configured
    token = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
    if token != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Starting background Telegram Bot thread...")
        threading.Thread(target=telegram_bot.main, daemon=True).start()
    else:
        print("Telegram bot not started (no token configured).")

class MessageRequest(BaseModel):
    message: str

class MessageResponse(BaseModel):
    is_spam: bool
    confidence: float
    category: str
    processing_time_ms: float

@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return HTMLResponse(content=f"Error loading index.html: {e}", status_code=500)

@app.post("/classify", response_model=MessageResponse)
async def classify_message(request: MessageRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    start_time = time.time()
    
    try:
        # Get prediction
        prediction = model.predict([request.message])[0]
        probabilities = model.predict_proba([request.message])[0]
        confidence = float(probabilities[prediction])
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return MessageResponse(
            is_spam=bool(prediction),
            confidence=confidence,
            category="Spam" if prediction else "Ham",
            processing_time_ms=round(processing_time, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }