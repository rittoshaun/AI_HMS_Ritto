from typing import Optional
from pydantic import BaseModel, Field

#Inputs
class ConsultationRequest(BaseModel):
    consultation: str

class HistoryRequest(BaseModel):
    history: str


#Outputs
class Vitals(BaseModel):
    temperature: Optional[str] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[str] = None
    respiratory_rate: Optional[str] = None
    oxygen_saturation: Optional[str] = None

class ClinicalNote(BaseModel):
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    vitals: Optional[Vitals] = None
    allergies: Optional[str] = None
    medications: Optional[list[str]] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None

class SummarizePatientHistory(BaseModel):
    summary: str
    previous_diagnosis: list[str]
    medications: list[str]
    allergies: list[str]
    important_findings: list[str]
    recent_events: list[str]

class AudioProcessingResponse(BaseModel):
    detected_language: str
    transcript: str
    clinical_note: ClinicalNote

class LabResult(BaseModel):
    test_name: str = Field(description="Name of the lab test, e.g., Hemoglobin")
    observed_value: Optional[str] = Field(default=None, description="Result value, e.g., '13.5' or 'Positive'")
    unit: Optional[str] = Field(default=None, description="Measurement unit, e.g., 'g/dL'")
    reference_range: Optional[str] = Field(default=None, description="Normal reference range, e.g., '12.0 - 15.5'")
    is_abnormal: Optional[bool] = Field(default=None, description="True if value is outside the reference range")

class LabReportResponse(BaseModel):
    patient_name: Optional[str] = None
    report_date: Optional[str] = None
    lab_name: Optional[str] = None
    results: list[LabResult] = []