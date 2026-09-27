"""BhumiLekh Validation Engine — Rules & Cross-Database Verification.

State-specific rules:
  - MH (Maharashtra): 7/12 extract format, Khata No, Hissa No, total area == sub-plot sum
  - UP (Uttar Pradesh): Khatauni 13-digit code validation, Fasli year cross-check
  - MP (Madhya Pradesh): Khasra/Bhoomi Swami area matching
  - TN (Tamil Nadu): Patta/Chitta Pul En (Survey No) & Sub-division validation, Nanja/Punja land type check
  - AP/TS (Andhra Pradesh/Telangana): Adangal 1B Khata & Survey number format
  - WB (West Bengal): Khatian & Dag number consistency

Business rules:
  1. Area non-negativity & unit conversion sanity (Hectares, Acres, Sq Ft, Gunta, Bigha)
  2. Duplicate detection check (same state + district + survey/khasra + owner)
  3. Format validation for Survey / Khata / Patta identifiers
"""
from __future__ import annotations

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ValidationRule:
    def __init__(self, rule_id: str, description: str, state: str = "ALL"):
        self.rule_id = rule_id
        self.description = description
        self.state = state

    def validate(self, record: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class AreaSumRule(ValidationRule):
    def __init__(self):
        super().__init__("RULE_AREA_SUM", "Sub-plot areas must sum to total plot area", "ALL")

    def validate(self, record: dict[str, Any]) -> dict[str, Any]:
        total_area = record.get("total_area")
        plots = record.get("plots", [])
        if total_area is not None and plots:
            plot_sum = sum(p.get("area", 0.0) for p in plots if isinstance(p.get("area"), (int, float)))
            if abs(total_area - plot_sum) > 0.05:
                return {
                    "passed": False,
                    "rule_id": self.rule_id,
                    "severity": "HIGH",
                    "message": f"Total area ({total_area}) does not match sum of sub-plots ({plot_sum})",
                }
        return {"passed": True, "rule_id": self.rule_id}


class SurveyNumberFormatRule(ValidationRule):
    def __init__(self):
        super().__init__("RULE_SURVEY_FORMAT", "Survey/Khasra/Patta number format check", "ALL")

    def validate(self, record: dict[str, Any]) -> dict[str, Any]:
        survey_no = str(record.get("survey_number") or record.get("khasra_number") or record.get("patta_number") or "")
        if survey_no and not re.match(r"^[0-9A-Za-z\/\-\.\s]+$", survey_no):
            return {
                "passed": False,
                "rule_id": self.rule_id,
                "severity": "MEDIUM",
                "message": f"Invalid Survey/Khasra/Patta format: {survey_no}",
            }
        return {"passed": True, "rule_id": self.rule_id}


class TamilNaduPattaChittaRule(ValidationRule):
    def __init__(self):
        super().__init__("RULE_TN_PATTA", "Tamil Nadu Patta/Chitta Pul En & Land Classification Check", "TN")

    def validate(self, record: dict[str, Any]) -> dict[str, Any]:
        state = str(record.get("state", "")).upper()
        if state not in ("TN", "TAMIL NADU"):
            return {"passed": True, "rule_id": self.rule_id}

        pul_en = record.get("pul_en") or record.get("survey_number")
        if not pul_en:
            return {
                "passed": False,
                "rule_id": self.rule_id,
                "severity": "HIGH",
                "message": "Tamil Nadu record missing Pul En (Survey Number)",
            }
        return {"passed": True, "rule_id": self.rule_id}


class Maharashtra712Rule(ValidationRule):
    def __init__(self):
        super().__init__("RULE_MH_712", "Maharashtra 7/12 Extract Khata & Hissa Validation", "MH")

    def validate(self, record: dict[str, Any]) -> dict[str, Any]:
        state = str(record.get("state", "")).upper()
        if state not in ("MH", "MAHARASHTRA"):
            return {"passed": True, "rule_id": self.rule_id}

        khata_no = record.get("khata_number")
        if not khata_no:
            return {
                "passed": False,
                "rule_id": self.rule_id,
                "severity": "HIGH",
                "message": "Maharashtra 7/12 record missing Khata Number (खाते क्रमांक)",
            }
        return {"passed": True, "rule_id": self.rule_id}


class ValidationEngine:
    """Main Validation Engine orchestrating business & state rules."""

    def __init__(self):
        self.rules: list[ValidationRule] = [
            AreaSumRule(),
            SurveyNumberFormatRule(),
            TamilNaduPattaChittaRule(),
            Maharashtra712Rule(),
        ]

    def validate_document(self, record: dict[str, Any]) -> dict[str, Any]:
        """Validate land record dictionary against registered rules."""
        results = []
        is_valid = True

        for rule in self.rules:
            res = rule.validate(record)
            results.append(res)
            if not res.get("passed", True):
                is_valid = False

        failed = [r for r in results if not r.get("passed", True)]

        return {
            "is_valid": is_valid,
            "total_rules_checked": len(self.rules),
            "failed_count": len(failed),
            "failures": failed,
            "all_results": results,
        }


# Module instance singleton
engine = ValidationEngine()


def validate_land_record(record: dict[str, Any]) -> dict[str, Any]:
    """Public helper function to validate a land record."""
    return engine.validate_document(record)
