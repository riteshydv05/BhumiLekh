"""Bhashini Hosted Translation & Transliteration External Service Adapter.

Purpose:
  Provides optional hosted Indic translation and transliteration via Government of India's Bhashini API.

Key Principles:
  - 100% Optional: System runs offline using local IndicXlit/IndicTrans2 if Bhashini is unconfigured.
  - Fail-Safe: Never crashes document processing pipeline.
  - Privacy/Security: Never logs API keys, sends minimal data required, handles timeouts and rate limits.
  - Integrity: Preserves original OCR text intact and never replaces legal identifiers with translated words.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import mask_secret, settings

logger = logging.getLogger(__name__)


class BhashiniService:
    """Adapter for Bhashini hosted AI translation and transliteration services."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.BHASHINI_API_KEY).strip()
        self.api_url = (api_url if api_url is not None else settings.BHASHINI_API_URL).strip()
        self.enabled = enabled if enabled is not None else settings.ENABLE_BHASHINI
        self.timeout = timeout if timeout is not None else settings.BHASHINI_TIMEOUT

    @property
    def is_configured(self) -> bool:
        """Return True if Bhashini API is explicitly enabled and API key is provided."""
        return bool(self.enabled and self.api_key and self.api_url)

    def _get_headers(self) -> Dict[str, str]:
        """Generate HTTP headers with masked secret protection."""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "BhumiLekh-LandRecordAISystem/1.0",
        }

    def transliterate(
        self,
        text: str,
        source_lang: str = "hi",
        target_lang: str = "en",
    ) -> Dict[str, Any]:
        """Transliterate Indic text to Roman/Latin phonetic representation.
        
        Never raises exceptions — returns status='not_configured', 'success', or 'error'.
        """
        if not text or not text.strip():
            return {"status": "skipped", "original_text": text, "transliteration": "", "source": "bhashini"}

        if not self.is_configured:
            logger.debug("Bhashini service skipped: not configured (enabled=%s, key=%s)", self.enabled, mask_secret(self.api_key))
            return {
                "status": "not_configured",
                "original_text": text,
                "transliteration": None,
                "source": "bhashini",
                "reason": "Bhashini API key or URL not configured",
            }

        logger.info(
            "Calling Bhashini transliteration API (source_lang=%s, key=%s)",
            source_lang,
            mask_secret(self.api_key),
        )

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "transliteration",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang,
                        }
                    },
                }
            ],
            "inputData": {"input": [{"source": text}]},
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.api_url,
                    json=payload,
                    headers=self._get_headers(),
                )

            if response.status_code == 429:
                logger.warning("Bhashini API rate limit exceeded (HTTP 429)")
                return {
                    "status": "rate_limited",
                    "original_text": text,
                    "transliteration": None,
                    "source": "bhashini",
                    "reason": "Rate limit exceeded (HTTP 429)",
                }

            response.raise_for_status()
            data = response.json()

            # Parse Bhashini response structure
            output_text = None
            if "pipelineResponse" in data and len(data["pipelineResponse"]) > 0:
                out_list = data["pipelineResponse"][0].get("output", [])
                if out_list and "target" in out_list[0]:
                    output_text = out_list[0]["target"]

            return {
                "status": "success",
                "original_text": text,
                "transliteration": output_text or text,
                "source": "bhashini",
            }

        except httpx.TimeoutException:
            logger.warning("Bhashini API request timed out (timeout=%.1fs)", self.timeout)
            return {
                "status": "timeout",
                "original_text": text,
                "transliteration": None,
                "source": "bhashini",
                "reason": f"Request timed out after {self.timeout}s",
            }
        except httpx.HTTPStatusError as exc:
            logger.warning("Bhashini API HTTP error %d: %s", exc.response.status_code, exc)
            return {
                "status": "error",
                "original_text": text,
                "transliteration": None,
                "source": "bhashini",
                "reason": f"HTTP {exc.response.status_code} error",
                "error": f"HTTP {exc.response.status_code} error",
            }
        except Exception as exc:
            logger.error("Unexpected Bhashini API error: %s", exc)
            return {
                "status": "error",
                "original_text": text,
                "transliteration": None,
                "source": "bhashini",
                "reason": str(exc),
                "error": str(exc),
            }

    def translate(
        self,
        text: str,
        source_lang: str = "hi",
        target_lang: str = "en",
        is_identifier: bool = False,
    ) -> Dict[str, Any]:
        """Translate Indic domain text into target language (e.g. English).
        
        CRITICAL: Never translate legal names or parcel identifiers!
        """
        if not text or not text.strip():
            return {"status": "skipped", "original_text": text, "translation": None, "source": "bhashini"}

        if is_identifier:
            logger.debug("Skipping Bhashini translation for legal identifier field: %s", text)
            return {
                "status": "skipped_identifier",
                "original_text": text,
                "translation": None,
                "source": "bhashini",
                "reason": "Legal names and parcel identifiers must never be translated",
            }

        if not self.is_configured:
            logger.debug("Bhashini service skipped: not configured")
            return {
                "status": "not_configured",
                "original_text": text,
                "translation": None,
                "source": "bhashini",
                "reason": "Bhashini API key or URL not configured",
            }

        logger.info(
            "Calling Bhashini translation API (source_lang=%s, target_lang=%s, key=%s)",
            source_lang,
            target_lang,
            mask_secret(self.api_key),
        )

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang,
                        }
                    },
                }
            ],
            "inputData": {"input": [{"source": text}]},
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.api_url,
                    json=payload,
                    headers=self._get_headers(),
                )

            if response.status_code == 429:
                logger.warning("Bhashini API rate limit exceeded (HTTP 429)")
                return {
                    "status": "rate_limited",
                    "original_text": text,
                    "translation": None,
                    "source": "bhashini",
                    "reason": "Rate limit exceeded (HTTP 429)",
                }

            response.raise_for_status()
            data = response.json()

            output_text = None
            if "pipelineResponse" in data and len(data["pipelineResponse"]) > 0:
                out_list = data["pipelineResponse"][0].get("output", [])
                if out_list and "target" in out_list[0]:
                    output_text = out_list[0]["target"]

            return {
                "status": "success",
                "original_text": text,
                "translation": output_text or text,
                "source": "bhashini",
            }

        except httpx.TimeoutException:
            logger.warning("Bhashini API request timed out (timeout=%.1fs)", self.timeout)
            return {
                "status": "timeout",
                "original_text": text,
                "translation": None,
                "source": "bhashini",
                "reason": f"Request timed out after {self.timeout}s",
            }
        except httpx.HTTPStatusError as exc:
            logger.warning("Bhashini API HTTP error %d: %s", exc.response.status_code, exc)
            return {
                "status": "error",
                "original_text": text,
                "translation": None,
                "source": "bhashini",
                "reason": f"HTTP {exc.response.status_code} error",
                "error": f"HTTP {exc.response.status_code} error",
            }
        except Exception as exc:
            logger.error("Unexpected Bhashini translation error: %s", exc)
            return {
                "status": "error",
                "original_text": text,
                "translation": None,
                "source": "bhashini",
                "reason": str(exc),
                "error": str(exc),
            }
