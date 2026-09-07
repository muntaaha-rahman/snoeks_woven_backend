from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.photo_storage import save_data_url


def _room_relationship_options():
    return (
        selectinload(models.Visit.rooms).selectinload(models.Room.window_treatments),
        selectinload(models.Visit.rooms).selectinload(models.Room.flooring_sections),
        selectinload(models.Visit.rooms).selectinload(models.Room.insect_screens),
        selectinload(models.Visit.rooms).selectinload(models.Room.sun_shadings),
    )


def _build_item(model_cls, item_in, owner_type: str, pending_photos: list[tuple[str, object, list[str]]]):
    """Construct an ORM item from its input schema, deferring any inline photos
    until after the item has a database-assigned id (see _attach_pending_photos).
    """
    fields = item_in.model_dump(exclude={"new_photos"})
    item = model_cls(**fields)
    if item_in.new_photos:
        pending_photos.append((owner_type, item, item_in.new_photos))
    return item


def _build_room(room_in: schemas.RoomIn, position: int, pending_photos: list[tuple[str, object, list[str]]]) -> models.Room:
    room = models.Room(name=room_in.name, position=position)
    room.window_treatments = [
        _build_item(models.WindowTreatment, item, "window_treatment", pending_photos)
        for item in room_in.window_treatments
    ]
    room.flooring_sections = [
        _build_item(models.FlooringSection, item, "flooring_section", pending_photos)
        for item in room_in.flooring_sections
    ]
    room.insect_screens = [
        _build_item(models.InsectScreen, item, "insect_screen", pending_photos)
        for item in room_in.insect_screens
    ]
    room.sun_shadings = [
        _build_item(models.SunShading, item, "sun_shading", pending_photos)
        for item in room_in.sun_shadings
    ]
    return room


def _attach_pending_photos(db: Session, pending_photos: list[tuple[str, object, list[str]]]) -> None:
    """Flush to assign ids, then decode and store each item's inline base64 photos."""
    if not pending_photos:
        return
    db.flush()
    for owner_type, item, data_urls in pending_photos:
        for data_url in data_urls:
            file_path = save_data_url(data_url)
            if file_path:
                db.add(models.Photo(owner_type=owner_type, owner_id=item.id, file_path=file_path))


def create_visit(db: Session, data: schemas.VisitIn) -> models.Visit:
    visit = models.Visit(
        customer_name=data.customer_name,
        address=data.address,
        postal_code=data.postal_code,
        city=data.city,
        phone=data.phone,
        email=data.email,
        visit_date=data.visit_date,
        surveyor_name=data.surveyor_name,
        property_notes=data.property_notes,
    )

    pending_photos: list[tuple[str, object, list[str]]] = []
    for position, room_in in enumerate(data.rooms):
        visit.rooms.append(_build_room(room_in, position, pending_photos))

    db.add(visit)
    _attach_pending_photos(db, pending_photos)
    db.commit()
    db.refresh(visit)
    return visit


def update_visit(db: Session, visit: models.Visit, data: schemas.VisitIn) -> models.Visit:
    """Replace the visit's top-level fields and its full room tree.

    Note: since rooms/items are fully rebuilt with new ids, any photos previously
    attached to this visit's items are orphaned. Re-attach via new_photos if needed.
    """
    visit.customer_name = data.customer_name
    visit.address = data.address
    visit.postal_code = data.postal_code
    visit.city = data.city
    visit.phone = data.phone
    visit.email = data.email
    visit.visit_date = data.visit_date
    visit.surveyor_name = data.surveyor_name
    visit.property_notes = data.property_notes

    visit.rooms.clear()
    pending_photos: list[tuple[str, object, list[str]]] = []
    for position, room_in in enumerate(data.rooms):
        visit.rooms.append(_build_room(room_in, position, pending_photos))

    _attach_pending_photos(db, pending_photos)
    db.commit()
    db.refresh(visit)
    return visit


def get_visit(db: Session, visit_id: str) -> models.Visit | None:
    return (
        db.query(models.Visit)
        .options(*_room_relationship_options())
        .filter(models.Visit.id == visit_id)
        .first()
    )


def list_visits(
    db: Session,
    search: str | None = None,
    city: str | None = None,
    surveyor_name: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[models.Visit]:
    query = db.query(models.Visit)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.Visit.customer_name.ilike(like),
                models.Visit.address.ilike(like),
                models.Visit.city.ilike(like),
            )
        )
    if city:
        query = query.filter(models.Visit.city.ilike(f"%{city}%"))
    if surveyor_name:
        query = query.filter(models.Visit.surveyor_name.ilike(f"%{surveyor_name}%"))
    if date_from:
        query = query.filter(models.Visit.visit_date >= date_from)
    if date_to:
        query = query.filter(models.Visit.visit_date <= date_to)

    return query.order_by(models.Visit.visit_date.desc(), models.Visit.created_at.desc()).all()


