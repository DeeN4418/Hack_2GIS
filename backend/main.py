from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.app.api.v1.stt_route import router as stt_router
from app.settings.config import API_Settings

settings = API_Settings()
print(settings.yandex_api)


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