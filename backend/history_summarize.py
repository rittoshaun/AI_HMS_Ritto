import os
import json
import logging
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from fastapi import HTTPException
from schemas import SummarizePatientHistory

load_dotenv()

logger = logging.getLogger("history_summarize")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
openrouter_client = OpenAI(
    base_url="[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

PROMPT_TEMPLATE = """
You are a clinical documentation assistant.
Summarize the patient's previous medical history for a doctor who is about to see the patient.

Rules:
1. Use ONLY information present in the provided history.
2. Never invent diagnoses, medications, allergies, symptoms, test results, or other medical information.
3. Do not make a new diagnosis.
4. Highlight clinically relevant information.
5. If a category has no information, return an empty list.
6. Keep the summary concise.

Patient history:
{history}
"""

def try_gemini_history(history: str) -> SummarizePatientHistory:
    prompt = PROMPT_TEMPLATE.format(history=history)
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": SummarizePatientHistory,
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

def try_openrouter_history(history: str) -> SummarizePatientHistory:
    schema_str = json.dumps(SummarizePatientHistory.model_json_schema(), indent=2)
    prompt = PROMPT_TEMPLATE.format(history=history) + f"\n\nReturn JSON strictly matching this schema:\n{schema_str}"

    response = openrouter_client.chat.completions.create(
        model="google/gemini-2.5-flash-lite",
        extra_body={
            "models": [
                "meta-llama/llama-3.3-70b-instruct:free",
                "deepseek/deepseek-r1:free"
            ]
        },
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    parsed = _extract_json(response.choices[0].message.content)
    return SummarizePatientHistory.model_validate(parsed)

def PatientHistorySummarize(history: str) -> SummarizePatientHistory:
    try:
        summary = try_gemini_history(history)
        logger.info("[PatientHistorySummarize] Primary model (Gemini) succeeded.")
        return summary
    except Exception as gemini_err:
        logger.warning(f"[PatientHistorySummarize] Gemini failed: {gemini_err}. Initiating OpenRouter fallback...")
        try:
            summary = try_openrouter_history(history)
            logger.info("[PatientHistorySummarize] Fallback model (OpenRouter) succeeded.")
            return summary
        except Exception as openrouter_err:
            logger.error(f"[PatientHistorySummarize] Both models failed! Gemini: {gemini_err} | OpenRouter: {openrouter_err}")
            raise HTTPException(
                status_code=500,
                detail=f"Both primary and fallback models failed. Gemini: {gemini_err} | OpenRouter: {openrouter_err}"
            )