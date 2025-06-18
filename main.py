import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise
from config import DATABASE_CONFIG, ALLOWED_HOSTS
from api.client_site.v1 import router as client_site_v1_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ]
)

app = FastAPI(
    title="SpeakNowly API",
    description="Modular FastAPI backend for SpeakNowly platform.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(client_site_v1_router, prefix="/api/v1")

app.mount("/media", StaticFiles(directory="media"), name="media")

register_tortoise(
    app,
    config=DATABASE_CONFIG,
    generate_schemas=False,
    add_exception_handlers=True,
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the SpeakNowly FastAPI application!"}