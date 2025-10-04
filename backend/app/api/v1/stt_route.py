import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from app.services.stt import mock_stt
from app.services.routing import mock_2gis_route

router = APIRouter()

class SttRouteResponse(BaseModel):
    transcript: str
    route: List[List[float]]

@router.post("/stt-route", response_model=SttRouteResponse)
async def stt_route_endpoint(audio: UploadFile = File(...)):
    """
    Receives an audio file, mocks STT and routing, and returns the result.
    """
    # Use a temporary file to store the uploaded audio
    temp_path = f"/tmp/{uuid.uuid4()}-{audio.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # 1. Mock Speech-to-Text
        transcript = mock_stt(temp_path)

        # 2. Mock 2GIS Routing
        route_coords = mock_2gis_route(transcript)

        return {
            "transcript": transcript,
            "route": route_coords,
        }
    finally:
        # 3. Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
