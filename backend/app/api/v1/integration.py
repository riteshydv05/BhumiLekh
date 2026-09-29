"""LRMS/DILRMP/GIS Integration API Router — Enhanced.

Endpoints:
- LRMS record lookup and listing
- GIS parcel GeoJSON (FeatureCollection + individual features)
- Spatial queries (ST_DWithin nearby, village/district/state filter)
- Document-to-parcel linking
- NEW: GIS statistics dashboard
- NEW: Filter option lists (villages, districts, states)
- NEW: Parcel overlap detection
- NEW: GeoJSON export
- Integration status
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
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
    """Look up a land record in LRMS by identifiers."""
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
    state: Optional[str] = Query(None),
    land_classification: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
):
    """Return GeoJSON FeatureCollection of all parcels.

    Filters by village, district, state, or land classification.
    """
    from app.services.gis_service import get_all_parcels_geojson
    return get_all_parcels_geojson(
        village=village,
        district=district,
        state=state,
        land_classification=land_classification,
        limit=limit,
    )


@router.get("/gis/parcels/nearby")
def gis_parcels_nearby(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(5000, description="Search radius in metres"),
):
    """Spatial query: find parcels within radius metres (ST_DWithin geography)."""
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
# NEW: GIS Dashboard Statistics
# ---------------------------------------------------------------------------

@router.get("/gis/stats")
def gis_stats():
    """Aggregate statistics for the GIS analytics dashboard.

    Returns total records, geometry coverage %, breakdown by district/state/land class.
    """
    from app.services.gis_service import get_parcel_stats
    return get_parcel_stats()


# ---------------------------------------------------------------------------
# NEW: Filter option lists
# ---------------------------------------------------------------------------

@router.get("/gis/filters/villages")
def gis_filter_villages():
    """Return sorted list of unique villages in the land records database."""
    from app.services.gis_service import get_unique_values
    return {"values": get_unique_values("village"), "field": "village"}


@router.get("/gis/filters/districts")
def gis_filter_districts():
    """Return sorted list of unique districts."""
    from app.services.gis_service import get_unique_values
    return {"values": get_unique_values("district"), "field": "district"}


@router.get("/gis/filters/states")
def gis_filter_states():
    """Return sorted list of unique states."""
    from app.services.gis_service import get_unique_values
    return {"values": get_unique_values("state"), "field": "state"}


@router.get("/gis/filters/land-classifications")
def gis_filter_land_classifications():
    """Return sorted list of unique land classification types."""
    from app.services.gis_service import get_unique_values
    return {"values": get_unique_values("land_classification"), "field": "land_classification"}


# ---------------------------------------------------------------------------
# NEW: Parcel Overlap Detection
# ---------------------------------------------------------------------------

@router.get("/gis/overlaps")
def gis_detect_overlaps(limit: int = Query(50, ge=1, le=200)):
    """Detect overlapping parcel boundaries using ST_Intersects.

    Returns pairs of parcels whose boundaries physically overlap (potential disputes).
    """
    from app.services.gis_service import detect_parcel_overlaps
    return detect_parcel_overlaps(limit=limit)


# ---------------------------------------------------------------------------
# NEW: GeoJSON Export
# ---------------------------------------------------------------------------

@router.get("/gis/export/geojson")
def gis_export_geojson(
    village: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
):
    """Export parcels as a downloadable GeoJSON file."""
    import json
    from app.services.gis_service import get_all_parcels_geojson

    data = get_all_parcels_geojson(village=village, district=district, state=state, limit=limit)
    json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")

    filename = "bhumilekh_parcels"
    if village:
        filename += f"_{village}"
    if district:
        filename += f"_{district}"
    filename += ".geojson"

    return Response(
        content=json_bytes,
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Document-to-Parcel Linking
# ---------------------------------------------------------------------------

@router.get("/documents/{document_id}/parcel")
def document_parcel(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Find the GIS parcel matching a document's extracted identifiers."""
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
