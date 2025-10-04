import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class API_Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=Path("./.env"), env_file_encoding='utf-8', extra='allow'
    )
    
    yandex_api: str
    yandex_api_key: str
    