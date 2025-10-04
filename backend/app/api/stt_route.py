import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Cookie, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.stt import mock_stt
from app.services.geocoding import mock_llm_geocoding, geocode_locations
from app.services.routing import get_2gis_route
from app.services.stt import mock_stt
from route_planner_agent.crew import RoutePlannerAgent


router = APIRouter()

class RoutePoint(BaseModel):
    coord: List[float]

class SttRouteResponse(BaseModel):
    transcript: str
    route: List[RoutePoint]

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
    if user_location:
        print(f"User location from cookie: {user_location}")
        # Here you could parse it and use it:
        # lon, lat = map(float, user_location.split(':'))

    temp_path = f"/tmp/{uuid.uuid4()}-{audio.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Perform speech-to-text conversion
        transcript = mock_stt(temp_path)
        os.remove(temp_path)

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

        if not location_names:
            raise HTTPException(
                status_code=404, detail="Could not find locations in the transcript."
            )
        
        # Geocode the locations to get coordinates, using user_location as the city context.
        points_to_route = await geocode_locations(location_names, city="Moscow")

        # Get route from 2GIS API
        route_coords = await get_2gis_route(points_to_route)

        # 5. Format for frontend
        route_for_frontend = [{"coord": c} for c in route_coords]

        return {
            "transcript": transcript,
            "route": route_for_frontend,
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
