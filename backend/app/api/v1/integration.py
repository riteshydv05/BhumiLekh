"""LRMS/DILRMP/GIS Integration API Router.

Exposes endpoints for:
- LRMS record lookup and listing
- GIS parcel GeoJSON (FeatureCollection + individual features)
- Spatial queries (nearby parcels, village filter)
- Document-to-parcel linking
- Integration status
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(
    prefix="/documents/integration",
    tags=["integration"],
)


# ---------------------------------------------------------------------------
# Integration Status
# ---------------------------------------------------------------------------

@router.get("/status")
def integration_status():
    """Return integration system status — active adapters, data source labels."""
    from app.services.lrms_integration_service import get_integration_status
    return get_integration_status()


# ---------------------------------------------------------------------------
# LRMS Lookup
# ---------------------------------------------------------------------------

@router.get("/lrms/lookup")
def lrms_lookup(
    survey_number: Optional[str] = Query(None),
    khasra_number: Optional[str] = Query(None),
    khata_number: Optional[str] = Query(None),
    plot_number: Optional[str] = Query(None),
    registration_number: Optional[str] = Query(None),
    village: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
):
    """Look up a land record in LRMS by identifiers.

    Returns MATCHED, NOT_FOUND, or ERROR with the matching record details.
    At least one identifier must be provided.
    """
    from app.services.lrms_integration_service import lookup_lrms

    identifiers = {}
    if survey_number:
        identifiers["survey_number"] = survey_number
    if khasra_number:
        identifiers["khasra_number"] = khasra_number
    if khata_number:
        identifiers["khata_number"] = khata_number
    if plot_number:
        identifiers["plot_number"] = plot_number
    if registration_number:
        identifiers["registration_number"] = registration_number
    if village:
        identifiers["village"] = village
    if district:
        identifiers["district"] = district

    if not identifiers:
        raise HTTPException(
            status_code=400,
            detail="At least one identifier (survey_number, khasra_number, etc.) is required",
        )

    result = lookup_lrms(identifiers)
    return result.to_dict()


@router.get("/lrms/records")
def lrms_list_records(
    village: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List all LRMS reference records with optional village filter."""
    from app.services.lrms_integration_service import list_lrms_records
    records = list_lrms_records(village=village, limit=limit)
    return {
        "count": len(records),
        "source": "synthetic_prototype",
        "records": records,
    }


# ---------------------------------------------------------------------------
# GIS Parcels — GeoJSON endpoints
# ---------------------------------------------------------------------------

@router.get("/gis/parcels")
def gis_parcels(
    village: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
):
    """Return GeoJSON FeatureCollection of all parcels.

    Optionally filter by village or district.
    Data is served from PostGIS land_records_reference table.
    """
    from app.services.gis_service import get_all_parcels_geojson
    return get_all_parcels_geojson(village=village, district=district)


@router.get("/gis/parcels/nearby")
def gis_parcels_nearby(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(5000, description="Search radius in meters"),
):
    """Spatial query: find parcels near a point (uses PostGIS)."""
    from app.services.gis_service import get_parcels_near_point
    return get_parcels_near_point(lat=lat, lng=lng, radius_m=radius)


@router.get("/gis/parcels/village/{village}")
def gis_parcels_by_village(village: str):
    """Return all parcels for a specific village."""
    from app.services.gis_service import get_all_parcels_geojson
    return get_all_parcels_geojson(village=village)


@router.get("/gis/parcels/{record_id}")
def gis_parcel_detail(record_id: str):
    """Return a single parcel as a GeoJSON Feature."""
    from app.services.gis_service import get_parcel_by_id

    feature = get_parcel_by_id(record_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Parcel not found or has no geometry")
    return feature


# ---------------------------------------------------------------------------
# Document-to-Parcel Linking
# ---------------------------------------------------------------------------

@router.get("/documents/{document_id}/parcel")
def document_parcel(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Find the GIS parcel matching a document's extracted identifiers.

    Looks up the document's canonical fields (Survey No., Khasra, Khata, etc.),
    finds the matching reference record in PostGIS, and returns it as GeoJSON.
    """
    from app.models.document import Document
    from app.services.gis_service import get_document_parcel

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    feature = get_document_parcel(str(document_id))
    if not feature:
        return {
            "status": "NOT_FOUND",
            "document_id": str(document_id),
            "message": "No matching parcel found for this document's extracted identifiers",
        }

    return {
        "status": "MATCHED",
        "document_id": str(document_id),
        "parcel": feature,
    }
