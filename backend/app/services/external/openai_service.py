"""OpenAI Vision Provider Adapter (Optional Escalation).

Purpose:
  Provides optional VLM fallback using OpenAI GPT-4o / Vision API.
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

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(VLMProvider):
    """OpenAI Vision VLM Provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.OPENAI_API_KEY).strip()
        self.enabled = enabled if enabled is not None else settings.ENABLE_VLM_FALLBACK

    @property
    def provider_name(self) -> str:
        return "openai_vlm"

    @property
    def is_configured(self) -> bool:
        return bool(self.enabled and self.api_key)

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Analyze document image using OpenAI Vision API."""
        now_iso = datetime.now(timezone.utc).isoformat()

        if not self.is_configured:
            return {
                "status": "not_configured",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": "OpenAI API key not configured or VLM fallback disabled",
            }

        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        query_prompt = prompt or "Transcribe the text in this land record image accurately."

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{encoded_image}"},
                        },
                    ],
                }
            ],
            "max_tokens": 500,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(OPENAI_API_URL, json=payload, headers=headers)

            if response.status_code == 429:
                return {
                    "status": "rate_limited",
                    "text": "",
                    "confidence": 0.0,
                    "source": self.provider_name,
                    "timestamp": now_iso,
                    "reason": "OpenAI API rate limit exceeded (HTTP 429)",
                }

            response.raise_for_status()
            data = response.json()
            extracted_text = data["choices"][0]["message"]["content"].strip()

            return {
                "status": "success",
                "text": extracted_text,
                "confidence": 0.85,
                "source": self.provider_name,
                "timestamp": now_iso,
                "metadata": {"model": "gpt-4o-mini"},
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
            logger.error("OpenAI VLM error: %s", exc)
            return {
                "status": "error",
                "text": "",
                "confidence": 0.0,
                "source": self.provider_name,
                "timestamp": now_iso,
                "reason": str(exc),
            }
