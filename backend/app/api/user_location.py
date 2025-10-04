from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UserLocation(BaseModel):
    lat: float
    lon: float

@router.post("/user-location")
def set_user_location(location: UserLocation, response: Response):
    """
    Receives user's location and sets it in a cookie.
    The cookie will be automatically sent by the browser in subsequent requests.
    """
    # Cookie is stored as a simple "lon:lat" string.
    cookie_value = f"{location.lon}:{location.lat}"
    
    # Set the cookie in the response. It will be valid for 1 day.
    response.set_cookie(
        key="user_location",
        value=cookie_value,
        max_age=86400, # 1 day in seconds
        samesite="lax",
    )
    return {"message": "Location stored in cookie."}
