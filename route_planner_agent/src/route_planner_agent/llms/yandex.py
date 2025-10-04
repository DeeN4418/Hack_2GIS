from crewai import BaseLLM
from typing import Any, Dict, List, Optional, Union
import os
import openai

class YandexGPTLLM(BaseLLM):
    """A custom LLM class for YandexGPT that uses the OpenAI SDK compatibility layer."""

    def __init__(self, model: str = "yandexgpt-lite", api_key: Optional[str] = None, folder_id: Optional[str] = None, temperature: Optional[float] = 0.7):
        """
        Initializes the YandexGPTLLM.

        Args:
            model (str): The model name to use (e.g., 'yandexgpt-lite').
            api_key (str, optional): The Yandex Cloud API key. Defaults to YANDEX_API_KEY env var.
            folder_id (str, optional): The Yandex Cloud Folder ID. Defaults to YANDEX_FOLDER_ID env var.
            temperature (float, optional): The temperature for text generation.
        """
        super().__init__(model=model, temperature=temperature)
        
        self.api_key = api_key or os.getenv("YANDEX_API_KEY")
        self.folder_id = folder_id or os.getenv("YANDEX_FOLDER_ID")
        
        if not self.api_key or not self.folder_id:
            raise ValueError("Yandex API key and Folder ID must be provided either as arguments or as environment variables (YANDEX_API_KEY, YANDEX_FOLDER_ID).")

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://llm.api.cloud.yandex.net/v1",
            project=self.folder_id
        )

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Union[str, Any]:
        """Call the YandexGPT LLM with the given messages using the OpenAI client."""
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        model_uri = f"gpt://{self.folder_id}/{self.model}"
        
        response = self.client.chat.completions.create(
            model=model_uri,
            messages=messages,
            max_tokens=2000,
            temperature=self.temperature,
            stream=False # crewai BaseLLM expects a string, not a stream
        )

        return response.choices[0].message.content

    def supports_function_calling(self) -> bool:
        """YandexGPT via OpenAI compatibility layer might support it, but we'll assume not for now to be safe."""
        return False

    def get_context_window_size(self) -> int:
        """Return the context window size of the YandexGPT model."""
        # YandexGPT-Lite has a context window of 8192 tokens.
        return 8192
