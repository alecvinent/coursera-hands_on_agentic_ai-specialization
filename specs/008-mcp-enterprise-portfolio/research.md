# Research: MCP Enterprise Integration Portfolio

**Feature**: 008-mcp-enterprise-portfolio
**Date**: 2026-09-18

## R1: MCP Protocol Specification Compliance

**Decision**: Follow MCP SDK v2 (`mcp` Python package) canonical implementation as used in task1.

**Rationale**: The `mcp` SDK v2 provides `MCPServer` with resource/tool decorators, STDIO and Streamable HTTP transports, and handles JSON-RPC framing. Hand-rolling protocol logic would risk non-compliance.

**Alternatives considered**:
- Custom JSON-RPC server: Rejected — high compliance risk, no standard transport support.
- REST-only API: Rejected — not MCP-compliant, loses protocol-level resource/tool semantics.

## R2: Architecture Assessment Delivery Format

**Decision**: Deliver as Markdown documents with Mermaid diagrams (renderable in GitHub/GitLab).

**Rationale**: Markdown is version-controllable, diffable, and renders natively in the target repositories. Mermaid diagrams are text-based and embeddable. PDF generation is optional and out of scope for the core deliverable.

**Alternatives considered**:
- PDF-only deliverable: Rejected — not diffable, harder to maintain.
- Slide deck (PPTX): Optional for portfolio presentation, not required for architecture assessment.

## R3: Enterprise Security Model

**Decision**: Extend task1's RBAC + API key model with role definitions specific to the retail scenario. No new authentication protocols.

**Rationale**: Task1 already implements `admin`, `support_agent`, `auditor`, `operator` roles with per-resource and per-tool permission checks. The retail scenario uses the same roles — extending them is consistent and low-risk.

**Alternatives considered**:
- OAuth 2.0 / OIDC: Out of scope for course project; noted in architecture assessment as future enhancement.
- mTLS client certificates: Operational complexity beyond course scope; TLS terminates at ingress.

## R4: Monitoring & Observability Stack

**Decision**: In-memory metrics + FastAPI sidecar (`/health`, `/metrics`, `/dashboard`), matching task1 patterns.

**Rationale**: Task1 demonstrates this pattern works. In-memory metrics are sufficient for single-host deployment. Prometheus/Grafana integration is documented as a scaling strategy but not implemented.

**Alternatives considered**:
- External metrics backend (Prometheus): Documented as future; in-memory sufficient for demo.
- Structured logging only (no dashboard): Insufficient — dashboard explicitly required.

## R5: CI/CD Pipeline

**Decision**: GitHub Actions YAML configuration providing lint, test, and Docker build stages.

**Rationale**: GitHub is the most common platform for course submissions. Pipeline is a configuration template, not a deployed pipeline.

**Alternatives considered**:
- GitLab CI: Equivalent; GitHub Actions chosen for broader familiarity.
- Jenkins: Too heavy for course project scope.

## R6: Disaster Recovery Approach

**Decision**: Documented procedures for seed data reset, audit log export, and configuration backup. No automated DR tooling.

**Rationale**: Mock data resets on startup by design. Audit logs and configuration are the only state that needs backup. Automated DR is overkill for a demo/course project.

**Alternatives considered**:
- Automated snapshot/restore scripts: Rejected — unnecessary complexity for in-memory mock data.

## R7: Integration Between Components

**Decision**: Architecture assessment's risk register directly maps to security framework controls. Server resource/tool design follows assessment's recommended integration points.

**Rationale**: The spec requires all three components to work cohesively. Explicit mapping ensures the assessment isn't a standalone document but drives implementation decisions.

**Alternatives considered**:
- Independent components: Rejected — violates integration requirement FR-019.

## R8: Portfolio Presentation Format

**Decision**: Markdown-based presentation (`presentation.md`) with structured sections. Optional Mermaid sequence diagrams for live demo flow.

**Rationale**: Markdown is consistent with all other deliverables. Slide deck conversion is a user preference, not a technical requirement.

**Alternatives considered**:
- PowerPoint/Google Slides: Optional; Markdown is the primary format.
