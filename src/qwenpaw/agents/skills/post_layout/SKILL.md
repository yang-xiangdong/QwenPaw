---
name: post_layout
description: "Analyze poster/image style and write text into a user-specified image region without calling a vision model. Use this for covers, posters, banners, title cards, and any image text layout task."
metadata:
  builtin_skill_version: "1.0"
  qwenpaw:
    emoji: "🖼️"
    requires: {}
---
# Post Layout

Use this skill when the user wants to place title text, body text, captions, or poster copy onto an existing image.

This skill is rule-based. It does not use a vision model to understand the image. It relies on:

- image brightness and dominant color analysis
- user-provided text
- user-provided writable region
- script-based layout and font-size fitting

## Workflow

1. If the user did not provide a writable region, use the default layout region for the requested text kind.
2. Call `analyze_image_style` first when you need a recommended text color, font list, or estimated font size.
3. Call `render_text_on_image` to write the text into the image.
4. For short text such as titles, prefer larger font sizes.
5. For long text such as body paragraphs, prefer smaller font sizes that still remain readable.

## Region Format

Pass `region` as JSON text:

```json
{"x":120,"y":80,"width":760,"height":280}
```

Coordinates are in pixels from the top-left corner.

If `region` is omitted, the scripts use these defaults:

- Title: height `20%-40%`, width `30%-70%`
- Body: height `30%-70%`, width `20%-80%`

## Practical Rules

- Titles: use `text_kind="title"`
- Body text: use `text_kind="body"`
- If the analysis suggests dark text, use black; if it suggests light text, use white
- If the image has little blank space, keep padding small and prefer tighter fitting
- If the image has more blank space, allow slightly larger padding and line spacing

## Font Candidates

You can pass a comma-separated `font_candidates` string. If omitted, the script uses a built-in fallback list of common fonts.

## Output

- `analyze_image_style` returns JSON text with color, brightness, font candidates, and font-size suggestions.
- `render_text_on_image` returns JSON text with output path, font used, and final font size.
