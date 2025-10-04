from pydantic import BaseModel, Field
from typing import List

class Itinerary(BaseModel):
    """A model to represent a travel itinerary."""
    locations: List[str] = Field(description="A list of location names for the itinerary.")
    current_location: str = Field(description="The current location (city) identified from the user's query.")
