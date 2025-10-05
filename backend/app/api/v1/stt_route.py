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

from route_planner_agent.crew import RoutePlannerAgent # type:ignore
from app.api.v1.schemas import SttRouteResponse
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/stt-route", response_model=SttRouteResponse)
async def stt_route_endpoint(
    audio: UploadFile = File(...),
    user_location: Optional[str] = Cookie(None)
):
    """
    Receives an audio file, mocks STT, geocodes text to points,
    and returns the result.
    """
    
    # Create a temporary file
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
        logger.debug("Transcript:", transcript)

        # 2. Use the crew to process the transcript
        inputs = {'text': transcript}
        crew_result = RoutePlannerAgent().crew().kickoff(inputs=inputs)
        
        # 3. Extract locations from crew result
        logger.debug("Raw crew result:", crew_result)
        logger.debug("Type of crew result:", type(crew_result))
        
        location_names = []
        current_location = "Unknown"
        
        if hasattr(crew_result, 'locations'):
            logger.debug("Crew result has 'locations' attribute")
            location_objects = crew_result.locations
            if hasattr(crew_result, 'current_location'):
                current_location = crew_result.current_location
            
            for loc in location_objects:
                if hasattr(loc, 'name'):
                    location_names.append(loc.name)
                elif isinstance(loc, dict) and 'name' in loc:
                    location_names.append(loc['name'])
        
        elif isinstance(crew_result, dict):
            logger.debug("Crew result is a dictionary")
            if 'locations' in crew_result:
                location_objects = crew_result['locations']
                current_location = crew_result.get('current_location', 'Unknown')
                
                for loc in location_objects:
                    if isinstance(loc, dict) and 'name' in loc:
                        location_names.append(loc['name'])
                    elif isinstance(loc, str):
                        location_names.append(loc)
        
        elif hasattr(crew_result, 'json_dict'):
            logger.debug("Crew result has 'json_dict'")
            result_data = crew_result.json_dict
            if 'locations' in result_data:
                location_objects = result_data['locations']
                current_location = result_data.get('current_location', 'Unknown')
                
                for loc in location_objects:
                    if isinstance(loc, dict) and 'name' in loc:
                        location_names.append(loc['name'])
        
        elif isinstance(crew_result, str):
            logger.debug("Crew result is a string, trying to parse as JSON")
            import json
            try:
                result_data = json.loads(crew_result)
                if 'locations' in result_data:
                    location_objects = result_data['locations']
                    current_location = result_data.get('current_location', 'Unknown')
                    
                    for loc in location_objects:
                        if isinstance(loc, dict) and 'name' in loc:
                            location_names.append(loc['name'])
            except:
                pass
        
        logger.debug("Extracted location names:", location_names)
        logger.debug("Current location:", current_location)

        # Если не удалось определить город из crew результата
        if current_location == "Unknown":
            current_location = user_location or "Москва"
            logger.debug(f"Using fallback location: {current_location}")

        if not location_names:
            # Детальная отладка
            logger.debug("DEBUG - Crew result structure:")
            logger.debug(f"  Type: {type(crew_result)}")
            logger.debug(f"  Dir: {[attr for attr in dir(crew_result) if not attr.startswith('_')]}")
            if hasattr(crew_result, '__dict__'):
                logger.debug(f"  Dict: {crew_result.__dict__}")
            
            raise HTTPException(
                status_code=404, 
                detail=f"Could not find locations in the transcript. Crew result: {crew_result}"
            )
        
        # 4. Geocode the locations to get coordinates
        logger.debug(f"Geocoding {len(location_names)} locations in {current_location}...")
        points_to_route = await geocode_locations(location_names, city=current_location)
        logger.debug("Geocoded coordinates:", points_to_route)

        # 5. Get route from 2GIS API
        logger.debug("Building route with 2GIS API...")
        route_coords = await get_2gis_route(points_to_route)
        logger.debug(f"Route built with {len(route_coords)} points")

        # 6. Format for frontend
        route_for_frontend = [{"coord": c} for c in route_coords]
        pivot_route_points = [{"coord": c} for c in points_to_route]

        return {
            "route_type": "car",
            "transcript": transcript,
            "route": route_for_frontend, 
            "pivot_route_points": pivot_route_points
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in stt_route_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)