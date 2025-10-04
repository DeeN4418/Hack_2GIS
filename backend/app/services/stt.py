import json
import os
import urllib
import urllib.request
from app.settings.config import API_Settings

settings = API_Settings()

def mock_stt(audio_path: str) -> str:
    """
    Converts an audio file to text using Yandex SpeechKit

    Args:
        audio_path (str): Path to the audio file

    Returns:
        str: Recognized text
    """
    if not os.path.exists(audio_path):
        return f"File not found: {audio_path}"

    audio_extensions = ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac']
    file_ext = os.path.splitext(audio_path)[1].lower()
    if file_ext not in audio_extensions:
        return f"error: file not in audio_extensios: {', '.join(audio_extensions)}"
    
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
            return f"Error Yandex SpeechKit: {decoded_data}"
        
        result = decoded_data.get("result", "")
        return result

    except Exception as e:
        return f"Internal Server Error: {str(e)}"