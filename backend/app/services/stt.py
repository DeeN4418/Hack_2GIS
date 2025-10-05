import json
import os
import urllib
import urllib.request
import logging
from backend.app.settings.config import API_Settings
import aiofiles
import httpx
from io import BytesIO
from pydub import AudioSegment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = API_Settings()

async def stt(audio_path: str) -> str:
    """
    Converts an audio file to text using Yandex SpeechKit.
    The audio is converted to OGG (Opus) format before sending.

    Args:
        audio_path (str): Path to the audio file

    Returns:
        str: Recognized text
    """
    if not os.path.exists(audio_path):
        return f"File not found: {audio_path}"

    try:
        # Convert audio to ogg format in memory
        audio = AudioSegment.from_file(audio_path)
        
        with BytesIO() as ogg_buffer:
            audio.export(ogg_buffer, format="ogg", codec="libopus")
            contents = ogg_buffer.getvalue()
        
        params = {
            "topic": "general",
            "folderId": settings.yandex_folder_id,
            "lang": "ru-RU"
        }
        
        headers = {
            "Authorization": f"Bearer {settings.yandex_iam_token}",
            "Content-Type": "audio/ogg;codecs=opus"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.yandex_stt_url,
                params=params,
                content=contents,
                headers=headers
            )
            response.raise_for_status()

        response_text = response.text
        logger.info(f"Yandex STT API response: {response_text}")
        
        decoded_data = response.json()
        
        if decoded_data.get("error_code") is not None:
            return f"Error Yandex SpeechKit: {decoded_data}"
        
        result = decoded_data.get("result", "")
        return result

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.request.url} - {e.response.status_code} - {e.response.text}")
        return f"Error Yandex SpeechKit: {e.response.text}"
    except Exception as e:
        logger.error(f"An unexpected error occurred in STT service: {e}")
        return "Произошла ошибка при распознавании речи."
