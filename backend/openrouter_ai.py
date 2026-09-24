import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import HTTPException
from schemas import ClinicalNote

load_dotenv

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def summarize_openrouter(consultation: str) -> ClinicalNote:
    prompt = f"""
You are a clinical documentation assistant.
Convert the doctor's consultation into a structured clinical note matching this exact JSON schema:

JSON Schema:
{{
  "chief_complaint": "string or null",
  "history_of_present_illness": "string or null",
  "vitals": {{
    "temperature": "string or null",
    "blood_pressure": "string or null",
    "heart_rate": "string or null",
    "respiratory_rate": "string or null",
    "oxygen_saturation": "string or null"
  }},
  "allergies": "string or null",
  "medications": ["list of medication strings or empty list"],
  "assessment": "string or null",
  "plan": "string or null"
}}

Rules:
1. Only use information explicitly present in the consultation.
2. Never invent symptoms, diagnoses, medications, test results, allergies, or other clinical information.
3. If information is not mentioned, return null.
4. Do not make an autonomous diagnosis.
5. Preserve the doctor's meaning.
6. Respond only with valid JSON, no extra text
Doctor's consultation:
{consultation}
"""
    try:
        response = client.chat.completions.create(
            model = "google/gemini-2.5-flash-lite",
            extra_body={
                "models":[
                    "meta-llama/llama-3.3-70b-instruct:free",
                    "deepseek/deepseek-r1:free"
                ]
            },
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type":"json_object"}
        )
        raw_json = response.choices[0].message.content
        return ClinicalNote.model_validate_json(raw_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenRouter Error: {str(e)}")
        
