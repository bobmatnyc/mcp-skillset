"""LLM service for answering questions using OpenRouter."""

import os
from pathlib import Path

import httpx

from mcp_skills.models.config import LLMConfig


class LLMService:
    """Service for interacting with LLM via OpenRouter API.

    Provides chat completion capabilities for the ask command,
    with support for skill context injection.

    Attributes:
        config: LLM configuration (API key, model, max_tokens)
    """

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, config: LLMConfig):
        """Initialize LLM service.

        Args:
            config: LLM configuration
        """
        self.config = config

    def get_api_key(self) -> str | None:
        """Get API key from config, environment, or .env files.

        Checks in order:
        1. Config object (from config.yaml)
        2. Environment variable (OPENROUTER_API_KEY)
        3. .env.local file
        4. .env file

        Returns:
            API key string or None if not found
        """
        # Check config first
        if self.config.api_key:
            return self.config.api_key

        # Check environment variable
        if key := os.getenv("OPENROUTER_API_KEY"):
            return key

        # Check .env files (project root and user home)
        env_files = [
            Path(".env.local"),
            Path(".env"),
            Path.home() / ".env.local",
            Path.home() / ".env",
        ]

        for env_file in env_files:
            if env_file.exists():
                try:
                    for line in env_file.read_text().splitlines():
                        line = line.strip()
                        if line.startswith("OPENROUTER_API_KEY="):
                            # Strip quotes and whitespace
                            key = line.split("=", 1)[1].strip().strip('"\'')
                            if key:
                                return key
                except Exception:
                    # Ignore file read errors, continue to next file
                    continue

        return None

    def ask(self, question: str, context: str = "") -> str:
        """Ask a question with optional skill context.

        Args:
            question: User question to answer
            context: Optional skill context to include (markdown formatted)

        Returns:
            LLM response as string

        Raises:
            ValueError: If no API key is configured
            httpx.HTTPError: If API request fails
        """
        api_key = self.get_api_key()
        if not api_key:
            raise ValueError(
                "No OpenRouter API key configured. "
                "Set OPENROUTER_API_KEY environment variable or configure via "
                "`mcp-skillset config`"
            )

        # Build system prompt
        system_prompt = """You are a helpful assistant for mcp-skillset, a skill discovery system for AI code assistants.

Answer questions about coding practices, tools, and skills concisely and accurately.
If skill context is provided, use it to give more specific guidance.

Focus on practical, actionable advice. Keep responses clear and well-structured using markdown formatting."""

        # Build message list
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add context if provided
        if context:
            messages.append(
                {
                    "role": "user",
                    "content": f"Here is relevant context from the skill library:\n\n{context}",
                }
            )

        # Add user question
        messages.append({"role": "user", "content": question})

        # Make API request
        try:
            response = httpx.post(
                self.OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://github.com/bobmatnyc/mcp-skillset",
                    "X-Title": "mcp-skillset",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                },
                timeout=30.0,
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            # Better error messages for common HTTP errors
            if e.response.status_code == 401:
                raise ValueError(
                    "Invalid OpenRouter API key. Please check your configuration."
                ) from e
            elif e.response.status_code == 429:
                raise ValueError(
                    "OpenRouter rate limit exceeded. Please try again later."
                ) from e
            else:
                raise ValueError(
                    f"OpenRouter API error ({e.response.status_code}): {e.response.text}"
                ) from e
