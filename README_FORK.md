# QwenPaw Fork Notes

This file records fork-specific features added on top of the upstream project.
The upstream `README.md` stays unchanged. Future custom work for this fork
should be documented here.

## Custom Features

### 2026-04-16: Unified `generate_image` Tool

- Added a new `generate_image` tool for agent-side image creation.
- Introduced a backend abstraction under `src/qwenpaw/agents/image_generation/`.
- Added a MiniMax image-generation backend that calls `/v1/image_generation`.
- Registered MiniMax image generation metadata on built-in providers:
  - `minimax`
  - `minimax-cn`
- Added a dedicated global image-model slot in backend state and frontend settings.
- The Settings -> Models page now exposes a separate "Default Image Model" selector.

### 2026-04-17: `post_layout` Skill And Text-On-Image Tools

- Added a new `post_layout` skill for poster, cover, banner, and text overlay work.
- Added `analyze_image_style` to inspect image brightness and dominant color, then recommend:
  - black/white text color
  - candidate fonts
  - suggested font size for title/body text
- Added `render_text_on_image` to write text into a user-provided image region with Pillow.
- Added bundled scripts under `src/qwenpaw/agents/skills/post_layout/scripts/` so the layout logic stays deterministic and model-free.

## Design Notes

- `supports_multimodal` still means "the chat model can consume image/video input".
- Image generation is treated as a separate capability exposed through a tool.
- New image providers should reuse `generate_image` and implement a new backend,
  instead of creating a provider-specific tool each time.
