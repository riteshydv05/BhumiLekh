"""VLM (Vision-Language Model) Provider Abstraction Interface.

Purpose:
  Decouples the document processing pipeline from specific VLM vendors (Gemini, OpenAI, Anthropic).
  Supports low-confidence handwriting and unreadable region escalation.

Key Principles:
  - Vendor-agnostic interface: Pipeline depends on VLMProvider, not specific API implementations.
  - 100% Optional & Offline-First: If no VLM provider is configured, pipeline gracefully defaults to local OCR.
  - Human Verification: VLM results supplement (never overwrite) original OCR data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.config import settings


class VLMProvider(ABC):
    """Abstract base class for Vision-Language Model external providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifier for the VLM provider (e.g. 'gemini_vlm', 'openai_vlm', 'anthropic_vlm')."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the provider is enabled and has valid API key credentials."""
        pass

    @abstractmethod
    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Analyze a low-confidence document region image.
        
        Must return a dict with schema:
          - status: 'success' | 'not_configured' | 'skipped' | 'timeout' | 'error' | 'rate_limited'
          - text: extracted or interpreted text string
          - confidence: estimated confidence score (0.0 to 1.0)
          - source: provider_name
          - timestamp: ISO 8601 timestamp string
          - metadata: dict of extra provider metadata
        """
        pass


def get_vlm_provider(provider_name: Optional[str] = None) -> VLMProvider:
    """Factory function to get selected VLM provider implementation."""
    name = (provider_name or settings.DEFAULT_VLM_PROVIDER).lower().strip()
    
    if name == "gemini":
        from app.services.external.gemini_service import GeminiProvider
        return GeminiProvider()
    elif name in ("openai", "gpt"):
        from app.services.external.openai_service import OpenAIProvider
        return OpenAIProvider()
    elif name in ("anthropic", "claude"):
        from app.services.external.anthropic_service import AnthropicProvider
        return AnthropicProvider()
    else:
        # Default to GeminiProvider
        from app.services.external.gemini_service import GeminiProvider
        return GeminiProvider()
