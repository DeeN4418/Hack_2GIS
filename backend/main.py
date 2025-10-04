from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.stt_route import router as stt_router

app = FastAPI(title="Voice to Route API")

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

@app.get("/health", tags=["Health Check"])
def health_check():
    """A simple health check endpoint."""
    return {"ok": True}
