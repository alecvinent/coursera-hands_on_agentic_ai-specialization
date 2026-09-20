"""Configuration for the secure MCP server.

Every configurable value lives here via pydantic-settings (env prefix MCP_).
Secrets are never hardcoded; tests construct Settings directly.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from mcp_server.models import ApiCredential


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_", env_file=".env", extra="ignore"
    )

    api_keys: dict[str, ApiCredential] = Field(default_factory=dict)
    cache_ttl_seconds: int = Field(default=60, ge=0)
    rate_limit_per_minute: int = Field(default=120, ge=1)
    rate_limit_burst: int = Field(default=20, ge=1)
    tool_timeout_seconds: float = Field(default=10.0, gt=0)
    error_rate_threshold: float = Field(default=0.1, ge=0, le=1)
    mock_failure_mode: str = Field(default="off", pattern=r"^(off|unavailable|slow)$")
    mock_latency_ms: int = Field(default=0, ge=0)
    tls_enabled: bool = False
    tls_cert_path: str = ""
    tls_key_path: str = ""
    seed_customers: int = Field(default=12, ge=1)
    seed_orders: int = Field(default=20, ge=1)
    seed_products: int = Field(default=10, ge=1)
    seed_tickets: int = Field(default=15, ge=1)
    seed: int = 20260918
