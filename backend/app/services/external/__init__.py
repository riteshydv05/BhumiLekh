"""External Service Integration Layer (Optional Escalation)."""

from app.services.external.bhashini_service import BhashiniService
from app.services.external.vlm_provider import VLMProvider, get_vlm_provider
from app.services.external.gemini_service import GeminiProvider
from app.services.external.openai_service import OpenAIProvider
from app.services.external.anthropic_service import AnthropicProvider

__all__ = [
    "BhashiniService",
    "VLMProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "get_vlm_provider",
]
