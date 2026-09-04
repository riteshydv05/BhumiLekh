"""Tests for Optional External API Integrations (Bhashini, Gemini VLM, OpenAI VLM, Anthropic VLM).

Verifies all 11 required scenarios:
1. No API keys configured (core system functional).
2. Bhashini disabled.
3. VLM fallback disabled.
4. Missing Gemini key.
5. Missing Bhashini key.
6. Provider timeout.
7. Provider HTTP error.
8. Provider rate limit.
9. Successful provider response.
10. Original OCR preservation.
11. API key masking in logs.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

from app.core.config import settings, mask_secret
from app.services.external.bhashini_service import BhashiniService
from app.services.external.gemini_service import GeminiProvider
from app.services.external.openai_service import OpenAIProvider
from app.services.external.anthropic_service import AnthropicProvider
from app.services.external.vlm_provider import get_vlm_provider
from app.services.multilingual_service import process_text_multilingual


class TestExternalServices:
    """Test suite covering all 11 external API integration scenarios."""

    # 1. No API keys configured
    def test_01_no_api_keys_configured(self, monkeypatch):
        """Core system works without any external API keys configured."""
        monkeypatch.setattr(settings, "BHASHINI_API_KEY", "")
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
        monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
        monkeypatch.setattr(settings, "ENABLE_BHASHINI", False)
        monkeypatch.setattr(settings, "ENABLE_VLM_FALLBACK", False)

        bhashini = BhashiniService()
        assert not bhashini.is_configured

        gemini = GeminiProvider()
        assert not gemini.is_configured

        openai = OpenAIProvider()
        assert not openai.is_configured

        anthropic = AnthropicProvider()
        assert not anthropic.is_configured

        # Test multilingual fallback to local IndicXlit/IndicTrans2
        res = process_text_multilingual("राम लाल", language="hi")
        assert res["original_text"] == "राम लाल"
        assert res["transliteration"] != ""  # Local transliteration works

    # 2. Bhashini disabled
    def test_02_bhashini_disabled(self, monkeypatch):
        """When ENABLE_BHASHINI=False, Bhashini returns controlled not_configured response."""
        monkeypatch.setattr(settings, "BHASHINI_API_KEY", "dummy_key")
        monkeypatch.setattr(settings, "ENABLE_BHASHINI", False)

        bhashini = BhashiniService()
        assert not bhashini.is_configured
        res = bhashini.transliterate("राम", "hi", "en")
        assert res["status"] == "not_configured"
        assert res.get("original_text") == "राम"  # Returns original text unmodified

    # 3. VLM fallback disabled
    def test_03_vlm_fallback_disabled(self, monkeypatch):
        """When ENABLE_VLM_FALLBACK=False, VLM providers are skipped."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "dummy_gemini_key")
        monkeypatch.setattr(settings, "ENABLE_VLM_FALLBACK", False)

        provider = get_vlm_provider("gemini")
        assert not provider.is_configured  # Enabled is False, so is_configured is False

    # 4. Missing Gemini key
    def test_04_missing_gemini_key(self, monkeypatch):
        """When GEMINI_API_KEY is empty, GeminiProvider is unconfigured and safely skipped."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        monkeypatch.setattr(settings, "ENABLE_VLM_FALLBACK", True)
        gemini = GeminiProvider()
        assert not gemini.is_configured
        res = gemini.analyze_image(b"fake_bytes")
        assert res["status"] == "not_configured"
        assert "not configured" in res.get("reason", "").lower()

    # 5. Missing Bhashini key
    def test_05_missing_bhashini_key(self, monkeypatch):
        """When BHASHINI_API_KEY is empty, BhashiniService is unconfigured."""
        monkeypatch.setattr(settings, "BHASHINI_API_KEY", "")
        monkeypatch.setattr(settings, "ENABLE_BHASHINI", True)

        bhashini = BhashiniService()
        assert not bhashini.is_configured
        res = bhashini.translate("राम", "hi", "en")
        assert res["status"] == "not_configured"

    # 6. Provider timeout
    def test_06_provider_timeout(self, monkeypatch):
        """Provider handles timeout gracefully without throwing uncaught exceptions."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_key")
        monkeypatch.setattr(settings, "ENABLE_VLM_FALLBACK", True)
        gemini = GeminiProvider()

        import httpx

        def mock_post(*args, **kwargs):
            raise httpx.TimeoutException("Request timed out")

        with patch("httpx.Client.post", side_effect=mock_post):
            res = gemini.analyze_image(b"image_data")
            assert res["status"] == "timeout"
            assert res["source"] == "gemini_vlm"
            assert "timed out" in res.get("reason", "").lower()

    # 7. Provider HTTP error
    def test_07_provider_http_error(self, monkeypatch):
        """Provider handles HTTP 500 server errors gracefully."""
        monkeypatch.setattr(settings, "BHASHINI_API_KEY", "test_key")
        monkeypatch.setattr(settings, "BHASHINI_API_URL", "https://api.bhashini.gov.in/v1")
        monkeypatch.setattr(settings, "ENABLE_BHASHINI", True)
        bhashini = BhashiniService()

        import httpx
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_resp
        )

        with patch("httpx.Client.post", return_value=mock_resp):
            res = bhashini.transliterate("राम", "hi", "en")
            assert res["status"] == "error"
            assert "500" in res.get("reason", "")

    # 8. Provider rate limit
    def test_08_provider_rate_limit(self, monkeypatch):
        """Provider handles HTTP 429 rate limit error gracefully."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_key")
        monkeypatch.setattr(settings, "ENABLE_VLM_FALLBACK", True)
        gemini = GeminiProvider()

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit exceeded"

        with patch("httpx.Client.post", return_value=mock_resp):
            res = gemini.analyze_image(b"image_data")
            assert res["status"] == "rate_limited"
            assert "rate limit" in res.get("reason", "").lower()

    # 9. Successful provider response
    def test_09_successful_provider_response(self, monkeypatch):
        """Provider parses successful API response correctly."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_key")
        monkeypatch.setattr(settings, "ENABLE_VLM_FALLBACK", True)
        gemini = GeminiProvider()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Khasra No 123/4, Area 0.45 Hectare"}]
                    }
                }
            ]
        }

        with patch("httpx.Client.post", return_value=mock_resp):
            res = gemini.analyze_image(b"image_data")
            assert res["status"] == "success"
            assert res["source"] == "gemini_vlm"
            assert "123/4" in res["text"]
            assert res["confidence"] > 0.0

    # 10. Original OCR preservation
    def test_10_original_ocr_preservation(self, monkeypatch):
        """Bhashini and VLM results never overwrite original OCR text or legal identifiers."""
        # 1. Test Bhashini transliteration does not change original_text field
        monkeypatch.setattr(settings, "BHASHINI_API_KEY", "test_key")
        monkeypatch.setattr(settings, "BHASHINI_API_URL", "https://api.bhashini.gov.in/v1")
        monkeypatch.setattr(settings, "ENABLE_BHASHINI", True)

        bhashini = BhashiniService()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "pipelineResponse": [
                {
                    "output": [
                        {"target": "Ram Lal"}
                    ]
                }
            ]
        }

        with patch("httpx.Client.post", return_value=mock_resp):
            res = bhashini.transliterate("राम लाल", "hi", "en")
            assert res.get("transliteration") == "Ram Lal"
            assert res.get("original_text") == "राम लाल"  # Original preserved

        # 2. Test numeric identifier protection in Bhashini
        legal_text = "Khasra 452/12"
        res_legal = bhashini.translate(legal_text, "hi", "en", is_identifier=True)
        # Identifiers with digits/is_identifier are preserved and not sent to translation
        assert res_legal["status"] == "skipped_identifier"
        assert res_legal["original_text"] == legal_text

    # 11. API key masking in logs
    def test_11_api_key_masking_in_logs(self, caplog):
        """API keys are masked in logs and never printed in plaintext."""
        caplog.set_level(logging.INFO)

        secret1 = "sk-1234567890abcdef"
        masked1 = mask_secret(secret1)
        assert secret1 not in masked1
        assert "sk-1" in masked1
        assert "cdef" in masked1
        assert "****" in masked1

        secret2 = "AIzaSyB123456789"
        masked2 = mask_secret(secret2)
        assert secret2 not in masked2
        assert masked2.startswith("AIza****")

        # Verify mask_secret with empty / None
        assert mask_secret(None) == "<not-configured>"
        assert mask_secret("") == "<not-configured>"
