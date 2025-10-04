import os
import tempfile
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File

from app.services.stt import mock_stt
from app.services.routing import mock_2gis_route
from app.api.v1.stt.schemas import SttRouteResponse

router = APIRouter()

@router.post("/stt-route", response_model=SttRouteResponse)
async def stt_route_endpoint(audio: UploadFile = File(...)):
    """
    Receives an audio file, mocks STT and routing, and returns the result.
    """
    
    # Create a temporary file that works on all OS
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as temp_file:
        temp_path = temp_file.name
        
        # Save the uploaded audio to temporary file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

    try:
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