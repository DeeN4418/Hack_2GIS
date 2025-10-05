import os
import tempfile
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Cookie, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.app.services.stt import mock_stt
from backend.app.services.geocoding import mock_llm_geocoding, geocode_locations
from backend.app.services.routing import get_2gis_route
from fastapi import APIRouter, UploadFile, File

from backend.app.services.stt import mock_stt
from backend.app.api.v1.stt.schemas import SttRouteResponse
from backend.app.services.stt import mock_stt
from route_planner_agent.crew import RoutePlannerAgent


router = APIRouter()

class RoutePoint(BaseModel):
    coord: List[float]

class SttRouteResponse(BaseModel):
    route_type: str
    transcript: str
    route: List[RoutePoint]
    pivot_route_points: List[RoutePoint]

@router.post("/stt-route", response_model=SttRouteResponse)
async def stt_route_endpoint(
    audio: UploadFile = File(...),
    user_location: Optional[str] = Cookie(None)
):
    """
    Receives an audio file, mocks STT, geocodes text to points,
    and returns the result.
    It also reads the user's location from the cookie if available.
    """
    
    # Create a temporary file that works on all OS
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as temp_file:
        temp_path = temp_file.name
        
        # Save the uploaded audio to temporary file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

    try:
        # 1. Mock Speech-to-Text
        transcript = await mock_stt(temp_path)

        if not transcript:
            raise HTTPException(
                status_code=400, detail="Could not understand audio."
            )

        # Use the crew to get location names
        inputs = {'location': transcript}
        crew_result = RoutePlannerAgent().crew().kickoff(inputs=inputs)
        
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
        points_to_route = await geocode_locations(location_names, city=current_location)

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