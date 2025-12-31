"""Unit tests for LLM service."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from mcp_skills.models.config import LLMConfig
from mcp_skills.services.llm_service import LLMService


@pytest.fixture
def llm_config():
    """Create test LLM config."""
    return LLMConfig(
        api_key="test-key",
        model="anthropic/claude-3-haiku",
        max_tokens=1024,
    )


@pytest.fixture
def llm_service(llm_config):
    """Create LLM service instance."""
    return LLMService(llm_config)


class TestLLMService:
    """Test LLM service functionality."""

    def test_init(self, llm_config):
        """Test service initialization."""
        service = LLMService(llm_config)
        assert service.config == llm_config

    def test_get_api_key_from_config(self):
        """Test API key retrieval from config."""
        config = LLMConfig(api_key="config-key")
        service = LLMService(config)
        assert service.get_api_key() == "config-key"

    def test_get_api_key_from_env(self, monkeypatch):
        """Test API key retrieval from environment."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
        config = LLMConfig()  # No API key in config
        service = LLMService(config)
        assert service.get_api_key() == "env-key"

    def test_get_api_key_from_env_file(self, tmp_path, monkeypatch):
        """Test API key retrieval from .env file."""
        # Create test .env file
        env_file = tmp_path / ".env"
        env_file.write_text('OPENROUTER_API_KEY="file-key"\n')

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        config = LLMConfig()  # No API key in config or env
        service = LLMService(config)
        assert service.get_api_key() == "file-key"

    def test_get_api_key_no_key(self, monkeypatch):
        """Test API key retrieval when none configured."""
        # Clear environment
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        config = LLMConfig()  # No API key
        service = LLMService(config)
        assert service.get_api_key() is None

    def test_ask_no_api_key(self):
        """Test ask raises error when no API key."""
        config = LLMConfig()  # No API key
        service = LLMService(config)

        with pytest.raises(ValueError, match="No OpenRouter API key"):
            service.ask("What is pytest?")

    @patch("httpx.post")
    def test_ask_success(self, mock_post, llm_service):
        """Test successful ask request."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Pytest is a testing framework."}}]
        }
        mock_post.return_value = mock_response

        # Ask question
        result = llm_service.ask("What is pytest?")

        # Verify response
        assert result == "Pytest is a testing framework."

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check URL
        assert call_args[0][0] == LLMService.OPENROUTER_URL

        # Check headers
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-key"
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers

        # Check body
        json_data = call_args[1]["json"]
        assert json_data["model"] == "anthropic/claude-3-haiku"
        assert json_data["max_tokens"] == 1024
        assert len(json_data["messages"]) == 2  # system + user
        assert json_data["messages"][1]["content"] == "What is pytest?"

    @patch("httpx.post")
    def test_ask_with_context(self, mock_post, llm_service):
        """Test ask with skill context."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Answer with context."}}]
        }
        mock_post.return_value = mock_response

        # Ask with context
        context = "# Pytest Skill\nPytest is great."
        result = llm_service.ask("What is pytest?", context=context)

        # Verify response
        assert result == "Answer with context."

        # Verify context was included
        json_data = mock_post.call_args[1]["json"]
        assert len(json_data["messages"]) == 3  # system + context + user
        assert context in json_data["messages"][1]["content"]

    @patch("httpx.post")
    def test_ask_http_error_401(self, mock_post, llm_service):
        """Test ask with 401 unauthorized error."""
        # Mock 401 error
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=Mock(), response=mock_response
        )

        # Should raise ValueError with friendly message
        with pytest.raises(ValueError, match="Invalid OpenRouter API key"):
            llm_service.ask("What is pytest?")

    @patch("httpx.post")
    def test_ask_http_error_429(self, mock_post, llm_service):
        """Test ask with 429 rate limit error."""
        # Mock 429 error
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=Mock(), response=mock_response
        )

        # Should raise ValueError with friendly message
        with pytest.raises(ValueError, match="rate limit exceeded"):
            llm_service.ask("What is pytest?")

    @patch("httpx.post")
    def test_ask_http_error_generic(self, mock_post, llm_service):
        """Test ask with generic HTTP error."""
        # Mock 500 error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=Mock(), response=mock_response
        )

        # Should raise ValueError with error details
        with pytest.raises(ValueError, match="OpenRouter API error \\(500\\)"):
            llm_service.ask("What is pytest?")
