from fastapi import FastAPI
from app.api.mobile.v1.routes import router as mobile_v1_router
from app.api.dashboard.v1.routes import router as dashboard_v1_router
from app.api.client_site.v1.routes import router as client_site_v1_router

app = FastAPI()

app.include_router(mobile_v1_router, prefix="/api/mobile/v1", tags=["mobile v1"])
app.include_router(dashboard_v1_router, prefix="/api/dashboard/v1", tags=["dashboard v1"])
app.include_router(client_site_v1_router, prefix="/api/client_site/v1", tags=["client site v1"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}