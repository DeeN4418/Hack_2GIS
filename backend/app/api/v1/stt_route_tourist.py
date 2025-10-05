import os
import tempfile
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Cookie, HTTPException
from typing import List, Optional

from pydantic import BaseModel

from app.services.stt import stt
from app.services.geocoding import geocode_locations
from app.services.routing import get_2gis_route
from fastapi import APIRouter, UploadFile, File

from backend.app.services.geocoding_tourist import geocode_locations_tourist
from tourist_route_planner.crew import TouristRoutePlanner # type:ignore
from app.api.v1.schemas import SttRouteResponse
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/stt-route-tourist", response_model=SttRouteResponse)
async def stt_route_tourist_endpoint(
    audio: UploadFile = File(...),
    user_location: Optional[str] = Cookie(None)
):
    """
    Receives an audio file, mocks STT, geocodes text to points,
    and returns the result.
    """
    
     # Create a temporary file that works on all OS
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as temp_file:
        temp_path = temp_file.name
        
        # Save the uploaded audio to temporary file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

    try:
        # 1. Mock Speech-to-Text
        transcript = await stt(temp_path)

        if not transcript:
            raise HTTPException(
                status_code=400, detail="Could not understand audio."
            )

        # Use the crew to get location names
        inputs = {'location': transcript}
        crew_result = TouristRoutePlanner().crew().kickoff(inputs=inputs)
        
        # The result from the crew is now a Pydantic model (Itinerary).
        # We need to access the 'locations' attribute to get the list.
        location_names = crew_result.json_dict['locations']
        current_location = crew_result.json_dict['current_location']
        if current_location == "Unknown":
            raise HTTPException(
                status_code=404, detail="Could not find current location in the transcript."
            )


        if not location_names:
            raise HTTPException(
                status_code=404, detail="Could not find locations in the transcript."
            )
        
        # Geocode the locations to get coordinates, using user_location as the city context.
        points_to_route = await geocode_locations_tourist(location_names, city=current_location)

        # Get route from 2GIS API
        route_coords = await get_2gis_route(points_to_route)

        # 5. Format for frontend
        route_for_frontend = [{"coord": c} for c in route_coords]
        pivot_route_points = [{"coord": c} for c in points_to_route]

        return {
            "route_type": "pedestrian",
            "transcript": transcript,
            "route": route_for_frontend,
            "pivot_route_points": pivot_route_points
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)