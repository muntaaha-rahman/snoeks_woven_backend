from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_type: str
    owner_id: str
    file_path: str


# ---- Window treatment ----

class WindowTreatmentBase(BaseModel):
    width_mm: float
    height_mm: float
    product: str
    fabric_colour_sample: str = ""
    frame_reveal_depth_mm: float | None = None
    operating_side: str = ""
    operating_type: str = ""
    profile_colour: str = ""
    window_opening_direction: str = ""
    mounting: str = ""
    note: str = ""


class WindowTreatmentIn(WindowTreatmentBase):
    new_photos: list[str] = []  # base64 data: URLs captured on-device, saved on submit


class WindowTreatmentOut(WindowTreatmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    photos: list[PhotoOut] = []


# ---- Flooring ----

class FlooringSectionBase(BaseModel):
    length_m: float
    width_m: float
    subfloor_type: str = ""
    levelling_required: bool = False
    underfloor_heating_present: bool = False
    laying_direction: str = ""
    sound_insulation_requirement: str = ""
    note: str = ""


class FlooringSectionIn(FlooringSectionBase):
    new_photos: list[str] = []


class FlooringSectionOut(FlooringSectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    area_m2: float
    photos: list[PhotoOut] = []


# ---- Insect screen ----

class InsectScreenBase(BaseModel):
    width_mm: float
    height_mm: float
    mount_type: str = ""
    window_door_type: str = ""
    opening_direction: str = ""
    frame_reveal_depth_mm: float | None = None
    profile_colour: str = ""
    mesh_sample: str = ""
    operating_side: str = ""
    mounting_surface: str = ""
    note: str = ""


class InsectScreenIn(InsectScreenBase):
    new_photos: list[str] = []


class InsectScreenOut(InsectScreenBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    photos: list[PhotoOut] = []


# ---- Sun shading ----

class SunShadingBase(BaseModel):
    width_mm: float
    height_projection_mm: float
    mounting_surface: str = ""
    obstacles: str = ""
    wind_resistance: str = ""
    fabric_colour_sample: str = ""
    housing_arm_colour_sample: str = ""
    mounting_height_mm: float | None = None
    note: str = ""


class SunShadingIn(SunShadingBase):
    new_photos: list[str] = []


class SunShadingOut(SunShadingBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    photos: list[PhotoOut] = []


# ---- Room ----

class RoomIn(BaseModel):
    name: str
    window_treatments: list[WindowTreatmentIn] = []
    flooring_sections: list[FlooringSectionIn] = []
    insect_screens: list[InsectScreenIn] = []
    sun_shadings: list[SunShadingIn] = []


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    window_treatments: list[WindowTreatmentOut] = []
    flooring_sections: list[FlooringSectionOut] = []
    insect_screens: list[InsectScreenOut] = []
    sun_shadings: list[SunShadingOut] = []


# ---- Visit ----

class VisitIn(BaseModel):
    customer_name: str
    address: str
    postal_code: str
    city: str
    phone: str = ""
    email: str = ""
    visit_date: date
    surveyor_name: str
    property_notes: str = ""
    rooms: list[RoomIn] = []


class VisitListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    customer_name: str
    address: str
    city: str
    visit_date: date
    surveyor_name: str
    created_at: datetime
    email_sent: bool


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    customer_name: str
    address: str
    postal_code: str
    city: str
    phone: str
    email: str
    visit_date: date
    surveyor_name: str
    property_notes: str
    created_at: datetime
    updated_at: datetime
    email_sent: bool
    email_error: str | None
    rooms: list[RoomOut] = []
