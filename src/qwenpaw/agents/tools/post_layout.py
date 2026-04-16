# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


def _skill_scripts_dir() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "skills"
        / "post_layout"
        / "scripts"
    )


def _run_script(script_name: str, payload: dict[str, Any]) -> ToolResponse:
    script_path = _skill_scripts_dir() / script_name
    if not script_path.exists():
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: script not found: {script_path}",
                ),
            ],
        )

    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:  # pylint: disable=broad-except
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: failed to execute {script_name}: {exc}",
                ),
            ],
        )

    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip()
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: {script_name} failed: {stderr}",
                ),
            ],
        )

    return ToolResponse(
        content=[TextBlock(type="text", text=proc.stdout.strip())],
    )


async def analyze_image_style(
    image_path: str,
    text: str = "",
    text_kind: str = "title",
    region: str = "",
    font_candidates: str = "",
    min_font_size: int = 18,
    max_font_size: int = 96,
) -> ToolResponse:
    """Analyze an image and suggest font color, font list, and font size.

    This tool does not use a vision model. It inspects image brightness and
    color distribution, then returns a JSON object with a black/white text
    recommendation, candidate fonts, and a suggested size range for the given
    text and region.
    """

    return _run_script(
        "analyze_image_style.py",
        {
            "image_path": image_path,
            "text": text,
            "text_kind": text_kind,
            "region": region,
            "font_candidates": font_candidates,
            "min_font_size": min_font_size,
            "max_font_size": max_font_size,
        },
    )


async def render_text_on_image(
    image_path: str,
    output_path: str,
    text: str,
    region: str,
    font_color: str = "",
    font_candidates: str = "",
    font_size: int = 0,
    text_kind: str = "body",
    align: str = "center",
    line_spacing: float = 1.2,
    padding: int = 16,
    stroke_width: int = 0,
    stroke_fill: str = "",
) -> ToolResponse:
    """Render the given text into the specified image region.

    `region` should be a JSON string such as
    `{"x":120,"y":80,"width":760,"height":280}`.
    If `font_size` is 0, the script auto-fits the text to the region.
    """

    return _run_script(
        "render_text_on_image.py",
        {
            "image_path": image_path,
            "output_path": output_path,
            "text": text,
            "region": region,
            "font_color": font_color,
            "font_candidates": font_candidates,
            "font_size": font_size,
            "text_kind": text_kind,
            "align": align,
            "line_spacing": line_spacing,
            "padding": padding,
            "stroke_width": stroke_width,
            "stroke_fill": stroke_fill,
        },
    )
