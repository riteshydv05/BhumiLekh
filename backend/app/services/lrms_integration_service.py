"""LRMS / DILRMP Integration Service.

Provides a pluggable adapter architecture for external land record systems.
For the prototype, uses a SyntheticLRMSAdapter that queries local PostGIS data.

Architecture:
  LRMSAdapter (ABC)
    ├── SyntheticLRMSAdapter  → queries land_records_reference (active)
    ├── UPBhumiLRMSAdapter    → (future: UP Bhulekh API)
    ├── DILRMPNationalAdapter → (future: DILRMP national API)
    └── StateCadastralAdapter → (future: State cadastral DB)
"""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class LRMSRecord:
    """A record from any LRMS/DILRMP system."""
    record_id: str
    survey_number: str | None = None
    khasra_number: str | None = None
    khata_number: str | None = None
    plot_number: str | None = None
    owner_name: str | None = None
    father_name: str | None = None
    village: str | None = None
    tehsil: str | None = None
    district: str | None = None
    state: str | None = None
    area: str | None = None
    land_classification: str | None = None
    registration_number: str | None = None
    mutation_number: str | None = None
    lrms_id: str | None = None
    dilrmp_id: str | None = None
    source: str = "unknown"
    has_geometry: bool = False


@dataclass
class LRMSLookupResult:
    """Result of an LRMS lookup."""
    status: str  # MATCHED | NOT_FOUND | ERROR
    record: LRMSRecord | None = None
    source_system: str = "synthetic_prototype"
    match_score: float = 0.0
    matched_fields: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        result = {
            "status": self.status,
            "source_system": self.source_system,
            "match_score": self.match_score,
            "matched_fields": self.matched_fields,
        }
        if self.record:
            result["record"] = {
                "record_id": self.record.record_id,
                "survey_number": self.record.survey_number,
                "khasra_number": self.record.khasra_number,
                "khata_number": self.record.khata_number,
                "plot_number": self.record.plot_number,
                "owner_name": self.record.owner_name,
                "father_name": self.record.father_name,
                "village": self.record.village,
                "tehsil": self.record.tehsil,
                "district": self.record.district,
                "state": self.record.state,
                "area": self.record.area,
                "land_classification": self.record.land_classification,
                "registration_number": self.record.registration_number,
                "mutation_number": self.record.mutation_number,
                "lrms_id": self.record.lrms_id,
                "dilrmp_id": self.record.dilrmp_id,
                "source": self.record.source,
                "has_geometry": self.record.has_geometry,
            }
        if self.error:
            result["error"] = self.error
        return result


# ---------------------------------------------------------------------------
# Abstract adapter
# ---------------------------------------------------------------------------

