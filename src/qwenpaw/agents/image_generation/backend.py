from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ...providers.provider import Provider


@dataclass(slots=True)
class ImageGenerationRequest:
    prompt: str
    aspect_ratio: str = "1:1"
    n: int = 1
    model: str = ""
    response_format: str = "url"
    prompt_optimizer: bool = True
    size: str = ""
    quality: str = ""
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ImageGenerationResult:
    provider_id: str
    backend_name: str
    model: str
    urls: list[str] = field(default_factory=list)
    revised_prompt: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)


class ImageGenerationBackend(ABC):
    """Unified backend interface for image generation providers."""

    name: str = "unknown"

    def __init__(self, provider: Provider) -> None:
        self.provider = provider

    @abstractmethod
    async def generate(
        self,
        request: ImageGenerationRequest,
    ) -> ImageGenerationResult:
        """Generate images for the given request."""
