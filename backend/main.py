import sys
import os

# Add the route_planner_agent to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'route_planner_agent', 'src'))

import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.user_location import router as location_router
from backend.app.api.v1.stt_route import router as stt_router
from app.settings.config import API_Settings

settings = API_Settings()

app = FastAPI(title="Voice to Route API",
            docs_url="/api/openapi",
            openapi_url="/api/openapi.json")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(stt_router, prefix="/api", tags=["STT Route"])
app.include_router(location_router, prefix="/api", tags=["User Location"])


@app.get("/health", tags=["Health Check"])
def health_check():
    """A simple health check endpoint."""
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001
    )
