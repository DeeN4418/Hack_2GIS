import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent

class API_Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding='utf-8', 
        extra='allow'
    )
    
    yandex_stt_url: str 
    yandex_iam_token: str 
    yandex_folder_id: str
    gis_key: str
    places_api_url: str = "https://catalog.api.2gis.com/3.0/items"
    routing_api_url: str = "https://routing.api.2gis.com/routing/7.0.0/global"