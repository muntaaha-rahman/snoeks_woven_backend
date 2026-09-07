from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import photos, visits

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Snoeks Wonen - Measurement App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(visits.router)
app.include_router(photos.router)


@app.get("/health")
def health():
    return {"status": "ok"}
