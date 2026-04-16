from __future__ import annotations

import json
import math
import os
import sys
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "/home/yxd/.local/share/fonts/SmileySans-Oblique.ttf",
    "/home/yxd/.local/share/fonts/LXGWWenKai-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("Empty stdin payload.")
    return json.loads(raw)


def parse_region(region_value: str | dict[str, Any]) -> dict[str, int]:
    if isinstance(region_value, dict):
        data = region_value
    else:
        data = json.loads(region_value)
    x = int(data["x"])
    y = int(data["y"])
    width = int(data["width"])
    height = int(data["height"])
    if width <= 0 or height <= 0:
        raise ValueError("Region width and height must be positive.")
    return {"x": x, "y": y, "width": width, "height": height}


def default_region_for_text_kind(
    image_width: int,
    image_height: int,
    text_kind: str,
) -> dict[str, int]:
    kind = (text_kind or "body").lower()
    if kind == "title":
        left = int(image_width * 0.30)
        right = int(image_width * 0.70)
        top = int(image_height * 0.20)
        bottom = int(image_height * 0.40)
    else:
        left = int(image_width * 0.20)
        right = int(image_width * 0.80)
        top = int(image_height * 0.30)
        bottom = int(image_height * 0.70)

    return {
        "x": left,
        "y": top,
        "width": max(1, right - left),
        "height": max(1, bottom - top),
    }


def split_font_candidates(font_candidates: str) -> list[str]:
    custom = [
        item.strip()
        for item in (font_candidates or "").split(",")
        if item.strip()
    ]
    merged: list[str] = []
    for candidate in custom + DEFAULT_FONT_CANDIDATES:
        if candidate not in merged:
            merged.append(candidate)
    return merged


def preferred_font_candidates(
    text_kind: str,
    font_candidates: str,
) -> list[str]:
    custom = [
        item.strip()
        for item in (font_candidates or "").split(",")
        if item.strip()
    ]
    kind = (text_kind or "body").lower()
    if kind == "title":
        preferred = [
            "/home/yxd/.local/share/fonts/SmileySans-Oblique.ttf",
            "/home/yxd/.local/share/fonts/LXGWWenKai-Regular.ttf",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
        ]
    else:
        preferred = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "/home/yxd/.local/share/fonts/LXGWWenKai-Regular.ttf",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/home/yxd/.local/share/fonts/SmileySans-Oblique.ttf",
        ]

    merged: list[str] = []
    for candidate in custom + preferred + DEFAULT_FONT_CANDIDATES:
        if candidate not in merged:
            merged.append(candidate)
    return merged


def resolve_font(font_candidates: list[str], font_size: int) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, str]:
    for candidate in font_candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), font_size), str(path)
            except OSError:
                continue
    return ImageFont.load_default(), "PIL_default"


def wrap_text_to_width(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            trial = current + char
            bbox = font.getbbox(trial)
            width = bbox[2] - bbox[0]
            if width <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines or [text]


def measure_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    line_spacing: float,
) -> tuple[int, int, int]:
    max_width = 0
    total_height = 0
    line_height = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line or " ", font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        max_width = max(max_width, width)
        line_height = max(line_height, height)
    if lines:
        total_height = int(len(lines) * line_height + max(0, len(lines) - 1) * line_height * (line_spacing - 1))
    return max_width, total_height, line_height


def choose_font_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    region: dict[str, int],
    font_candidates: list[str],
    min_font_size: int,
    max_font_size: int,
    line_spacing: float,
    padding: int,
) -> tuple[int, str, list[str], int]:
    inner_width = max(1, region["width"] - padding * 2)
    inner_height = max(1, region["height"] - padding * 2)
    best_size = min_font_size
    best_font_path = "PIL_default"
    best_lines = [text]
    best_line_height = 0

    for font_size in range(max_font_size, min_font_size - 1, -1):
        font, font_path = resolve_font(font_candidates, font_size)
        lines = wrap_text_to_width(text, font, inner_width)
        width, height, line_height = measure_block(
            draw,
            lines,
            font,
            line_spacing,
        )
        if width <= inner_width and height <= inner_height:
            return font_size, font_path, lines, line_height
        best_size = font_size
        best_font_path = font_path
        best_lines = lines
        best_line_height = line_height

    return best_size, best_font_path, best_lines, best_line_height


def mean_brightness(image: Image.Image, region: dict[str, int] | None = None) -> float:
    target = image
    if region is not None:
        box = (
            region["x"],
            region["y"],
            region["x"] + region["width"],
            region["y"] + region["height"],
        )
        target = image.crop(box)
    grayscale = target.convert("L")
    hist = grayscale.histogram()
    total = sum(hist)
    if total == 0:
        return 255.0
    return sum(value * count for value, count in enumerate(hist)) / total


def dominant_rgb(image: Image.Image) -> tuple[int, int, int]:
    thumb = image.convert("RGB").resize((64, 64))
    colors = thumb.getcolors(64 * 64) or []
    if not colors:
        return (255, 255, 255)
    _, rgb = max(colors, key=lambda item: item[0])
    return rgb


def emit_json(data: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2))
