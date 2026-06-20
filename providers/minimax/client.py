"""MiniMax (MiniMax) provider using native Anthropic-compatible Messages."""

from __future__ import annotations

from typing import Any

import httpx

from providers.base import ProviderConfig
from providers.defaults import MINIMAX_DEFAULT_BASE
from providers.transports.anthropic_messages import AnthropicMessagesTransport

_ANTHROPIC_VERSION = "2023-06-01"

# MiniMax lists models from the OpenAI-compatible root, not the Anthropic path.
_MINIMAX_OPENAI_MODELS_URL = "https://api.minimax.io/v1/models"


class MiniMaxProvider(AnthropicMessagesTransport):
    """MiniMax using ``https://api.minimax.io/anthropic`` (Anthropic Messages API).

    Supports the MiniMax Token Plan subscription key. See
    https://platform.minimax.io/docs/guides/quickstart for both the
    Anthropic SDK (``ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic``)
    and OpenAI SDK base URLs.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(
            config,
            provider_name="MINIMAX",
            default_base_url=MINIMAX_DEFAULT_BASE,
        )

    def _request_headers(self) -> dict[str, str]:
        return {
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        }

    async def _send_model_list_request(self) -> httpx.Response:
        """Models are listed from the OpenAI-compat root, not ``/anthropic``."""
        return await self._client.get(
            _MINIMAX_OPENAI_MODELS_URL,
            headers=self._model_list_headers(),
        )

    def _model_list_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def _build_request_body(
        self, request: Any, thinking_enabled: bool | None = None
    ) -> dict:
        # Defer to the shared Anthropic Messages request builder; let the
        # base class resolve thinking_enabled from the request if not provided.
        if thinking_enabled is None:
            thinking_enabled = self._is_thinking_enabled(request)
        return super()._build_request_body(request, thinking_enabled=thinking_enabled)
