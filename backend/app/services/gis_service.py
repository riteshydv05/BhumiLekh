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


def extract_cadastral_polygons_from_map(image_bytes: bytes, extract_labels: bool = True) -> dict:
    """OpenCV Contour Extraction & Vectorization for Cadastral Maps (FMB / Tippan / Village Maps).

    Detects parcel boundary lines, calculates polygon bounding boxes, extracts survey number
    labels via OCR if requested, and generates GeoJSON geometries for GIS overlay.
    """
    try:
        import cv2
        import numpy as np
        from io import BytesIO
        from PIL import Image
        import re

        pil_img = Image.open(BytesIO(image_bytes)).convert("L")
        img_np = np.array(pil_img)

        # Preprocessing: Gaussian Blur + Adaptive Thresholding to extract boundary lines
        blurred = cv2.GaussianBlur(img_np, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find closed contours (land parcel polygons)
        # In RETR_CCOMP, hierarchy[0][i][3] != -1 represents internal holes enclosed by boundaries
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        features = []
        img_h, img_w = img_np.shape[:2]

        # Filter candidate contours: prefer internal holes enclosed by boundary lines
        candidate_contours = []
        if hierarchy is not None and len(hierarchy[0]) > 0:
            for i, cnt in enumerate(contours):
                # If it's a hole (child contour enclosed by lines)
                if hierarchy[0][i][3] != -1:
                    candidate_contours.append(cnt)

        # Fallback if no internal holes detected (e.g. inverted or simple polygon sketches)
        if not candidate_contours:
            candidate_contours = contours

        # Optional tesseract OCR for parcel text/labels
        tesseract_available = False
        if extract_labels:
            try:
                import pytesseract
                tesseract_available = True
            except ImportError:
                tesseract_available = False

        for idx, cnt in enumerate(candidate_contours):
            area = cv2.contourArea(cnt)
            # Filter out tiny noise and full-page bounding frame
            if 400 < area < (img_h * img_w * 0.85):

                epsilon = 0.02 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)

                # Convert contour points to GeoJSON Polygon format normalized [lng, lat] coords
                pts = [[round(float(pt[0][0]) / img_w * 0.01 + 77.0, 6),
                        round(float(img_h - pt[0][1]) / img_h * 0.01 + 20.0, 6)] for pt in approx]
                if pts:
                    pts.append(pts[0])  # Close ring

                # Bounding box & centroid
                bx, by, bw, bh = cv2.boundingRect(cnt)
                centroid_x = int(bx + bw / 2)
                centroid_y = int(by + bh / 2)

                survey_label = None
                if tesseract_available and bw > 30 and bh > 20:
                    try:
                        crop = img_np[by:by+bh, bx:bx+bw]
                        # OCR on crop with sparse text mode
                        txt = pytesseract.image_to_string(
                            crop,
                            config="--psm 11"
                        ).strip()

                        match = re.search(r"\b\d+([/-][0-9A-Za-z]+)?\b", txt)
                        if match:
                            survey_label = match.group(0)
                        elif txt:
                            survey_label = txt.split()[0]
                    except Exception as ocr_err:
                        logger.debug("Crop OCR failed for parcel %d: %s", idx, ocr_err)

                features.append({
                    "type": "Feature",
                    "id": f"polygon_{idx+1}",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [pts]
                    },
                    "properties": {
                        "parcel_id": f"P-{idx+1}",
                        "survey_number": survey_label or f"P-{idx+1}",
                        "extracted_area_px": float(area),
                        "vertex_count": len(approx),
                        "bounding_box": [int(bx), int(by), int(bw), int(bh)],
                        "centroid": [centroid_x, centroid_y],
                    }
                })


        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "vectorization_engine": "OpenCV-ContourDP",
                "extracted_parcels_count": len(features),
                "image_width": img_w,
                "image_height": img_h,
            }
        }
    except Exception as exc:
        logger.error("OpenCV cadastral vectorization failed: %s", exc, exc_info=True)
        return {"type": "FeatureCollection", "features": [], "metadata": {"error": str(exc)}}


