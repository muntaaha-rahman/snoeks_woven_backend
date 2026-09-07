from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.photo_storage import save_bytes

router = APIRouter(prefix="/photos", tags=["photos"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
OWNER_TYPES = {"window_treatment", "flooring_section", "insect_screen", "sun_shading", "room"}


@router.post("", response_model=schemas.PhotoOut)
async def upload_photo(
    owner_type: str,
    owner_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    if owner_type not in OWNER_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown owner_type '{owner_type}'")
    if not crud.owner_exists(db, owner_type, owner_id):
        raise HTTPException(status_code=404, detail="Owner item not found")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    extension = Path(file.filename or "").suffix or ".jpg"
    contents = await file.read()
    file_path = save_bytes(contents, extension)

    photo = crud.add_photo(db, owner_type, owner_id, file_path)
    return photo
