from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...exceptions import ProviderError
from ...config.context import get_current_workspace_dir
from ...constant import WORKING_DIR
from ..image_generation import (
    ImageGenerationRequest,
    resolve_image_generation_backend,
)


def _output_dir() -> Path:
    workspace_dir = get_current_workspace_dir() or WORKING_DIR
    return Path(workspace_dir) / "generated_images"


def _save_base64_images(base64_images: list[str]) -> list[str]:
    output_dir = _output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_paths: list[str] = []

    for index, item in enumerate(base64_images, start=1):
        image_bytes = base64.b64decode(item)
        path = output_dir / f"generated_{timestamp}_{index}.jpg"
        path.write_bytes(image_bytes)
        saved_paths.append(str(path.resolve()))

    return saved_paths


async def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    n: int = 1,
    model: str = "",
    provider_id: str = "",
    response_format: str = "base64",
    prompt_optimizer: bool = True,
    size: str = "",
    quality: str = "",
    seed: int | None = None,
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
                seed=seed,
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

    saved_paths: list[str] = []
    if result.base64_images:
        saved_paths = _save_base64_images(result.base64_images)
    elif result.urls:
        saved_paths = result.urls

    payload = {
        "provider_id": result.provider_id,
        "model": result.model,
        "saved_paths": saved_paths,
        "image_count": len(saved_paths),
    }
    if result.revised_prompt:
        payload["revised_prompt"] = result.revised_prompt

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=json.dumps(payload, ensure_ascii=False, indent=2),
            ),
        ],
    )
