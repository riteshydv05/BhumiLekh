"""Synthetic land_records_reference table for cross-database verification.

This table represents authorized government land record data for the prototype.
In production, this would be replaced by connections to LRMS/DILRMP databases.

PostGIS geometry column stores parcel boundary polygons (SRID 4326 / WGS84).
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.db.session import Base


class LandRecordReference(Base):
    """Reference land record for cross-database verification.

    Represents an authoritative land record entry. Extracted field values
    are compared against this table to verify accuracy.

    The parcel_geometry column stores PostGIS POLYGON shapes for GIS display.
    """

    __tablename__ = "land_records_reference"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Identifiers
    survey_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True,
    )
    khasra_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True,
    )
    khata_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True,
    )
    plot_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True,
    )
    registration_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True,
    )
    mutation_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )

    # People
    owner_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    father_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    village: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tehsil: Mapped[str | None] = mapped_column(String(200), nullable=True)
    district: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Land details
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    land_classification: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
    )

    # -----------------------------------------------------------------------
    # PostGIS Geometry — parcel boundary polygon (WGS84 / SRID 4326)
    # -----------------------------------------------------------------------
    parcel_geometry = mapped_column(
        Geometry("POLYGON", srid=4326), nullable=True,
        comment="PostGIS parcel boundary polygon (WGS84)",
    )
    centroid_lat: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Pre-computed centroid latitude for fast lookups",
    )
    centroid_lng: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Pre-computed centroid longitude for fast lookups",
    )

    # -----------------------------------------------------------------------
    # Integration System Identifiers
    # -----------------------------------------------------------------------
    lrms_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Land Records Management System identifier",
    )
    dilrmp_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Digital India Land Records Modernisation Programme ID",
    )

    # Source metadata
    source_database: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default="synthetic_prototype",
        comment="Origin: synthetic_prototype | lrms | dilrmp | state_registry",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )

