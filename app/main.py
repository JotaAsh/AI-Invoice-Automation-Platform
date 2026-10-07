from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="AI Invoice Automation Platform API",
    version="1.0.0",
    description="Production-ready AP Automation Platform for processing invoices asynchronously.",
)

# Register the main v1 router under the global '/api/v1' prefix
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    """
    Simple health check endpoint for container orchestrators or monitoring tools.
    """
    return {"status": "healthy"}
