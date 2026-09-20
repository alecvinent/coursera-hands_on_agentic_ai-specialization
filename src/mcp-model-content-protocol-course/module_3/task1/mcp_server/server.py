"""MCP server assembly: resources + tools bound to one credential.

Single-client binding keeps authentication explicit and auditable: the
server is built for exactly one API key (STDIO local use), while HTTP
deployments sit behind ingress that selects the key per deployment.
Production multi-tenant use should adopt MCP OAuth Authorization.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time

from loguru import logger
from mcp.server.mcpserver import MCPServer

from mcp_server.audit import AuditLog
from mcp_server.auth import (
    AuthContext,
    Forbidden,
    Unauthenticated,
    authenticate,
    require,
)
from mcp_server.cache import TTLCache
from mcp_server.config import Settings
from mcp_server.metrics import MetricsRegistry
from mcp_server.ops_app import OpsDeps
from mcp_server.ratelimit import RateLimiter
from mcp_server.resilience import CircuitBreaker
from mcp_server.resources import ResourceService
from mcp_server.store import MockStore
from mcp_server.tools import TOOL_ROLES, ToolService


class ServerDeps:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = MockStore(settings)
        self.cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)
        self.audit = AuditLog()
        self.metrics = MetricsRegistry()
        self.limiter = RateLimiter(
            per_minute=settings.rate_limit_per_minute, burst=settings.rate_limit_burst
        )
        self.breaker = CircuitBreaker()
        self.resources = ResourceService(
            settings,
            settings.api_keys,
            self.store,
            self.cache,
            self.audit,
            self.metrics,
            self.limiter,
            self.breaker,
        )
        self.tools = ToolService(
            settings,
            settings.api_keys,
            self.store,
            self.audit,
            self.metrics,
            self.limiter,
        )

    def ops_deps(self) -> OpsDeps:
        return OpsDeps(
            settings=self.settings,
            credentials=self.settings.api_keys,
            store=self.store,
            audit=self.audit,
            metrics=self.metrics,
            breaker=self.breaker,
            started_at=time.monotonic(),
        )


def build_server(
    settings: Settings, api_key: str, deps: ServerDeps | None = None
) -> MCPServer:
    ctx: AuthContext = authenticate(settings.api_keys, api_key)
    deps = deps or ServerDeps(settings)
    mcp = MCPServer("secure-store")
    logger.info(f"building MCP server for key_id={ctx.key_id} role={ctx.role.value}")

    @mcp.resource("store://customers/{customer_id}", mime_type="application/json")
    async def customer_profile(customer_id: str) -> dict:
        return await deps.resources.read(f"store://customers/{customer_id}", api_key)

    @mcp.resource(
        "store://customers/{customer_id}/orders", mime_type="application/json"
    )
    async def customer_orders(customer_id: str) -> dict:
        return await deps.resources.read(
            f"store://customers/{customer_id}/orders", api_key
        )

    @mcp.resource(
        "store://customers/{customer_id}/tickets", mime_type="application/json"
    )
    async def customer_tickets(customer_id: str) -> dict:
        return await deps.resources.read(
            f"store://customers/{customer_id}/tickets", api_key
        )

    @mcp.resource("store://orders/{order_id}", mime_type="application/json")
    async def order_detail(order_id: str) -> dict:
        return await deps.resources.read(f"store://orders/{order_id}", api_key)

    @mcp.resource("store://orders/status/{status}", mime_type="application/json")
    async def orders_by_status(status: str) -> dict:
        return await deps.resources.read(f"store://orders/status/{status}", api_key)

    @mcp.resource("store://tickets/{ticket_id}", mime_type="application/json")
    async def ticket_detail(ticket_id: str) -> dict:
        return await deps.resources.read(f"store://tickets/{ticket_id}", api_key)

    @mcp.resource("store://tickets/status/{status}", mime_type="application/json")
    async def tickets_by_status(status: str) -> dict:
        return await deps.resources.read(f"store://tickets/status/{status}", api_key)

    @mcp.resource("store://products", mime_type="application/json")
    async def product_catalog() -> dict:
        return await deps.resources.read("store://products", api_key)

    @mcp.resource("store://products/{product_id}", mime_type="application/json")
    async def product_detail(product_id: str) -> dict:
        return await deps.resources.read(f"store://products/{product_id}", api_key)

    @mcp.tool()
    async def create_ticket(
        customer_id: str, subject: str, description: str, order_id: str | None = None
    ) -> dict:
        return await deps.tools.create_ticket(
            api_key,
            {
                "customer_id": customer_id,
                "subject": subject,
                "description": description,
                "order_id": order_id,
            },
        )

    @mcp.tool()
    async def update_order(
        order_id: str,
        new_status: str,
        reason: str = "",
        expected_version: int | None = None,
    ) -> dict:
        return await deps.tools.update_order(
            api_key,
            {
                "order_id": order_id,
                "new_status": new_status,
                "reason": reason,
                "expected_version": expected_version,
            },
        )

    @mcp.tool()
    async def update_ticket_status(
        ticket_id: str,
        new_status: str,
        note: str = "",
        expected_version: int | None = None,
    ) -> dict:
        return await deps.tools.update_ticket_status(
            api_key,
            {
                "ticket_id": ticket_id,
                "new_status": new_status,
                "note": note,
                "expected_version": expected_version,
            },
        )

    @mcp.tool()
    async def get_task_status(task_id: str) -> dict:
        try:
            ctx_tools = authenticate(settings.api_keys, api_key)
            require(ctx_tools, TOOL_ROLES)
        except (Unauthenticated, Forbidden):
            return {
                "error": {"code": "FORBIDDEN", "message": "insufficient permissions"}
            }
        return deps.tools.get_task(task_id)

    return mcp


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Secure MCP server with monitoring")
    parser.add_argument("--transport", choices=("stdio", "http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--ops-port", type=int, default=8001)
    parser.add_argument("--no-ops", action="store_true")
    parser.add_argument("--api-key", default=os.environ.get("MCP_SERVER_API_KEY", ""))
    args = parser.parse_args(argv)
    settings = Settings()
    deps = ServerDeps(settings)
    server = build_server(settings, args.api_key, deps)
    if args.transport == "stdio":
        asyncio.run(server.run_stdio_async())
    else:
        import threading

        from mcp_server.ops_app import create_ops_app

        if not args.no_ops:
            import uvicorn

            ops_app = create_ops_app(deps.ops_deps())
            thread = threading.Thread(
                target=uvicorn.run,
                kwargs={"app": ops_app, "host": args.host, "port": args.ops_port},
                daemon=True,
            )
            thread.start()
            logger.info(f"ops sidecar on {args.host}:{args.ops_port}")
        asyncio.run(server.run_streamable_http_async(host=args.host, port=args.port))


if __name__ == "__main__":
    main()
