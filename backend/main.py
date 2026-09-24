import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import ConsultationRequest, HistoryRequest, LabReportResponse
from doctor_ai import Summarize
from history_summarize import PatientHistorySummarize
from ocr import parse_lab_report
from openrouter_ai import summarize_openrouter
from speech_to_text import speech_to_text_with_fallback

app = FastAPI(title="Doctor AI Assistant")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "message": "Doctor AI is running"}


@app.post("/doctor-ai")
def doctor_ai(payload: ConsultationRequest):
    note = Summarize(payload.consultation)
    return {"clinical_note": note}


@app.post("/history-summarize")
def history_summarize(payload: HistoryRequest):
    summary = PatientHistorySummarize(payload.history)
    return {"patient_history": summary}


@app.post("/doctor-ai/audio")
async def doctor_ai_audio(audio: UploadFile = File(...)):
    file_path = f"temp_{audio.filename}"
    
    # Save uploaded file temporarily
    with open(file_path, "wb") as f:
        f.write(await audio.read())
        
    try:
        result = speech_to_text_with_fallback(file_path)
        return result
    finally:
        # Always clean up temporary audio files
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/ai/ocr-parser", response_model=LabReportResponse)
async def ocr_parser(file: UploadFile = File(...)):
    """
    Accepts an uploaded lab report image (JPEG/PNG) or PDF, 
    and uses Gemini Vision to extract structured test parameters.
    """
    allowed_types = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file.content_type}. Please upload an image or PDF."
        )
    file_bytes = await file.read()
    parsed_report = parse_lab_report(
        file_bytes=file_bytes, 
        mime_type=file.content_type
    )
    return parsed_report

@app.post("/openrouter")
def dr_ai_openrouter(payload: ConsultationRequest):
    note = summarize_openrouter(payload.consultation)
    return{"clinical_note": note}