def delete_visit(db: Session, visit: models.Visit) -> None:
    db.delete(visit)
    db.commit()


def set_email_status(db: Session, visit: models.Visit, sent: bool, error: str | None) -> models.Visit:
    visit.email_sent = sent
    visit.email_error = error
    db.commit()
    db.refresh(visit)
    return visit


def add_photo(db: Session, owner_type: str, owner_id: str, file_path: str) -> models.Photo:
    photo = models.Photo(owner_type=owner_type, owner_id=owner_id, file_path=file_path)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


_OWNER_MODELS = {
    "window_treatment": models.WindowTreatment,
    "flooring_section": models.FlooringSection,
    "insect_screen": models.InsectScreen,
    "sun_shading": models.SunShading,
    "room": models.Room,
}


def owner_exists(db: Session, owner_type: str, owner_id: str) -> bool:
    model = _OWNER_MODELS.get(owner_type)
    if model is None:
        return False
    return db.query(model).filter(model.id == owner_id).first() is not None


def photos_for_owner(db: Session, owner_type: str, owner_id: str) -> list[models.Photo]:
    return (
        db.query(models.Photo)
        .filter(models.Photo.owner_type == owner_type, models.Photo.owner_id == owner_id)
        .all()
    )


def _photos_by_owner_type(db: Session, visit_id: str) -> dict[str, list[models.Photo]]:
    """Fetch every photo belonging to a visit's items in one query, grouped by owner_id."""
    all_ids: list[str] = []
    for room in db.get(models.Visit, visit_id).rooms:
        all_ids.append(room.id)
        for item in (*room.window_treatments, *room.flooring_sections, *room.insect_screens, *room.sun_shadings):
            all_ids.append(item.id)

    if not all_ids:
        return {}

    photos = db.query(models.Photo).filter(models.Photo.owner_id.in_(all_ids)).all()
    grouped: dict[str, list[models.Photo]] = {}
    for photo in photos:
        grouped.setdefault(photo.owner_id, []).append(photo)
    return grouped


def _item_dict(item, photos_by_owner: dict[str, list[models.Photo]], columns: list[str]) -> dict:
    result = {col: getattr(item, col) for col in columns}
    result["id"] = item.id
    result["photos"] = [
        {"id": p.id, "owner_type": p.owner_type, "owner_id": p.owner_id, "file_path": p.file_path}
        for p in photos_by_owner.get(item.id, [])
    ]
    return result


def serialize_visit(db: Session, visit: models.Visit) -> dict:
    """Build the full nested VisitOut-shaped dict, attaching photos to each item."""
    photos_by_owner = _photos_by_owner_type(db, visit.id)

    rooms = []
    for room in visit.rooms:
        rooms.append(
            {
                "id": room.id,
                "name": room.name,
                "window_treatments": [
                    _item_dict(
                        wt,
                        photos_by_owner,
                        [
                            "width_mm", "height_mm", "product", "fabric_colour_sample",
                            "frame_reveal_depth_mm", "operating_side", "operating_type",
                            "profile_colour", "window_opening_direction", "mounting", "note",
                        ],
                    )
                    for wt in room.window_treatments
                ],
                "flooring_sections": [
                    {**_item_dict(
                        fs,
                        photos_by_owner,
                        [
                            "length_m", "width_m", "subfloor_type", "levelling_required",
                            "underfloor_heating_present", "laying_direction",
                            "sound_insulation_requirement", "note",
                        ],
                    ), "area_m2": fs.area_m2}
                    for fs in room.flooring_sections
                ],
                "insect_screens": [
                    _item_dict(
                        ins,
                        photos_by_owner,
                        [
                            "width_mm", "height_mm", "mount_type", "window_door_type",
                            "opening_direction", "frame_reveal_depth_mm", "profile_colour",
                            "mesh_sample", "operating_side", "mounting_surface", "note",
                        ],
                    )
                    for ins in room.insect_screens
                ],
                "sun_shadings": [
                    _item_dict(
                        ss,
                        photos_by_owner,
                        [
                            "width_mm", "height_projection_mm", "mounting_surface", "obstacles",
                            "wind_resistance", "fabric_colour_sample", "housing_arm_colour_sample",
                            "mounting_height_mm", "note",
                        ],
                    )
                    for ss in room.sun_shadings
                ],
            }
        )

    return {
        "id": visit.id,
        "customer_name": visit.customer_name,
        "address": visit.address,
        "postal_code": visit.postal_code,
        "city": visit.city,
        "phone": visit.phone,
        "email": visit.email,
        "visit_date": visit.visit_date,
        "surveyor_name": visit.surveyor_name,
        "property_notes": visit.property_notes,
        "created_at": visit.created_at,
        "updated_at": visit.updated_at,
        "email_sent": visit.email_sent,
        "email_error": visit.email_error,
        "rooms": rooms,
    }
