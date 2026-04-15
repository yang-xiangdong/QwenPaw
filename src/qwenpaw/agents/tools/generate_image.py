from __future__ import annotations

from agentscope.message import ImageBlock, TextBlock
from agentscope.tool import ToolResponse

from ...exceptions import ProviderError
from ..image_generation import (
    ImageGenerationRequest,
    resolve_image_generation_backend,
)


async def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    n: int = 1,
    model: str = "",
    provider_id: str = "",
    response_format: str = "url",
    prompt_optimizer: bool = True,
    size: str = "",
    quality: str = "",
) -> ToolResponse:
    """Generate images with the configured image backend.

    Use this when the user explicitly asks to create an image, poster,
    illustration, avatar, cover, or visual concept. By default the tool
    uses the active provider if it exposes an image-generation backend;
    otherwise it falls back to the first configured image provider.
    """
    if not prompt.strip():
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: prompt must not be empty.",
                ),
            ],
        )

    try:
        backend = resolve_image_generation_backend(
            provider_id=provider_id or None,
        )
        result = await backend.generate(
            ImageGenerationRequest(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                n=n,
                model=model,
                response_format=response_format,
                prompt_optimizer=prompt_optimizer,
                size=size,
                quality=quality,
            ),
        )
    except ProviderError as exc:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Error: {exc}")],
        )
    except Exception as exc:  # pylint: disable=broad-except
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: image generation failed: {exc}",
                ),
            ],
        )

    content = []
    for url in result.urls:
        content.append(
            ImageBlock(
                type="image",
                source={"type": "url", "url": url},
            ),
        )

    summary = (
        f"Generated {len(result.urls)} image(s) via "
        f"{result.provider_id}/{result.model}."
    )
    if result.revised_prompt:
        summary += f"\nRevised prompt: {result.revised_prompt}"
    content.append(TextBlock(type="text", text=summary))
    return ToolResponse(content=content)
