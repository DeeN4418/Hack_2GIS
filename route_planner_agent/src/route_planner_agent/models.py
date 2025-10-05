from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class LocationWithTime(BaseModel):
    """Model for location with time information"""
    name: str = Field(description="The name or address of the location")
    time: Optional[str] = Field(description="The time for visiting this location", default=None)

class Itinerary(BaseModel):
    """A model to represent a travel itinerary."""
    locations: List[LocationWithTime] = Field(description="A list of locations with their times")
    current_location: str = Field(description="The current location (city) identified from the user's query.")

class ExtractedPlaces(BaseModel):
    """A model to represent extracted places with times."""
    places: Dict[str, Optional[str]] = Field(description="Dictionary of place names and their times")