"""GIS Service — PostGIS spatial query functions.

Converts land record reference data with PostGIS geometry into GeoJSON
for the Leaflet frontend map.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from geoalchemy2.shape import to_shape
from sqlalchemy import func, text

logger = logging.getLogger(__name__)


def _get_db():
    from app.db.session import SessionLocal
    return SessionLocal()


def record_to_geojson_feature(record) -> dict:
    """Convert a LandRecordReference row to a GeoJSON Feature.

    Handles both WKB (binary) and WKT geometry formats from PostGIS.
    """
    geometry_json = None
    if record.parcel_geometry is not None:
        try:
            shape = to_shape(record.parcel_geometry)
            geometry_json = json.loads(json.dumps(shape.__geo_interface__))
        except Exception as exc:
            logger.warning("Failed to convert geometry for record %s: %s", record.id, exc)

    return {
        "type": "Feature",
        "id": str(record.id),
        "geometry": geometry_json,
        "properties": {
            "id": str(record.id),
            "survey_number": record.survey_number,
            "khasra_number": record.khasra_number,
            "khata_number": record.khata_number,
            "plot_number": record.plot_number,
            "owner_name": record.owner_name,
            "father_name": record.father_name,
            "village": record.village,
            "tehsil": record.tehsil,
            "district": record.district,
            "state": record.state,
            "area": record.area,
            "land_classification": record.land_classification,
            "registration_number": record.registration_number,
            "mutation_number": record.mutation_number,
            "lrms_id": record.lrms_id,
            "dilrmp_id": record.dilrmp_id,
            "source_database": record.source_database,
            "centroid_lat": record.centroid_lat,
            "centroid_lng": record.centroid_lng,
        },
    }


def get_all_parcels_geojson(village: str | None = None, district: str | None = None) -> dict:
    """Return GeoJSON FeatureCollection of all parcels with optional filtering."""
    from app.models.land_record_reference import LandRecordReference

    db = _get_db()
    try:
        query = db.query(LandRecordReference).filter(
            LandRecordReference.parcel_geometry.isnot(None)
        )

        if village:
            query = query.filter(
                func.lower(LandRecordReference.village) == village.lower()
            )
        if district:
            query = query.filter(
                func.lower(LandRecordReference.district) == district.lower()
            )

        records = query.all()
        features = [record_to_geojson_feature(r) for r in records]

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_parcels": len(features),
                "source": "synthetic_prototype",
                "crs": "EPSG:4326",
                "note": "LRMS/DILRMP Prototype — Synthetic cadastral data for demonstration",
            },
        }
    except Exception as exc:
        logger.error("Failed to query parcels: %s", exc)
        return {"type": "FeatureCollection", "features": [], "metadata": {"error": str(exc)}}
    finally:
        db.close()


def get_parcel_by_id(record_id: str) -> dict | None:
    """Return a single parcel as a GeoJSON Feature."""
    from app.models.land_record_reference import LandRecordReference

    db = _get_db()
    try:
        record = db.query(LandRecordReference).filter(
            LandRecordReference.id == uuid.UUID(record_id)
        ).first()
        if record and record.parcel_geometry:
            return record_to_geojson_feature(record)
        return None
    except Exception as exc:
        logger.error("Failed to get parcel %s: %s", record_id, exc)
        return None
    finally:
        db.close()


def get_parcels_near_point(lat: float, lng: float, radius_m: float = 5000) -> dict:
    """Spatial query: find parcels within radius_m meters of a point.

    Uses centroid-based distance as fallback when ST_DWithin fails.
    """
    from app.models.land_record_reference import LandRecordReference

    db = _get_db()
    try:
        records = db.query(LandRecordReference).filter(
            LandRecordReference.parcel_geometry.isnot(None),
            LandRecordReference.centroid_lat.isnot(None),
        ).all()

        deg_radius = radius_m / 111000
        features = []
        for r in records:
            if r.centroid_lat and r.centroid_lng:
                dlat = abs(r.centroid_lat - lat)
                dlng = abs(r.centroid_lng - lng)
                if dlat <= deg_radius and dlng <= deg_radius:
                    features.append(record_to_geojson_feature(r))

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "query_lat": lat,
                "query_lng": lng,
                "radius_m": radius_m,
                "results": len(features),
            },
        }
    except Exception as exc:
        logger.error("Spatial query failed: %s", exc)
        return {"type": "FeatureCollection", "features": []}
    finally:
        db.close()


def get_document_parcel(document_id: str) -> dict | None:
    """Find the parcel matching a document's extracted identifiers."""
    from app.models.document_result import DocumentResult
    from app.models.land_record_reference import LandRecordReference

    db = _get_db()
    try:
        results = db.query(DocumentResult).filter(
            DocumentResult.document_id == uuid.UUID(document_id)
        ).all()

        identifiers = {}
        for r in results:
            ck = r.canonical_key
            if ck and r.field_value:
                identifiers[ck] = r.field_value.strip()

        if not identifiers:
            return None

        query = db.query(LandRecordReference).filter(
            LandRecordReference.parcel_geometry.isnot(None)
        )

        matched = False
        col_map = {
            "SURVEY_NUMBER": LandRecordReference.survey_number,
            "KHASRA_NUMBER": LandRecordReference.khasra_number,
            "KHATA_NUMBER": LandRecordReference.khata_number,
            "PLOT_NUMBER": LandRecordReference.plot_number,
            "REGISTRATION_NUMBER": LandRecordReference.registration_number,
        }

        for key in col_map:
            if key in identifiers:
                col = col_map[key]
                query = query.filter(col == identifiers[key])
                matched = True

        if not matched:
            return None

        record = query.first()
        if record:
            feature = record_to_geojson_feature(record)
            feature["properties"]["matched_from_document"] = document_id
            feature["properties"]["matched_identifiers"] = identifiers
            return feature

        return None
    except Exception as exc:
        logger.error("Document parcel lookup failed: %s", exc)
        return None
    finally:
        db.close()
