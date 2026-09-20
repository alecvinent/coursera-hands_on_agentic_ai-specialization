Here is a publication-ready **Ethical Governance Framework** tailored specifically for an automated elderly care residential facility: **"Casa Yordan — Autonomous Residential Assistance & Facility Management System."**

---

# Ethical Governance Framework: Autonomous Residential Assistance & Facility Management

**Organization:** Casa Yordan (Residential Facility for Older Adults)

**Target Deployment:** Autonomous Patient Monitoring, Ambient Climate Control, and WhatsApp Care Coordinator

**Word Count Target:** ~3,500 words Equivalent Structure

---

## Executive Summary

As AI implementations move from passive logging to active, autonomous environmental control and health alerting in sensitive environments, strict ethical governance becomes vital. **Casa Yordan** is deploying an integrated AI agent system across ambient IoT hardware, administrative dashboards, and WhatsApp communication channels. The system autonomously manages room climate and lighting, schedules dietary and medication alerts, monitors non-invasive wellness parameters, and routes family updates.

Given the vulnerability of care home residents, this framework prioritizes physical safety, privacy, and personal dignity. Aligned with the **EU AI Act** (classified under High-Risk management systems), **NIST AI Risk Management Framework (AI RMF)**, and Uruguayan Personal Data Protection Law (Law 18.331), this document defines system autonomy limits, data safeguards, and mandatory **Human-in-the-Loop (HITL)** oversight for all medical or emergency escalations.

---

## 1. System Analysis and Autonomy Assessment

### System Description & Intended Use Case

The **Casa Yordan Autonomous Facility System** is a hybrid software and IoT infrastructure operating across ambient sensors, dynamic nursing dashboards, and automated messaging endpoints. Its core functions include:

* Regulating room environmental parameters (lighting, temperature, air quality) tailored to resident health profiles.
* Generating real-time non-invasive wellness alerts (e.g., movement anomaly detection, missed routine check-ins) to nursing staff.
* Coordinating daily dietary schedules based on medical restrictions and preferences.
* Providing families with automated, structured updates regarding facility activities and daily care logs via WhatsApp.

### Autonomy Assessment

Using the Course Autonomy Framework, the system operates across strictly defined autonomy tiers based on operational risk:

| Task Domain | Autonomy Level | Description & Boundary Limits |
| --- | --- | --- |
| **Ambient Climate & Lighting Control** | **Level 4 (High Autonomy)** | Adjusts HVAC and ambient lighting within pre-approved medical temperature bands without manual sign-off. |
| **Family Notifications & Administrative Logistics** | **Level 3 (Conditional Autonomy)** | Drafts and sends routine facility announcements and schedule summaries; flags non-standard inquiries for administrative review. |
| **Dietary & Meal Planning Alerts** | **Level 2 (Assisted Autonomy)** | Generates daily menu recommendations based on dietary profiles; requires caregiver verification before meal prep. |
| **Emergency Health & Anomaly Escalations** | **Level 1 (Human-Driven)** | Triggers immediate alert signals to staff dashboards and phones upon detecting movement anomalies or distress. No autonomous clinical action is taken. |

### Stakeholder Impact Analysis

* **Residents:** Experience customized ambient comfort, prompt staff responses, and tailored dietary care. Primary risks include privacy loss, algorithmic misinterpretation of normal behavior, and reduced human contact if over-automated.
* **Caregivers & Nursing Staff:** Benefit from reduced administrative burden and actionable fall/anomaly alerts. Risks include alert fatigue, over-reliance on automated checks, or system misconfigurations.
* **Facility Leadership & Families:** Families gain transparent, timely updates; leadership optimizes operational efficiency. Risks involve reputational damage and severe legal liability in the event of an unflagged emergency.

### Key Governance Challenges

1. **Informed Consent & Cognitive Capacity:** Managing data rights and operational consent when residents may have varying levels of cognitive capability.
2. **Zero-Tolerance Fall Identification:** Ensuring high-sensitivity anomaly detection while preventing false-alarm fatigue among care staff.
3. **Data Protection in Sensitive Environments:** Securing continuous telemetry and personal health information against unauthorized access or leakages.

---

## 2. Compliance and Regulatory Strategy

### Applicable Regulatory Frameworks

```
                       ┌────────────────────────────────────────┐
                       │      Global & Sector Regulations       │
                       └───────────────────┬────────────────────┘
                                           │
         ┌─────────────────────────────────┼────────────────────────────────┐
         ▼                                 ▼                                ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│   EU AI Act      │             │  NIST AI RMF     │             │ Law 18.331 (UY)  │
│  (High-Risk AI   │             │ (Map, Measure,   │             │ (Sensitive Health│
│ Classification)  │             │ Manage, Govern)  │             │ Data Protection) │
└──────────────────┘             └──────────────────┘             └──────────────────┘

```

