from __future__ import annotations

import asyncio
from typing import Any

import httpx

from ...exceptions import ProviderError
from ...providers.provider import Provider
from .backend import (
    ImageGenerationBackend,
    ImageGenerationRequest,
    ImageGenerationResult,
)


class MiniMaxImageBackend(ImageGenerationBackend):
    """MiniMax image generation backend."""

    name = "minimax"

    def __init__(self, provider: Provider) -> None:
        super().__init__(provider)
        cfg = provider.meta.get("image_generation", {})
        self._cfg = cfg if isinstance(cfg, dict) else {}

    def _endpoint_url(self) -> str:
        api_base_url = str(self._cfg.get("api_base_url") or "").rstrip("/")
        if not api_base_url:
            raise ProviderError(
                message=(
                    f"Provider '{self.provider.id}' is missing "
                    "image_generation.api_base_url"
                ),
            )
        endpoint = str(
            self._cfg.get("endpoint") or "/v1/image_generation",
        )
        return f"{api_base_url}/{endpoint.lstrip('/')}"

    def _default_model(self) -> str:
        return str(self._cfg.get("default_model") or "image-01")

    async def _wait_until_image_urls_ready(
        self,
        urls: list[str],
    ) -> list[str]:
        """Wait briefly for upstream image URLs to become fetchable."""
        if not urls:
            return urls

        max_attempts = int(self._cfg.get("availability_max_attempts") or 5)
        retry_delay = float(self._cfg.get("availability_retry_delay") or 1.0)
        ready_urls = list(urls)

        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
        ) as client:
            for attempt in range(max_attempts):
                pending: list[str] = []
                for url in ready_urls:
                    try:
                        response = await client.get(
                            url,
                            headers={"Range": "bytes=0-0"},
                        )
                        content_type = response.headers.get(
                            "Content-Type",
                            "",
                        ).lower()
                        if (
                            response.status_code >= 400
                            or not content_type.startswith("image/")
                        ):
                            pending.append(url)
                    except httpx.HTTPError:
                        pending.append(url)
                if not pending:
                    return ready_urls
                if attempt < max_attempts - 1:
                    await asyncio.sleep(retry_delay)
                ready_urls = pending

        return urls

    async def generate(
        self,
        request: ImageGenerationRequest,
    ) -> ImageGenerationResult:
        if not self.provider.api_key:
            raise ProviderError(
                message=(
                    f"Provider '{self.provider.id}' does not have an API key "
                    "configured for image generation."
                ),
            )

        payload: dict[str, Any] = {
            "model": request.model or self._default_model(),
            "prompt": request.prompt,
            "aspect_ratio": request.aspect_ratio,
            "response_format": request.response_format,
            "n": request.n,
            "prompt_optimizer": request.prompt_optimizer,
        }
        if request.size:
            payload["size"] = request.size
        if request.quality:
            payload["quality"] = request.quality
        payload.update(request.extra_params)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._endpoint_url(),
                headers={
                    "Authorization": f"Bearer {self.provider.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        image_urls = data.get("data", {}).get("image_urls", [])
        if not isinstance(image_urls, list):
            image_urls = []
        normalized_urls = [
            str(url) for url in image_urls if isinstance(url, str)
        ]
        ready_urls = await self._wait_until_image_urls_ready(normalized_urls)

        return ImageGenerationResult(
            provider_id=self.provider.id,
            backend_name=self.name,
            model=payload["model"],
            urls=ready_urls,
            revised_prompt=str(
                data.get("data", {}).get("revised_prompt", ""),
            ),
            raw_response=data if isinstance(data, dict) else {},
        )
