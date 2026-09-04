"""Anthropic Claude Vision Provider Adapter (Optional Escalation).

Purpose:
  Provides optional VLM fallback using Anthropic Claude Vision API.
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

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(VLMProvider):
    """Anthropic Claude Vision VLM Provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.ANTHROPIC_API_KEY).strip()
        self.enabled = enabled if enabled is not None else settings.ENABLE_VLM_FALLBACK

    @property
    def provider_name(self) -> str:
        return "anthropic_vlm"

    @property
    def is_configured(self) -> bool:
        return bool(self.enabled and self.api_key)

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Analyze document image using Anthropic Claude Vision API."""
        now_iso = datetime.now(timezone.utc).isoformat()

        if not self.is_configured:
            return {
                "status": "not_configured",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": "Anthropic API key not configured or VLM fallback disabled",
            }

        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        query_prompt = prompt or "Transcribe the text in this land record image accurately."

        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": encoded_image,
                            },
                        },
                        {"type": "text", "text": query_prompt},
                    ],
                }
            ],
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(ANTHROPIC_API_URL, json=payload, headers=headers)

            if response.status_code == 429:
                return {
                    "status": "rate_limited",
                    "text": "",
                    "confidence": 0.0,
                    "source": self.provider_name,
                    "timestamp": now_iso,
                    "reason": "Anthropic API rate limit exceeded (HTTP 429)",
                }

            response.raise_for_status()
            data = response.json()
            extracted_text = data["content"][0]["text"].strip()

            return {
                "status": "success",
                "text": extracted_text,
                "confidence": 0.85,
                "source": self.provider_name,
                "timestamp": now_iso,
                "metadata": {"model": "claude-3-haiku-20240307"},
            }

        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": f"Request timed out after {timeout}s",
            }
        except Exception as exc:
            logger.error("Anthropic VLM error: %s", exc)
            return {
                "status": "error",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": str(exc),
            }
