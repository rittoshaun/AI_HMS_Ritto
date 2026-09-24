import os
import logging
from dotenv import load_dotenv
from sarvamai import SarvamAI
from groq import Groq
from doctor_ai import Summarize

load_dotenv()

logger = logging.getLogger("speech_to_text")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

sarvam_client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def speech_to_text_with_fallback(audio_file_path: str) -> dict:
    transcript = None
    detected_language = "unknown"

    try:
        logger.info("[Speech-to-Text] Attempting transcription via Sarvam AI...")
        with open(audio_file_path, "rb") as f:
            response = sarvam_client.speech_to_text.transcribe(
                file=f,
                model="saaras:v3",
                mode="translate",
                language_code="unknown"
            )
        transcript = response.transcript
        detected_language = response.language_code
        logger.info("[Speech-to-Text] Sarvam AI transcription succeeded.")

    except Exception as e:
        logger.warning(f"[Speech-to-Text] Sarvam AI failed: {e}. Switching to Groq Whisper fallback...")

    if not transcript:
        try:
            with open(audio_file_path, "rb") as f:
                transcription_response = groq_client.audio.transcriptions.create(
                    file=(os.path.basename(audio_file_path), f.read()),
                    model="whisper-large-v3-turbo",
                    response_format="json"
                )
            transcript = transcription_response.text
            detected_language = "en"
            logger.info("[Speech-to-Text] Groq Whisper transcription succeeded.")

        except Exception as e:
            logger.error(f"[Speech-to-Text] Groq Whisper failed as well: {e}")
            raise Exception("All Speech-to-Text providers failed.")

    clinical_note = Summarize(transcript)

    return {
        "language": detected_language,
        "transcript": transcript,
        "clinical_note": clinical_note
    }