class LRMSAdapter(ABC):
    """Base adapter for any LRMS/DILRMP/GIS source."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def lookup(self, identifiers: dict[str, str]) -> LRMSLookupResult: ...

    @abstractmethod
    def list_records(self, village: str | None = None, limit: int = 50) -> list[LRMSRecord]: ...


# ---------------------------------------------------------------------------
# Synthetic (Prototype) adapter — queries local PostGIS
# ---------------------------------------------------------------------------

class SyntheticLRMSAdapter(LRMSAdapter):
    """Prototype adapter: queries the local land_records_reference table."""

    @property
    def name(self) -> str:
        return "synthetic_prototype"

    def lookup(self, identifiers: dict[str, str]) -> LRMSLookupResult:
        """Look up a record by any combination of identifiers."""
        from app.models.land_record_reference import LandRecordReference
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            query = db.query(LandRecordReference)
            matched_fields = []

            col_map = {
                "survey_number": LandRecordReference.survey_number,
                "khasra_number": LandRecordReference.khasra_number,
                "khata_number": LandRecordReference.khata_number,
                "plot_number": LandRecordReference.plot_number,
                "registration_number": LandRecordReference.registration_number,
                "village": LandRecordReference.village,
                "district": LandRecordReference.district,
            }

            for key, value in identifiers.items():
                key_lower = key.lower().replace(" ", "_")
                col = col_map.get(key_lower)
                if col is not None and value:
                    query = query.filter(col == value.strip())
                    matched_fields.append(key_lower)

            if not matched_fields:
                return LRMSLookupResult(
                    status="NOT_FOUND",
                    source_system=self.name,
                    error="No valid identifiers provided",
                )

            record = query.first()
            if record is None:
                return LRMSLookupResult(
                    status="NOT_FOUND",
                    source_system=self.name,
                    matched_fields=matched_fields,
                )

            lrms_record = self._to_lrms_record(record)
            score = min(1.0, len(matched_fields) / 3.0)

            return LRMSLookupResult(
                status="MATCHED",
                record=lrms_record,
                source_system=self.name,
                match_score=round(score, 2),
                matched_fields=matched_fields,
            )
        except Exception as exc:
            logger.error("LRMS lookup failed: %s", exc)
            return LRMSLookupResult(status="ERROR", error=str(exc), source_system=self.name)
        finally:
            db.close()

    def list_records(self, village: str | None = None, limit: int = 50) -> list[LRMSRecord]:
        """List all reference records."""
        from app.models.land_record_reference import LandRecordReference
        from app.db.session import SessionLocal
        from sqlalchemy import func

        db = SessionLocal()
        try:
            query = db.query(LandRecordReference)
            if village:
                query = query.filter(func.lower(LandRecordReference.village) == village.lower())
            records = query.limit(limit).all()
            return [self._to_lrms_record(r) for r in records]
        except Exception as exc:
            logger.error("LRMS list failed: %s", exc)
            return []
        finally:
            db.close()

    @staticmethod
    def _to_lrms_record(record) -> LRMSRecord:
        return LRMSRecord(
            record_id=str(record.id),
            survey_number=record.survey_number,
            khasra_number=record.khasra_number,
            khata_number=record.khata_number,
            plot_number=record.plot_number,
            owner_name=record.owner_name,
            father_name=record.father_name,
            village=record.village,
            tehsil=record.tehsil,
            district=record.district,
            state=record.state,
            area=record.area,
            land_classification=record.land_classification,
            registration_number=record.registration_number,
            mutation_number=record.mutation_number,
            lrms_id=record.lrms_id,
            dilrmp_id=record.dilrmp_id,
            source="synthetic_prototype",
            has_geometry=record.parcel_geometry is not None,
        )


# ---------------------------------------------------------------------------
# Future adapter stubs (ready for government API integration)
# ---------------------------------------------------------------------------

# class UPBhumiLRMSAdapter(LRMSAdapter):
#     """Uttar Pradesh Bhulekh/Bhumi LRMS API integration."""
#     @property
#     def name(self) -> str: return "up_bhulekh"
#     def lookup(self, identifiers): raise NotImplementedError("Requires authorized UP Bhulekh API credentials")
#     def list_records(self, village=None, limit=50): raise NotImplementedError

# class DILRMPNationalAdapter(LRMSAdapter):
#     """National DILRMP portal integration."""
#     @property
#     def name(self) -> str: return "dilrmp_national"
#     def lookup(self, identifiers): raise NotImplementedError("Requires authorized DILRMP API access")
#     def list_records(self, village=None, limit=50): raise NotImplementedError


# ---------------------------------------------------------------------------
# Public API — uses the active adapter
# ---------------------------------------------------------------------------

_active_adapter: LRMSAdapter = SyntheticLRMSAdapter()


def get_active_adapter() -> LRMSAdapter:
    """Return the currently active LRMS adapter."""
    return _active_adapter


def lookup_lrms(identifiers: dict[str, str]) -> LRMSLookupResult:
    """Look up a land record in the active LRMS system."""
    logger.info("[LRMS] Lookup: %s", identifiers)
    result = _active_adapter.lookup(identifiers)
    logger.info("[LRMS] Result: status=%s, source=%s", result.status, result.source_system)
    return result


def list_lrms_records(village: str | None = None, limit: int = 50) -> list[dict]:
    """List records from the active LRMS adapter."""
    records = _active_adapter.list_records(village, limit)
    return [
        {
            "record_id": r.record_id,
            "survey_number": r.survey_number,
            "khasra_number": r.khasra_number,
            "khata_number": r.khata_number,
            "owner_name": r.owner_name,
            "village": r.village,
            "district": r.district,
            "state": r.state,
            "lrms_id": r.lrms_id,
            "dilrmp_id": r.dilrmp_id,
            "source": r.source,
            "has_geometry": r.has_geometry,
        }
        for r in records
    ]


def get_integration_status() -> dict:
    """Return integration system status."""
    adapter = get_active_adapter()
    return {
        "active_adapter": adapter.name,
        "available_adapters": [
            {"name": "synthetic_prototype", "status": "active", "description": "Local PostGIS prototype data"},
            {"name": "up_bhulekh", "status": "not_configured", "description": "UP Bhulekh LRMS (requires auth)"},
            {"name": "dilrmp_national", "status": "not_configured", "description": "DILRMP National Portal (requires auth)"},
            {"name": "state_cadastral", "status": "not_configured", "description": "State Cadastral Survey DB (requires auth)"},
        ],
        "postgis_enabled": True,
        "data_source_label": "SYNTHETIC PROTOTYPE DATA — Not connected to government databases",
    }