1. **EU AI Act Alignment:** Classified as a **High-Risk AI System** due to its deployment in critical infrastructure and healthcare/caregiver support settings. Requires fundamental rights impact assessments, strict logging, accuracy benchmarking, and human oversight mechanisms.
2. **NIST AI Risk Management Framework (AI RMF 1.0):** Operationalized across *Govern*, *Map*, *Measure*, and *Manage* to ensure reliability, data privacy, and safety in high-vulnerability environments.
3. **Uruguay Data Protection Law (Law 18.331):** Categorizes resident health and daily activity records as **Sensitive Data**, requiring explicit consent (or legal guardian authorization), encryption, and strict access controls.

### Adaptive Compliance Architecture

To maintain regulatory compliance without disrupting core operational uptime, the system employs a modular, isolated architecture:

* **Sensor & Edge Processing Layer:** Processes movement and ambient telemetry locally; raw video or biometric feeds are discarded or anonymized at the edge.
* **Governance & Policy Engine:** Sits between the AI analytics layer and notification services to validate actions against safety thresholds (e.g., verifying maximum room temperature caps).
* **Care Core Engine:** Executes schedule management, dietary filtering, and ambient adjustments.
* **Immutable Audit Vault:** Cryptographically logs all system triggers, environmental changes, human overrides, and alert dispatches for legal and clinical compliance auditing.

### Implementation Timeline and Resource Requirements

```
Phase 1: Architecture, Privacy & Safety Controls (Months 1-2)
  ├── Edge Anonymization & Data Encryption Pipeline
  └── Baseline Health & Safety Rule Formulation
Phase 2: Closed-Loop Simulation & Red Teaming (Month 3)
  ├── Sensor Failure & False-Positive Alert Stress Testing
  └── Regulatory Compliance Audit (Law 18.331)
Phase 3: Controlled Pilot Rollout (Month 4)
  ├── Deployment in 10% of facility rooms
  └── 24/7 Co-Monitoring with On-Duty Nursing Staff
Phase 4: Full Deployment & Continuous Oversight (Month 5+)
  └── Quarterly Safety Model Recalibration & Regulatory Audits

```

* **Budget & Resources:** Allocation of 20% of engineering and operational resources specifically toward compliance verification, edge-device security, and staff safety training.

### Mitigation Strategies for Regulatory Non-Compliance

* **Fail-Safe Analog Mode:** In the event of network disruption or governance gateway failure, all room systems default to standard manual thermostat and switch controls, and alarm systems revert to direct physical call-buttons.
* **Guardian Audit Access:** Primary family members or legal guardians can request an itemized log of automated decisions (e.g., temperature adjustments, notification logs) affecting their family member.

---

## 3. Risk Management and Governance Structure

### Comprehensive Risk Matrix

| Risk Dimension | Risk Description | Severity | Likelihood | Mitigation Strategy |
| --- | --- | --- | --- | --- |
| **Technical** | Sensor drift or offline status causing incorrect room temperature or missed anomaly detection. | High | Medium | Dual-sensor redundancy and hourly automated self-diagnostic ping tests. |
| **Operational** | Caregivers develop over-reliance on AI monitoring, reducing manual in-person check-ins. | High | Medium | Enforce mandatory physical check-in logs that cannot be bypassed by automated telemetry. |
| **Ethical** | Over-monitoring violating resident dignity and personal privacy. | High | Low | Purely non-visual acoustic/thermal/radar sensors for ambient rooms; no optical cameras in private living quarters. |
| **Regulatory** | Unlawful processing of sensitive medical or daily behavioral records. | Critical | Low | On-premise or localized encrypted data storage; signed guardian consent agreements. |
| **Reputational** | False alarm causing unnecessary family panic via WhatsApp notifications. | Medium | Medium | Automated alerts sent strictly to internal nursing staff first; family notifications sent only after human verification. |

### Governance Organizational Structure

```
                  ┌────────────────────────────────────────┐
                  │       AI Governance Lead (Owner)       │
                  │   Oversees compliance & ethical risk   │
                  └───────────────────┬────────────────────┘
                                      │
         ┌────────────────────────────┴────────────────────────────┐
         ▼                                                         ▼
┌──────────────────────────────────┐             ┌──────────────────────────────────┐
│    Technical Systems Engineer    │             │   Head Nurse / Medical Director  │
│ Oversees hardware & audit logs   │             │ Manages human response & overrides│
└──────────────────────────────────┘             └──────────────────────────────────┘

```

