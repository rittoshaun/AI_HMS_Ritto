import os
import json
import logging
import re
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from fastapi import HTTPException
from schemas import ClinicalNote

load_dotenv()

logger = logging.getLogger("doctor_ai")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

PROMPT_TEMPLATE = """
You are a clinical documentation assistant.
Convert the doctor's consultation into a structured clinical note.

Rules:
1. Only use information explicitly present in the consultation.
2. Never invent symptoms, diagnoses, medications, test results, allergies, or other clinical information.
3. If information is not mentioned, return null.
4. Do not make an autonomous diagnosis.
5. Preserve the doctor's meaning.

Doctor's consultation:
{consultation}
"""

def try_gemini(consultation: str) -> ClinicalNote:
    prompt = PROMPT_TEMPLATE.format(consultation=consultation)
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config = {
            "response_mime_type":"application/json",
            "response_schema":ClinicalNote
        }
    )
    return response.parsed


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    return json.loads(text)


def try_openrouter(consultation: str) -> tuple[ClinicalNote, str]:
    schema_str = json.dumps(ClinicalNote.model_json_schema(), indent =2)
    prompt = PROMPT_TEMPLATE.format(consultation = consultation) + f"Return json in this format: {schema_str}"
    response = openrouter_client.chat.completions.create(
        model="qwen/qwen-2.5-72b-instruct:free",
        extra_body={
            "models" : [
                "inclusionai/ling-3.0-flash-sante:free",
                "deepseek/deepseek-r1:free",
                "google/gemini-2.5-flash-lite",
            ]
        },
        messages = [{"role":"user" , "content":prompt}]
    )
    used_model = response.model
    parsed = _extract_json(response.choices[0].message.content)
    return ClinicalNote.model_validate(parsed), used_model


def Summarize(consultation: str) -> ClinicalNote:
    try:
        note = try_gemini(consultation)
        logger.info("[Summarize] primary model (Gemini) Succeeded")
        return note
    except Exception as gemini_err:
        logger.warning(f"[Summarize] Gemini Failed: {gemini_err}. Switching to OpenRouter")
        try :
            note, used_model = try_openrouter(consultation)
            logger.info(f"[Summarize] Secondary Model (OpenRouter - {used_model}) succeeded")
            return note
        except Exception as openrouter_err:
            logger.error(f"[Summarize] Both models failed. Gemini: {gemini_err} | OpenRouter: {openrouter_err}")
            raise HTTPException(
                status_code=500,
                detail=f"Both primary and fallback models failed. Gemini: {gemini_err} | OpenRouter: {openrouter_err}"
            )