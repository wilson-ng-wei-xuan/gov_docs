from __future__ import annotations

from functools import lru_cache

from atlas.services import S, ServiceRegistry

__all__ = ["service_registry", "get_service"]


service_registry: ServiceRegistry = ServiceRegistry()
service_registry.import_plugins()


@lru_cache
def get_service(key: str) -> S | None:
    """
    Convenience function to retrieving the service

    Args:
        key (str): Service key

    Returns:
        S | None: Service

    Raises:
        KeyError: If service does not exist
    """
    return service_registry[key]
