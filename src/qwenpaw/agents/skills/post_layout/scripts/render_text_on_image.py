from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from shared import (
    choose_font_size,
    default_region_for_text_kind,
    emit_json,
    load_payload,
    parse_region,
    preferred_font_candidates,
    resolve_font,
)


def main() -> None:
    payload = load_payload()
    image_path = str(payload["image_path"])
    output_path = str(payload["output_path"])
    text = str(payload["text"])
    text_kind = str(payload.get("text_kind") or "body").lower()
    region_value = payload.get("region") or ""
    font_color = str(payload.get("font_color") or "").strip() or "#FFFFFF"
    font_candidates = preferred_font_candidates(
        text_kind,
        str(payload.get("font_candidates") or ""),
    )
    requested_font_size = int(payload.get("font_size") or 0)
    align = str(payload.get("align") or "center").lower()
    line_spacing = float(payload.get("line_spacing") or 1.2)
    padding = int(payload.get("padding") or 16)
    stroke_width = int(payload.get("stroke_width") or 0)
    stroke_fill = str(payload.get("stroke_fill") or "").strip() or None

    with Image.open(image_path) as image:
        image = image.convert("RGBA")
        region = (
            parse_region(region_value)
            if region_value
            else default_region_for_text_kind(
                image.width,
                image.height,
                text_kind,
            )
        )
        draw = ImageDraw.Draw(image)
        max_font_size = 96 if text_kind == "title" else 42
        min_font_size = 18 if text_kind == "title" else 14

        if requested_font_size > 0:
            chosen_size = requested_font_size
            font, chosen_font = resolve_font(font_candidates, chosen_size)
            lines = []
            inner_width = max(1, region["width"] - padding * 2)
            current = ""
            for char in text:
                trial = current + char
                bbox = font.getbbox(trial)
                if bbox[2] - bbox[0] <= inner_width or not current:
                    current = trial
                else:
                    lines.append(current)
                    current = char
            if current:
                lines.append(current)
            if not lines:
                lines = [text]
            line_bbox = draw.textbbox((0, 0), "字", font=font)
            line_height = line_bbox[3] - line_bbox[1]
        else:
            chosen_size, chosen_font, lines, line_height = choose_font_size(
                draw=draw,
                text=text,
                region=region,
                font_candidates=font_candidates,
                min_font_size=min_font_size,
                max_font_size=max_font_size,
                line_spacing=line_spacing,
                padding=padding,
            )
            font, _ = resolve_font(font_candidates, chosen_size)

        total_height = int(
            len(lines) * line_height
            + max(0, len(lines) - 1) * line_height * (line_spacing - 1)
        )
        start_y = region["y"] + max(
            padding,
            (region["height"] - total_height) // 2,
        )

        for index, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line or " ", font=font)
            line_width = bbox[2] - bbox[0]
            if align == "left":
                x = region["x"] + padding
            elif align == "right":
                x = region["x"] + region["width"] - padding - line_width
            else:
                x = region["x"] + (region["width"] - line_width) // 2

            y = int(start_y + index * line_height * line_spacing)
            draw.text(
                (x, y),
                line,
                font=font,
                fill=font_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").save(output)

    emit_json(
        {
            "output_path": str(output),
            "font_used": chosen_font,
            "font_size": chosen_size,
            "line_count": len(lines),
            "font_color": font_color,
            "region": region,
        },
    )


if __name__ == "__main__":
    main()
