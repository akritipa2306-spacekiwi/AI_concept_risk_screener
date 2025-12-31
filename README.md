# AI Concept Risk Screener

A governance-first AI strategy MVP that helps teams answer a critical early question:

**“Should we build this AI system — and under what conditions?”**

This project focuses on **ideation-stage AI risk assessment**, before code is written, vendors are locked in, or regulatory exposure becomes expensive to unwind.

---

## Why this exists

Most AI governance tools operate **after deployment**, when risk has already materialized.

Early-stage teams face a different problem:
- Investors ask about AI risk before funding
- Product teams must justify AI features before budget approval
- Founders lack governance expertise but still need defensible answers

This MVP explores how AI governance can be embedded **upstream**, as a lightweight decision gate during ideation — not as a post-hoc compliance exercise.

---

## What it does

The AI Concept Risk Screener guides users through a **4-step ideation wizard** and produces a **deterministic governance readiness score** with an explicit feasibility recommendation.

### Core capabilities
- **System intake**  
  AI type, intent, autonomy level, and regulatory triggers
- **Purpose & MVP clarity assessment**  
  Evaluates problem definition and scope realism
- **Legal, data & vendor foundations**  
  Jurisdiction mapping, data sources, and third-party model risk
- **Stakeholder & harm pathway analysis**  
  Bias, misuse, safety, labour, privacy, and regulatory exposure

### Outputs
- Governance readiness score (0–100)
- Risk classification across multiple dimensions
- **GO / GO WITH CONDITIONS / NO-GO** recommendation
- Concrete mitigation requirements (not generic best practices)
- Exportable evaluation report (PDF)

The intent is not to replace legal or ethics review, but to **surface unknowns early and make tradeoffs explicit**.

---

## Governance lens

This project is informed by practical interpretations of:
- EU AI Act risk categorization
- NIST AI Risk Management Framework
- Data provenance and annotation supply-chain risks
- Third-party / vendor dependency analysis

Rather than mapping frameworks verbatim, the focus is on **turning governance principles into product flows**:
inputs → validation → scoring → explanation → decision.

---

## What makes this different

- **Ideation-stage focus**  
  Designed for the “should we build this?” moment, not post-deployment audits
- **Deterministic scoring**  
  Prevents LLM hallucinated math and enables explainable decisions
- **Vendor intelligence built-in**  
  Pre-populated risk profiles for common model providers
- **Actionable outputs**  
  Specific mitigations and unknowns, not abstract guidance
- **Lightweight UX**  
  10–15 minute evaluation instead of 40-page questionnaires

---

## Scoring overview (high-level)

The governance readiness score combines multiple dimensions, including:
- External harm risk
- Internal system failure risk
- Regulatory sensitivity
- Data & legal soundness
- Purpose & MVP clarity

Scores map to clear decision states:
- **70–100** → GO  
- **40–69** → GO WITH CONDITIONS  
- **0–39** → NO-GO / significant remediation required  

(Scoring logic is deterministic by design.)

---

## Target users

- Early-stage AI founders evaluating feasibility under investor scrutiny
- Product managers proposing new AI features internally
- VCs and accelerators performing AI governance due diligence

The tool is designed to help technical and non-technical stakeholders align around the same risk artifact.

---

## Tech overview

- **Backend:** Python, Flask
- **Frontend:** Jinja2 templates, vanilla JS, Tailwind (CDN)
- **AI:** OpenAI GPT-4o-mini (contextual analysis)
- **Data:** Static vendor risk profiles (JSON), session storage
- **Deployment:** Replit (MVP)

Technology choices were optimized for speed, clarity, and auditability rather than scale.

---

## Status & intent

This is a **portfolio MVP**, built to:
- explore governance-as-product patterns
- test ideation-stage risk workflows
- serve as a concrete AI strategy artifact

It is not production software.

---

## Author

Built by **Akriti Parida**