* **AI Governance Lead (Owner):** Maintains compliance documentation, oversees risk reviews, and reports directly to facility leadership.
* **Technical Systems Engineer:** Responsible for edge device integrity, cyber-security, software updates, and guardrail maintenance.
* **Head Nurse / Medical Director:** Serves as the primary Human-in-the-Loop authority, validating dietary plans, reviewing anomaly alerts, and overriding environmental settings when clinically necessary.

### Monitoring, Oversight, and Incident Response

* **Real-time Telemetry Dashboard:** Stationed at the central nursing station, showing device connection statuses, ambient conditions, pending human verifications, and alert logs.
* **Escalation Protocol:**
1. **Level 1 (Environmental Anomaly / Tech Warning):** Dispatches automated task to maintenance staff; local room controls remain operational.
2. **Level 2 (Resident Behavioral Anomaly / Health Alert):** Instant visual and audible notification on nursing dashboard; requires caregiver in-person verification within 3 minutes to clear.
3. **Level 3 (System Failure / Cyber Incident):** System drops to manual facility control; immediate alert dispatched to Technical Lead and Medical Director.



---

## 4. Implementation and Sustainability Plan

### Implementation Roadmap & Success Metrics

```
┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
│          Phase 1          │          Phase 2          │          Phase 3          │
│    Foundation & Design    │    Validation & Pilot     │   Scaling & Evolution     │
│       (Months 1-2)        │       (Months 3-4)        │        (Months 5+)        │
└─────────────┬─────────────┴─────────────┬─────────────┴─────────────┬─────────────┘
              │                           │                           │
              ▼                           ▼                           ▼
  • Hardware & Guardrail Setup   • Hardware Stress Testing   • Facility-Wide Rollout
  • Consent Framework Setup       • 10% Room Pilot Phase      • Annual Ethical Audits
  • Nursing Staff Orientation     • HITL Workflow Fine-Tuning • Regulatory Alignment

```

#### Success Metrics (KPIs)

* **Response Latency:** <60 seconds from anomaly detection to nurse dashboard alert.
* **System Accuracy:** >99.9% uptime on safety-critical environmental sensors.
* **Human Verification Compliance:** 100% of health/dietary alerts reviewed by qualified staff prior to execution.
* **Privacy Compliance:** Zero unauthorized data transfers or unencrypted health log exports.

### Change Management & Training Strategy

* **Caregiver & Staff Integration:** Comprehensive training program educating staff that the AI system is an advisory assistant designed to handle ambient tasks, not a replacement for human empathy and care.
* **Resident & Family Onboarding:** Clear orientation packages detailing what data is collected, how non-invasive radar/thermal sensors work, and how personal privacy is maintained.

### Long-Term Sustainability and Evolution

* **Continuous System Recalibration:** Bi-monthly reviews of false-positive and false-negative alert rates to tune detection thresholds without compromising safety.
* **Evolving Standard Review:** Semi-annual policy assessments to adapt the governance structure to emerging health-tech AI mandates, accessibility standards, and privacy legislation updates.
* **Model Drift Safeguards:** Weekly validation against baseline evaluation logs to prevent degraded performance in environmental control algorithms or communication parsing.

---

## Appendices

### Appendix A: Resident Data Consent & Transparency Form Header

> *"Casa Yordan is committed to providing a safe, comfortable, and dignified living environment. Our facility utilizes automated ambient systems to adjust room comfort and assist caregivers in monitoring resident well-being. All processing is completed using non-invasive sensors in strict compliance with Law 18.331. No optical cameras are used in private living quarters. Families and residents maintain full rights to inspect data logs and opt out of non-essential features at any time."*

### Appendix B: Operational Health Alert Escalation Flow

```
                      ┌─────────────────────────────────┐
                      │    Ambient Sensor / Telemetry   │
                      └────────────────┬────────────────┘
                                       │
                                       ▼
                       /───────────────────────────────\
                      < Does Event Exceed Safety Band?  >
                       \───────────────┬───────────────/
                                       │
                         ┌─────────────┴─────────────┐
                         │ YES                       │ NO
                         ▼                           ▼
         /───────────────────────────────\   ┌────────────────┐
        < Is Event Medical or Anomaly?   >   │ Maintain Ambient│
         \───────────────┬───────────────/   │ Control (L4)   │
                         │                   └────────────────┘
           ┌─────────────┴─────────────┐
           │ Medical/Anomaly           │ Environmental Only
           ▼                           ▼
 ┌───────────────────┐       ┌───────────────────┐
 │ Trigger L1 Alert: │       │ Adjust HVAC/Light │
 │ Nurse Dashboard   │       │ Within Pre-Set    │
 │ (Requires HITL)   │       │ Thermal Bands     │
 └───────────────────┘       └───────────────────┘

```