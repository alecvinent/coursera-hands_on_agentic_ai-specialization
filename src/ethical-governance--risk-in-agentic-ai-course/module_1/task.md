**System Classification**

* **System A (Fraud Detection)**
* **Classification:** Autonomous Agent


* **Justification:** It operates independently in real-time by taking direct action (temporarily blocking high-risk transactions) and possesses adaptive learning mechanisms to adjust sensitivity based on emerging fraud patterns.




* **System B (Customer Service Chatbot)**
* **Classification:** Adaptive


* **Justification:** It modifies its behavior over time by learning from interactions to improve responses, but it operates within bounded routine tasks and defers complex decisions to human agents via escalation.




* **System C (Investment Advisory System)**
* **Classification:** Agentic AI


* **Justification:** It exhibits high agency and goal-directed autonomy by independently analyzing complex market environments, generating strategic investment recommendations, and executing automatic portfolio rebalancing.





---

**Risk Assessment**

* **System A (Fraud Detection)**
* **Independent Decisions:** Temporarily blocking high-risk transactions and self-adjusting sensitivity thresholds.


* **Consequences:** False positives can disrupt legitimate customer transactions, leading to financial friction, customer dissatisfaction, and revenue loss.
* **Transparency:** Moderate to low. Machine learning sensitivity adjustments can act as a black box, making it difficult to explain specific transaction flags to users immediately.


* **System B (Customer Service Chatbot)**
* **Independent Decisions:** Routing queries, selecting response templates, and determining when to escalate issues.


* **Consequences:** Hallucinated or incorrect information provided to customers, brand damage, improper escalation routing, or subtle bias in customer interaction quality.
* **Transparency:** High for dialogue logs, though internal weight updates from learning interactions require oversight to prevent drift.


* **System C (Investment Advisory System)**
* **Independent Decisions:** Executing financial asset trades and rebalancing portfolios automatically.


* **Consequences:** Severe financial losses for clients, market systemic risk, breach of fiduciary duty, or systemic bias favoring specific asset classes under volatile market conditions.
* **Transparency:** Low to moderate. Complex algorithmic trade strategies and risk weighting models require robust audit trails to justify automatic executions.



---

**Governance Recommendations**

* **System A (Fraud Detection)**
* **Human Oversight:** Human-in-the-loop (HITL) for secondary review of blocked transactions within a designated SLA and clear appeal pathways for affected customers.
* **Monitoring & Auditing:** Automated real-time alerts for spike anomalies in block rates, paired with periodic audits of false-positive ratios to calibrate sensitivity models.
* **Accountability:** Fraud Operations Lead holds operational accountability; Risk & Compliance oversees model sensitivity thresholds.


* **System B (Customer Service Chatbot)**
* **Human Oversight:** Human-on-the-loop (HOTL) with customer service leads sampling interactions and stepping in when negative sentiment or repeated escalation flags trigger.
* **Monitoring & Auditing:** Regular evaluation of conversation logs for response accuracy, hallucination rates, and drift detection on continuous learning updates.
* **Accountability:** Customer Support Operations Manager owns output quality and prompt maintenance.


* **System C (Investment Advisory System)**
* **Human Oversight:** Strict Human-on-the-loop (HOTL) with mandatory guardrails (e.g., hard stop limits on trade execution sizes, maximum daily loss triggers requiring human authorization to resume).
* **Monitoring & Auditing:** Continuous, automated audit logging of all rebalancing decisions against pre-defined risk parameters and compliance rules, supplemented by quarterly algorithmic bias and fiduciary audits.
* **Accountability:** Chief Investment Officer (CIO) and Head of Compliance hold joint legal and fiduciary accountability for automated portfolio executions.