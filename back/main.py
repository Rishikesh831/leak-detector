from fastapi import FastAPI
from dashboard.metric import router as dashboard_router
from process.upload import router as upload_router
from process.process import router as process_router

app = FastAPI(
    title="Leak Detector API",
    description="Backend for ML-based financial anomaly detection",
    version="0.1.0"
)

# Include routers
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(upload_router, prefix="/back", tags=["Upload"])
app.include_router(process_router, prefix="/back", tags=["Processing"])

@app.get("/health")
def health_check():
    return {"status": "ok"}