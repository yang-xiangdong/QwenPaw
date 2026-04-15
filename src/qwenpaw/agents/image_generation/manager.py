from __future__ import annotations

from ...exceptions import ProviderError
from ...providers.provider import Provider
from ...providers.provider_manager import ProviderManager
from .backend import ImageGenerationBackend
from .minimax_backend import MiniMaxImageBackend


_BACKEND_REGISTRY: dict[str, type[ImageGenerationBackend]] = {
    "minimax": MiniMaxImageBackend,
}


def _provider_supports_image_generation(provider: Provider | None) -> bool:
    if provider is None:
        return False
    cfg = provider.meta.get("image_generation", {})
    return isinstance(cfg, dict) and bool(cfg.get("enabled"))


def _configured_image_generation_providers(
    manager: ProviderManager,
) -> list[Provider]:
    providers: list[Provider] = []
    for provider in list(manager.builtin_providers.values()) + list(
        manager.custom_providers.values(),
    ):
        if _provider_supports_image_generation(provider):
            providers.append(provider)
    return providers


def resolve_image_generation_backend(
    provider_id: str | None = None,
) -> ImageGenerationBackend:
    manager = ProviderManager.get_instance()

    provider: Provider | None = None
    if provider_id:
        provider = manager.get_provider(provider_id)
    else:
        active_model = manager.get_active_image_model()
        if active_model is None:
            active_model = manager.get_active_model()
        if active_model is not None:
            active_provider = manager.get_provider(active_model.provider_id)
            if _provider_supports_image_generation(active_provider):
                provider = active_provider

        if provider is None:
            configured = _configured_image_generation_providers(manager)
            provider = next((p for p in configured if p.api_key), None)
            if provider is None and configured:
                provider = configured[0]

    if provider is None:
        raise ProviderError(
            message=(
                "No image generation provider is configured. "
                "Configure a provider with image_generation metadata "
                "and an API key first."
            ),
        )

    cfg = provider.meta.get("image_generation", {})
    if not isinstance(cfg, dict) or not cfg.get("enabled"):
        raise ProviderError(
            message=(
                f"Provider '{provider.id}' does not support image generation."
            ),
        )

    backend_name = str(cfg.get("backend") or "").strip().lower()
    if not backend_name:
        raise ProviderError(
            message=(
                f"Provider '{provider.id}' is missing "
                "image_generation.backend configuration."
            ),
        )

    backend_cls = _BACKEND_REGISTRY.get(backend_name)
    if backend_cls is None:
        raise ProviderError(
            message=(
                f"Unsupported image generation backend '{backend_name}' "
                f"for provider '{provider.id}'."
            ),
        )
    return backend_cls(provider)
