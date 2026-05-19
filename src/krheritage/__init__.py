from __future__ import annotations

from krheritage.catalog import EndpointCatalogRow, api_catalog
from krheritage.client import AsyncHeritageClient, HeritageClient
from krheritage.config import HeritageConfig
from krheritage.services import EventService, GisService, HeritageDetailService, SearchService

__version__ = "0.1.0"
PROVIDER_NAME = "python-krheritage-api"

__all__ = [
    "PROVIDER_NAME",
    "AsyncHeritageClient",
    "EndpointCatalogRow",
    "EventService",
    "GisService",
    "HeritageClient",
    "HeritageConfig",
    "HeritageDetailService",
    "SearchService",
    "__version__",
    "api_catalog",
]
