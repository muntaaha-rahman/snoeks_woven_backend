import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def make_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Photo(Base):
    """A photo attached to any single measurement item (polymorphic owner)."""

    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=make_uuid)
    owner_type: Mapped[str] = mapped_column(String)  # e.g. "window_treatment", "room"
    owner_id: Mapped[str] = mapped_column(String, index=True)
    file_path: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=make_uuid)

    customer_name: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    postal_code: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String, default="")
    email: Mapped[str] = mapped_column(String, default="")
    visit_date: Mapped[date] = mapped_column(Date)
    surveyor_name: Mapped[str] = mapped_column(String)
    property_notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    email_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    rooms: Mapped[list["Room"]] = relationship(
        back_populates="visit", cascade="all, delete-orphan", order_by="Room.position"
    )


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=make_uuid)
    visit_id: Mapped[str] = mapped_column(ForeignKey("visits.id"))
    name: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(default=0)

    visit: Mapped["Visit"] = relationship(back_populates="rooms")

    window_treatments: Mapped[list["WindowTreatment"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    flooring_sections: Mapped[list["FlooringSection"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    insect_screens: Mapped[list["InsectScreen"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    sun_shadings: Mapped[list["SunShading"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


class WindowTreatment(Base):
    __tablename__ = "window_treatments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=make_uuid)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))

    width_mm: Mapped[float] = mapped_column(Float)
    height_mm: Mapped[float] = mapped_column(Float)
    product: Mapped[str] = mapped_column(String)  # curtain, roller_blind, pleated_blind, venetian_blind
    fabric_colour_sample: Mapped[str] = mapped_column(String, default="")
    frame_reveal_depth_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_side: Mapped[str] = mapped_column(String, default="")  # left, right
    operating_type: Mapped[str] = mapped_column(String, default="")  # chain, cordless, handle, motorised
    profile_colour: Mapped[str] = mapped_column(String, default="")
    window_opening_direction: Mapped[str] = mapped_column(String, default="")
    mounting: Mapped[str] = mapped_column(String, default="")  # wall, ceiling, recess
    note: Mapped[str] = mapped_column(Text, default="")

    room: Mapped["Room"] = relationship(back_populates="window_treatments")


class FlooringSection(Base):
    __tablename__ = "flooring_sections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=make_uuid)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))

    length_m: Mapped[float] = mapped_column(Float)
    width_m: Mapped[float] = mapped_column(Float)
    subfloor_type: Mapped[str] = mapped_column(String, default="")
    levelling_required: Mapped[bool] = mapped_column(Boolean, default=False)
    underfloor_heating_present: Mapped[bool] = mapped_column(Boolean, default=False)
    laying_direction: Mapped[str] = mapped_column(String, default="")
    sound_insulation_requirement: Mapped[str] = mapped_column(String, default="")
    note: Mapped[str] = mapped_column(Text, default="")

    room: Mapped["Room"] = relationship(back_populates="flooring_sections")

    @property
    def area_m2(self) -> float:
        return round(self.length_m * self.width_m, 2)


class InsectScreen(Base):
    __tablename__ = "insect_screens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=make_uuid)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))

    width_mm: Mapped[float] = mapped_column(Float)
    height_mm: Mapped[float] = mapped_column(Float)
    mount_type: Mapped[str] = mapped_column(String, default="")  # surface (op de dag) / recess (in de dag)
    window_door_type: Mapped[str] = mapped_column(String, default="")
    opening_direction: Mapped[str] = mapped_column(String, default="")
    frame_reveal_depth_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    profile_colour: Mapped[str] = mapped_column(String, default="")
    mesh_sample: Mapped[str] = mapped_column(String, default="")
    operating_side: Mapped[str] = mapped_column(String, default="")
    mounting_surface: Mapped[str] = mapped_column(String, default="")
    note: Mapped[str] = mapped_column(Text, default="")

    room: Mapped["Room"] = relationship(back_populates="insect_screens")


class SunShading(Base):
    __tablename__ = "sun_shadings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=make_uuid)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"))

    width_mm: Mapped[float] = mapped_column(Float)
    height_projection_mm: Mapped[float] = mapped_column(Float)
    mounting_surface: Mapped[str] = mapped_column(String, default="")
    obstacles: Mapped[str] = mapped_column(Text, default="")
    wind_resistance: Mapped[str] = mapped_column(String, default="")
    fabric_colour_sample: Mapped[str] = mapped_column(String, default="")
    housing_arm_colour_sample: Mapped[str] = mapped_column(String, default="")
    mounting_height_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")

    room: Mapped["Room"] = relationship(back_populates="sun_shadings")
