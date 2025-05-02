from fastapi import FastAPI
from api.client_site.v1.routes import router as client_site_v1_router
# from api.dashboard.v1.routes import router as dashboard_v1_router
# from api.mobile.v1.routes import router as mobile_v1_router

app = FastAPI()

app.include_router(client_site_v1_router, prefix="/api/client_site/v1", tags=["Client Site v1"])
# app.include_router(dashboard_v1_router, prefix="/api/dashboard/v1", tags=["Dashboard v1"])
# app.include_router(mobile_v1_router, prefix="/api/mobile/v1", tags=["Mobile v1"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}