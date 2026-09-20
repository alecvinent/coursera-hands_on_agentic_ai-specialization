Here is a complete, production-ready Model Context Protocol (MCP) Resource Schema designed for the TechFlow Analytics Sales Intelligence AI Assistant.

---

# MCP Resource Schema Documentation: TechFlow Sales Intelligence

## 1. Resource Inventory

The schema exposes four core entities required for real-time sales intelligence:

* **Customers (`customers`)**: Core demographic, health score, account manager, and value tier data for client accounts.
* **Deals (`deals`)**: Individual sales opportunities, including deal stage, monetary value, close dates, and probability.
* **Activities (`activities`)**: Interaction logs (calls, emails, meetings, notes) mapped to accounts or specific deals.
* **Pipelines (`pipelines`)**: Aggregated metrics, stage conversion rates, and total value distribution across active pipelines.

---

## 2. Resource URI Design & Patterns

All resources use the custom `sales://` scheme and follow a hierarchical, predictable path convention to support specific lookups and filtered dynamic views.

### URI Structure Rules

* **Collection Roots**: `sales://{entity}`
* **Direct Entity Lookup**: `sales://{entity}/{id}`
* **Filtered Views**: `sales://{entity}/{filter_category}/{filter_value}`
* **Nested Sub-resources**: `sales://{entity}/{id}/{sub_entity}`

### Target URI Patterns

| Resource Type | URI Pattern | Description / Usage Example |
| --- | --- | --- |
| **Customers** | `sales://customers/id/{customer_id}` | Direct profile lookup (`sales://customers/id/cust_10293`) |
| **Customers (Filtered)** | `sales://customers/tier/{tier_level}` | Segmented view (`sales://customers/tier/enterprise`) |
| **Deals** | `sales://deals/id/{deal_id}` | Detailed deal breakdown (`sales://deals/id/deal_8832`) |
| **Deals (Filtered)** | `sales://deals/stage/{stage_name}` | Pipeline status check (`sales://deals/stage/closing_this_month`) |
| **Activities** | `sales://customers/{customer_id}/activities` | Recent interaction timeline for an account |
| **Pipeline Summary** | `sales://pipelines/summary/{timeframe}` | Aggregated sales metrics (`sales://pipelines/summary/q3_2026`) |

---

## 3. Resource Schema Definitions

Below are JSON definitions representing the structure, metadata, and MIME types returned by the MCP server.

### Schema 1: Customer Profile Resource

```json
{
  "uri": "sales://customers/id/cust_10293",
  "name": "Customer Account Profile",
  "description": "Comprehensive customer profile including contact details, tier, and account health score.",
  "mimeType": "application/json",
  "schema": {
    "type": "object",
    "properties": {
      "customerId": { "type": "string" },
      "companyName": { "type": "string" },
      "tier": { "type": "string", "enum": ["SMB", "Mid-Market", "Enterprise"] },
      "primaryContact": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "email": { "type": "string" },
          "role": { "type": "string" }
        }
      },
      "accountOwner": { "type": "string" },
      "healthScore": { "type": "integer", "minimum": 0, "maximum": 100 },
      "arr": { "type": "number", "description": "Annual Recurring Revenue in USD" }
    },
    "required": ["customerId", "companyName", "tier", "healthScore"]
  }
}

```

### Schema 2: High-Value Closing Deals Resource

```json
{
  "uri": "sales://deals/stage/closing_this_month",
  "name": "Deals Closing Current Month",
  "description": "Filtered view of all open deals scheduled to close within the current calendar month.",
  "mimeType": "application/json",
  "schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "dealId": { "type": "string" },
        "customerId": { "type": "string" },
        "title": { "type": "string" },
        "value": { "type": "number" },
        "currency": { "type": "string", "default": "USD" },
        "stage": { "type": "string" },
        "probability": { "type": "number", "minimum": 0, "maximum": 1 },
        "expectedCloseDate": { "type": "string", "format": "date" }
      },
      "required": ["dealId", "customerId", "value", "stage", "expectedCloseDate"]
    }
  }
}

```

### Schema 3: Sales Activity Log Resource

```json
{
  "uri": "sales://customers/cust_10293/activities",
  "name": "Customer Activity Stream",
  "description": "Chronological history of communications and sales engagements for a specific customer.",
  "mimeType": "application/json",
  "schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "activityId": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "type": { "type": "string", "enum": ["call", "email", "meeting", "note"] },
        "author": { "type": "string" },
        "summary": { "type": "string" },
        "sentiment": { "type": "string", "enum": ["positive", "neutral", "negative"] }
      },
      "required": ["activityId", "timestamp", "type", "summary"]
    }
  }
}

```

---

## 4. Access Pattern & Usage Documentation

### Core Query Patterns

* **Prompt**: *"Show me all high-value deals closing this month."*
* **Resource Access**: Reads `sales://deals/stage/closing_this_month`.
* **AI Action**: Filters items where `value > 50000` and sorts by `probability`.


* **Prompt**: *"What's the status of the Johnson account?"*
* **Resource Access**: Fetches `sales://customers/id/cust_johnson` and `sales://customers/cust_johnson/activities`.
* **AI Action**: Combines customer metadata with the latest activity timeline to compose a contextual summary.



### Multi-Resource Orchestration

To answer complex analytical questions like *"Which enterprise accounts are at risk of missing their close date?"*, the AI assistant queries across paths:

1. Fetch active deals: `sales://deals/stage/in_negotiation`
2. Fetch account health scores: `sales://customers/tier/enterprise`
3. Join data on `customerId` where `healthScore < 50` and highlight deals closing within 14 days.

---

## 5. Architectural Reflection

* **Simplicity vs. Functionality in URI Design**: Static parameterization in URIs (e.g., `/stage/closing_this_month`) keeps the AI resource requests simple and explicit without forcing the AI to build complex SQL/GraphQL dynamic parameters. Advanced ad-hoc operations are handled by standard MCP tool calls instead of resources.
* **AI Usage Assumptions**: The schema assumes the AI assistant can parse ISO-8601 timestamps and perform client-side filtering/formatting on standard JSON arrays returned by filtered resource URIs.
* **Edge Case Handling**: If a filtered view returns an empty list (e.g., zero deals closing), the resource returns an empty array `[]` with a `200 OK` structure rather than an error, allowing the AI to naturally reply *"There are no deals matching that criteria."*
* **Multi-Team Scalability**: To support multiple sales teams, URIs can be namespaced by region or department using a `sales://{tenant_id}/{team_id}/...` path prefix (e.g., `sales://us_east/enterprise/deals/stage/closing_this_month`).
