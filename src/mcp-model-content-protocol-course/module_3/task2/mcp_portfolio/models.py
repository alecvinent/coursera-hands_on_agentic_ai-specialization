"""Domain entities for the MCP Enterprise Integration Portfolio."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field, field_validator, model_validator


class Role(str, Enum):
    ADMIN = "admin"
    SUPPORT_AGENT = "support_agent"
    AUDITOR = "auditor"
    OPERATOR = "operator"


class CustomerTier(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Outcome(str, Enum):
    SUCCESS = "success"
    DENIED = "denied"
    FAILED = "failed"


ORDER_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}

TICKET_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.IN_PROGRESS: {TicketStatus.RESOLVED, TicketStatus.CLOSED},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED},
    TicketStatus.CLOSED: set(),
}

MASKED = "***"

RESOURCE_ROLES_READ: set[Role] = {Role.ADMIN, Role.SUPPORT_AGENT, Role.AUDITOR}
INVENTORY_ROLES_READ: set[Role] = {Role.ADMIN, Role.SUPPORT_AGENT, Role.OPERATOR}
LOW_STOCK_ROLES: set[Role] = {Role.ADMIN, Role.OPERATOR}
TOOL_ROLES: set[Role] = {Role.ADMIN, Role.SUPPORT_AGENT}
INVENTORY_TOOL_ROLES: set[Role] = {Role.ADMIN, Role.OPERATOR}
OPERATOR_ROLES: set[Role] = {Role.ADMIN, Role.OPERATOR}


class Customer(BaseModel):
    customer_id: str = Field(pattern=r"^cust_[0-9]{4,}$")
    full_name: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str | None = None
    address: str | None = None
    tier: CustomerTier = CustomerTier.STANDARD
    created_at: datetime


class OrderItem(BaseModel):
    product_id: str = Field(pattern=r"^prd_[0-9]{4,}$")
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)


class Order(BaseModel):
    order_id: str = Field(pattern=r"^ord_[0-9]{4,}$")
    customer_id: str = Field(pattern=r"^cust_[0-9]{4,}$")
    items: list[OrderItem] = Field(min_length=1)
    total: Decimal = Field(ge=0)
    status: OrderStatus = OrderStatus.PENDING
    version: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def total_matches_items(self) -> Order:
        expected = sum(i.quantity * i.unit_price for i in self.items)
        if self.total != expected:
            raise ValueError(f"total {self.total} != sum of items {expected}")
        return self


class SupportTicket(BaseModel):
    ticket_id: str = Field(pattern=r"^tkt_[0-9]{4,}$")
    customer_id: str = Field(pattern=r"^cust_[0-9]{4,}$")
    order_id: str | None = Field(default=None, pattern=r"^ord_[0-9]{4,}$")
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    status: TicketStatus = TicketStatus.OPEN
    version: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime

    @field_validator("subject", "description", mode="before")
    @classmethod
    def strip_control_chars(cls, value: object) -> object:
        if isinstance(value, str):
            return "".join(ch for ch in value if ch.isprintable() or ch in "\n\t")
        return value


class Product(BaseModel):
    product_id: str = Field(pattern=r"^prd_[0-9]{4,}$")
    name: str = Field(min_length=1)
    description: str = ""
    category: str = Field(min_length=1)
    price: Decimal = Field(ge=0)
    stock_quantity: int = Field(default=0, ge=0)


class InventoryItem(BaseModel):
    product_id: str = Field(pattern=r"^prd_[0-9]{4,}$")
    location: str = Field(min_length=1)
    quantity: int = Field(ge=0)
    reserved: int = Field(default=0, ge=0)
    reorder_threshold: int = Field(default=20, ge=0)


class ApiCredential(BaseModel):
    key_id: str = Field(min_length=1)
    api_key: str = Field(min_length=16)
    role: Role = Role.SUPPORT_AGENT
    revoked: bool = False


class AuditRecord(BaseModel):
    seq: int = Field(ge=0)
    timestamp: datetime
    key_id: str
    role: str
    action: str
    resource_type: str
    inputs_hash: str | None = None
    outcome: Outcome = Outcome.SUCCESS
    latency_ms: float = 0.0


class HealthReport(BaseModel):
    status: str
    uptime_seconds: float
    requests_total: int = 0
    latency_ms_p50: float = 0.0
    latency_ms_p95: float = 0.0
    error_rate: float = 0.0
    dependencies: dict[str, str] = Field(default_factory=dict)
    version: str = "0.1.0"


class ErrorRecord(TypedDict):
    step: str
    error_type: str
    message: str
    timestamp: str
