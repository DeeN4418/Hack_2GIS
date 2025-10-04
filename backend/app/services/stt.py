import json
import os
import urllib
from app.settings.config import API_Settings

settings = API_Settings()

def mock_stt(audio_path: str) -> str:
    """
    Converts an audio file to text using Yandex SpeechKit

    Args:
    file_path (str): Path to the audio file

    Returns:
    dict: Recognition result with keys:
    - status: "success" or "error"
    - text: recognized text
    - filename: file name
    - error: error description (if any)
    Converts an audio file to text using Yandex SpeechKit

    Args:
    file_path (str): Path to the audio file

    Returns:
    dict: Recognition result with keys:
    - status: "success" or "error"
    - text: recognized text
    - filename: file name
    - error: error description (if any)
    """
    try:

        with open(audio_path, 'rb') as file:
            contents = file.read()
        params = "&".join([
            "topic=general",
            "folderId=%s" % settings.yandex_folder_id,
            "lang=ru-RU"
        ])
        
        url = urllib.request.Request(
            settings.yandex_stt_url % params, 
            data=contents
        )

        url.add_header("Authorization", "Bearer %s" % settings.yandex_iam_token)
        url.add_header("Content-Type", "application/octet-stream")
    
        response = urllib.request.urlopen(url)
        response_data = response.read().decode('UTF-8')
        decoded_data = json.loads(response_data)

        if decoded_data.get("error_code") is not None:
            return {
                "status": "error",
                "error": f"Ошибка Yandex SpeechKit: {decoded_data}",
                "text": "",
                "filename": audio_path
            }
        
        result = decoded_data.get("result", "")
        
        return result
    except Exception as e:
        return {
            "status": "error",
            "error": f"Внутренняя ошибка сервера: {str(e)}"}