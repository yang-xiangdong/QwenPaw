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

## Design Notes

- `supports_multimodal` still means "the chat model can consume image/video input".
- Image generation is treated as a separate capability exposed through a tool.
- New image providers should reuse `generate_image` and implement a new backend,
  instead of creating a provider-specific tool each time.
