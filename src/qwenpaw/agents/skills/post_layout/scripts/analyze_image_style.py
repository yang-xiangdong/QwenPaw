from __future__ import annotations

from PIL import Image, ImageDraw

from shared import (
    choose_font_size,
    default_region_for_text_kind,
    dominant_rgb,
    emit_json,
    load_payload,
    mean_brightness,
    parse_region,
    preferred_font_candidates,
)


def main() -> None:
    payload = load_payload()
    image_path = str(payload["image_path"])
    text = str(payload.get("text") or "")
    text_kind = str(payload.get("text_kind") or "title").lower()
    region_value = payload.get("region") or ""
    font_candidates = preferred_font_candidates(
        text_kind,
        str(payload.get("font_candidates") or ""),
    )
    min_font_size = int(payload.get("min_font_size") or 18)
    max_font_size = int(payload.get("max_font_size") or 96)

    with Image.open(image_path) as image:
        image = image.convert("RGB")
        region = (
            parse_region(region_value)
            if region_value
            else default_region_for_text_kind(
                image.width,
                image.height,
                text_kind,
            )
        )
        brightness = mean_brightness(image, region)
        dominant = dominant_rgb(image if region is None else image.crop((
            region["x"],
            region["y"],
            region["x"] + region["width"],
            region["y"] + region["height"],
        )))

        draw = ImageDraw.Draw(image)
        title_max = max_font_size
        body_max = min(max_font_size, 42)
        effective_max = title_max if text_kind == "title" else body_max
        suggested_size, chosen_font, lines, _ = choose_font_size(
            draw=draw,
            text=text or ("示例标题" if text_kind == "title" else "示例正文"),
            region=region,
            font_candidates=font_candidates,
            min_font_size=min_font_size,
            max_font_size=effective_max,
            line_spacing=1.2 if text_kind == "body" else 1.1,
            padding=16,
        )

    text_color = "#000000" if brightness >= 148 else "#FFFFFF"
    emit_json(
        {
            "image_path": image_path,
            "text_kind": text_kind,
            "dominant_rgb": {
                "r": dominant[0],
                "g": dominant[1],
                "b": dominant[2],
            },
            "brightness": round(brightness, 2),
            "recommended_text_color": text_color,
            "recommended_fonts": font_candidates[:5],
            "selected_font_preview": chosen_font,
            "suggested_font_size": suggested_size,
            "estimated_line_count": len(lines),
            "region": region,
        },
    )


if __name__ == "__main__":
    main()
