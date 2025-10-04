import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class API_Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path("./.env"), 
        env_file_encoding='utf-8', 
        extra='allow'
    )
    
    yandex_stt_url: str 
    yandex_iam_token: str 
    yandex_folder_id: str