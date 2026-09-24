import os
import json
import base64
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import OpenAI
from fastapi import HTTPException
from schemas import LabReportResponse

load_dotenv()

logger = logging.getLogger("ocr_parser")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

PROMPT_TEXT = """
You are a specialized clinical OCR and medical documentation assistant.
Extract all relevant lab test results, patient metadata, and lab header details from the attached document.

Rules:
1. Extract ONLY information explicitly present in the document.
2. Never invent test names, values, units, reference ranges, or patient details.
3. If a value or unit is missing or unreadable, return null for that field.
4. Set 'is_abnormal' to true ONLY if the result is explicitly flagged as high/low/out-of-range on the report.
5. Standardize qualitative results (e.g., 'Positive', 'Negative', 'Non-Reactive') as strings in 'observed_value'.
"""

def try_gemini_ocr(file_bytes: bytes, mime_type: str) -> LabReportResponse:
    image_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[image_part, PROMPT_TEXT],
        config={
            "response_mime_type": "application/json",
            "response_schema": LabReportResponse,
        },
    )
    return response.parsed

def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)

def try_openrouter_ocr(file_bytes: bytes, mime_type: str) -> LabReportResponse:
    base64_image = base64.b64encode(file_bytes).decode('utf-8')
    image_url = f"data:{mime_type};base64,{base64_image}"
    schema_str = json.dumps(LabReportResponse.model_json_schema(), indent=2)

    full_prompt = PROMPT_TEXT + f"\n\nReturn JSON matching this schema:\n{schema_str}"

    response = openrouter_client.chat.completions.create(
        model="google/gemini-2.5-flash",
        extra_body={
            "models": [
                "google/gemma-4-31b-it:free",
                "thinkingmachines/inkling:free"
            ]
        },
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
    parsed = _extract_json(response.choices[0].message.content)
    return LabReportResponse.model_validate(parsed)

def parse_lab_report(file_bytes: bytes, mime_type: str) -> LabReportResponse:
    try:
        report = try_gemini_ocr(file_bytes, mime_type)
        logger.info("[parse_lab_report] Primary OCR model (Gemini Vision) succeeded.")
        return report
    except Exception as gemini_err:
        logger.warning(f"[parse_lab_report] Gemini Vision failed: {gemini_err}. Initiating OpenRouter fallback...")
        try:
            report = try_openrouter_ocr(file_bytes, mime_type)
            logger.info("[parse_lab_report] Fallback OCR model (OpenRouter Vision) succeeded.")
            return report
        except Exception as openrouter_err:
            logger.error(f"[parse_lab_report] Both OCR providers failed! Gemini: {gemini_err} | OpenRouter: {openrouter_err}")
            raise HTTPException(
                status_code=500,
                detail=f"Both OCR providers failed. Gemini: {gemini_err} | OpenRouter: {openrouter_err}"
            )