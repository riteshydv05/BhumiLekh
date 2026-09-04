"""Gemini Vision-Language Model (VLM) Fallback Escalation Provider.

Purpose:
  Provides optional VLM fallback for unreadable/low-confidence document regions using Google Gemini API.

Key Principles:
  - Optional Escalation: Local pipeline (PaddleOCR, TrOCR, LayoutLMv3, IndicNER) remains the primary engine.
  - Invocation Criteria: Gemini is ONLY called when ENABLE_VLM_FALLBACK=True, API key exists, and confidence < VLM_CONFIDENCE_THRESHOLD.
  - Data Minimization: Sends only the relevant low-confidence page/crop region, never full document unnecessarily.
  - Non-Destructive: Results are marked source="gemini_vlm" and NEVER silently overwrite original OCR.
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from app.core.config import mask_secret, settings
from app.services.external.vlm_provider import VLMProvider

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
DEFAULT_PROMPT = "Transcribe the text in this land record document region accurately. Preserve survey numbers, names, dates, and areas."


class GeminiProvider(VLMProvider):
    """Google Gemini VLM Provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        enabled: Optional[bool] = None,
        confidence_threshold: Optional[float] = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.GEMINI_API_KEY).strip()
        self.enabled = enabled if enabled is not None else settings.ENABLE_VLM_FALLBACK
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else settings.VLM_CONFIDENCE_THRESHOLD
        )

    @property
    def provider_name(self) -> str:
        return "gemini_vlm"

    @property
    def is_configured(self) -> bool:
        """Return True if VLM fallback is enabled and Gemini API key is provided."""
        return bool(self.enabled and self.api_key)

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Analyze low-confidence document image region using Gemini VLM API.
        
        Never raises exceptions — returns standardized response dict.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        if not image_bytes:
            return {
                "status": "skipped",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": "Empty image bytes provided",
            }

        if not self.is_configured:
            logger.debug(
                "Gemini VLM provider skipped: not configured (enabled=%s, key=%s)",
                self.enabled,
                mask_secret(self.api_key),
            )
            return {
                "status": "not_configured",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": "Gemini API key not configured or VLM fallback disabled",
            }

        logger.info(
            "Escalating low-confidence region to Gemini VLM API (bytes=%d, key=%s)",
            len(image_bytes),
            mask_secret(self.api_key),
        )

        # Base64 encode image crop
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        query_prompt = prompt or DEFAULT_PROMPT

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": query_prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": encoded_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500,
            },
        }

        # Key is passed in URL query param for Gemini API
        url = f"{GEMINI_API_URL}?key={self.api_key}"

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload)

            if response.status_code == 429:
                logger.warning("Gemini API rate limit exceeded (HTTP 429)")
                return {
                    "status": "rate_limited",
                    "text": "",
                    "confidence": 0.0,
                    "source": self.provider_name,
                    "timestamp": now_iso,
                    "reason": "Gemini API rate limit exceeded (HTTP 429)",
                }

            response.raise_for_status()
            data = response.json()

            # Parse Gemini response candidate text
            extracted_text = ""
            if "candidates" in data and len(data["candidates"]) > 0:
                parts = data["candidates"][0].get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    extracted_text = parts[0]["text"].strip()

            logger.info("Gemini VLM fallback succeeded (text_len=%d)", len(extracted_text))

            return {
                "status": "success",
                "text": extracted_text,
                "confidence": 0.85,  # VLM output confidence
                "source": self.provider_name,
                "timestamp": now_iso,
                "metadata": {
                    "model": "gemini-1.5-flash",
                    "prompt_used": query_prompt,
                },
            }

        except httpx.TimeoutException:
            logger.warning("Gemini VLM request timed out (timeout=%.1fs)", timeout)
            return {
                "status": "timeout",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": f"Request timed out after {timeout}s",
            }
        except httpx.HTTPStatusError as exc:
            logger.warning("Gemini VLM HTTP error %d: %s", exc.response.status_code, exc)
            return {
                "status": "error",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": f"HTTP {exc.response.status_code} error",
            }
        except Exception as exc:
            logger.error("Unexpected Gemini VLM error: %s", exc, exc_info=True)
            return {
                "status": "error",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": str(exc),
            }
