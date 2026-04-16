from __future__ import annotations

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
        if request.seed is not None:
            payload["seed"] = request.seed
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

        response_data = data.get("data", {})
        image_urls: list[str] = []
        base64_images: list[str] = []
        if request.response_format == "base64":
            image_base64 = response_data.get("image_base64", [])
            if isinstance(image_base64, list):
                base64_images = [
                    item
                    for item in image_base64
                    if isinstance(item, str) and item
                ]
        else:
            response_urls = response_data.get("image_urls", [])
            if isinstance(response_urls, list):
                image_urls = [
                    str(url) for url in response_urls if isinstance(url, str)
                ]

        return ImageGenerationResult(
            provider_id=self.provider.id,
            backend_name=self.name,
            model=payload["model"],
            urls=image_urls,
            base64_images=base64_images,
            revised_prompt=str(
                response_data.get("revised_prompt", ""),
            ),
            raw_response=data if isinstance(data, dict) else {},
        )
