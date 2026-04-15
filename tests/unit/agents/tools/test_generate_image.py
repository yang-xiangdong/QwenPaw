from __future__ import annotations

import pytest

import qwenpaw.providers.provider_manager as provider_manager_module
from qwenpaw.agents.tools.generate_image import generate_image
from qwenpaw.providers.models import ModelSlotConfig
from qwenpaw.providers.provider_manager import ProviderManager


@pytest.fixture
def isolated_secret_dir(monkeypatch, tmp_path):
    secret_dir = tmp_path / ".qwenpaw.secret"
    monkeypatch.setattr(provider_manager_module, "SECRET_DIR", secret_dir)
    ProviderManager._instance = None
    try:
        yield secret_dir
    finally:
        ProviderManager._instance = None


async def test_generate_image_uses_active_minimax_provider(
    isolated_secret_dir,
    monkeypatch,
) -> None:
    manager = ProviderManager.get_instance()
    manager.active_model = ModelSlotConfig(
        provider_id="minimax-cn",
        model="MiniMax-M2.5",
    )
    manager.update_provider("minimax-cn", {"api_key": "test-key"})

    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": {
                    "image_urls": [
                        "https://example.com/1.png",
                        "https://example.com/2.png",
                    ],
                },
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(
        "qwenpaw.agents.image_generation.minimax_backend.httpx.AsyncClient",
        lambda timeout=60.0: FakeClient(),
    )

    result = await generate_image(
        prompt="draw a cat",
        aspect_ratio="16:9",
        n=2,
    )

    assert captured["url"] == "https://api.minimaxi.com/v1/image_generation"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["model"] == "image-01"
    assert captured["json"]["prompt"] == "draw a cat"
    assert captured["json"]["aspect_ratio"] == "16:9"
    assert captured["json"]["n"] == 2
    assert len(result.content) == 3
    assert result.content[0].type == "image"
    assert result.content[1].type == "image"
    assert "Generated 2 image(s) via minimax-cn/image-01." in result.content[
        2
    ].text


async def test_generate_image_returns_error_without_api_key(
    isolated_secret_dir,
) -> None:
    ProviderManager.get_instance()

    result = await generate_image(prompt="draw a cat")

    assert len(result.content) == 1
    assert result.content[0].type == "text"
    assert "does not have an API key configured" in result.content[0].text
