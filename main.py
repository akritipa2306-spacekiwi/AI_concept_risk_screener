from flask import Flask, render_template, request, session, redirect, url_for
from markupsafe import Markup
from openai import OpenAI
import markdown
import json
import re
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# ---------- Compressed governance prompt ----------
BASE_PROMPT = """
You are an AI Governance Assistant specialized in IDEATION-STAGE evaluation.

Your job is to decide whether a proposed AI system SHOULD BE BUILT, using these mechanisms:
1) Intake & System Registry
2) Purpose & Concept Assessment
3) Legal & Data Foundations
4) Stakeholder & Impact Assessment
5) Impact Triage (internal + external)
6) Feasibility Gate (GO / GO WITH CONDITIONS / NO-GO)

You will receive structured form inputs grouped into sections.

Always respond in CLEAN MARKDOWN with these headings:

### 1. SYSTEM INTAKE
Summarize:
- Proposed AI system name and description
- New system vs update to existing
- AI type (e.g., generative, predictive, classification, etc.)
- Primary intent / use case
- Regulatory exposure triggers (biometric data, minors, employment, housing, credit, health)

### 2. PURPOSE & CONCEPT CLARITY
Summarize and critique:
- Problem it solves and who experiences it today
- Value created by AI vs non-AI alternatives
- How success will be measured
- MVP definition (is it realistic and appropriately scoped?)

### 3. LEGAL & DATA FOUNDATIONS
Assess:
- Jurisdictions and regulatory frameworks:
  - Identify applicable regulations based on selected regions (GDPR, EU AI Act, US sectoral laws, PIPEDA, DPDP Act, PDPA, etc.)
  - Flag any cross-border data transfer concerns
  - Note jurisdiction-specific compliance requirements
- Data sources and provenance / licensing status
- Personal / sensitive data involved
- Third-party models, APIs, or vendors and their risks
- Deployment context (internal tool, customer-facing, embedded in product, etc.)
- Level of autonomy (fully automated vs human-in-the-loop vs manual trigger)
- Human annotator/moderator considerations:
  - Are annotators used? If so, evaluate annotation source
  - Labour safeguards, fair pay verification, and vulnerable worker protections
- Planned safeguards and mitigations:
  - Evaluate adequacy of selected safeguards (human review, access controls, audit logging, abuse monitoring, explainability, manual override, rate limits, etc.)
  - Note any gaps or missing safeguards given the system's risk profile

### 4. STAKEHOLDER & IMPACT ASSESSMENT
Analyse:
- Primary users and how they will interact with the system
- Affected / vulnerable groups (including non-users and downstream populations)
- Harm pathways that may apply:
  - Bias/unfair outcomes, incorrect/unsafe decisions, exclusion/denial of service
  - Privacy intrusion, IP/licensing issues, labour exploitation
  - Security vulnerabilities, misuse or dual-use risks
- Alignment with the stated risk tolerance
- Potential harms if it works as intended vs if it fails or misbehaves

### 5. IMPACT TRIAGE
Provide explicit ratings with brief justifications:
- External impact risk: Low / Medium / High
- Internal failure risk: Low / Medium / High
- Regulatory sensitivity: Low / Medium / High
- Governance level needed: Lightweight / Moderate / Full

### 6. FEASIBILITY GATE (GO / NO-GO)
Give:
- Overall recommendation: **GO**, **GO WITH CONDITIONS**, or **NO-GO**
- Bullet list of required mitigations or conditions (if any)
- Bullet list of unknowns / missing information that should be clarified before proceeding
- Any additional safeguards recommended beyond those already planned

### 7. GOVERNANCE READINESS SCORE
At the very end of your response, you MUST include a JSON block with scores.
Calculate a Numerical Governance Readiness Score (0-100) using this methodology:

1. External Harm Risk (0-30 points):
   - Low risk = 30 points
   - Medium risk = 15 points
   - High risk = 5 points

2. Internal Failure Risk (0-20 points):
   - Low = 20 points
   - Medium = 10 points
   - High = 5 points

3. Regulatory Sensitivity (0-20 points):
   - Low = 20 points
   - Medium = 10 points
   - High = 5 points

4. Data & Legal Soundness (0-20 points):
   Based on clarity of data provenance, licensing/rights, privacy requirements, cross-border issues, annotator labor ethics:
   - Excellent = 20 points
   - Moderate = 10 points
   - Weak = 5 points

5. Purpose & MVP Clarity (0-10 points):
   Based on problem clarity and solution fit:
   - Strong = 10 points
   - Moderate = 5 points
   - Weak = 2 points

Sum all points to get the final score (0-100).

Return the scores in this EXACT format at the end of your response:
```json
{
  "overall_score": <number 0-100>,
  "external_impact": "<Low/Medium/High>",
  "internal_failure": "<Low/Medium/High>",
  "regulatory_sensitivity": "<Low/Medium/High>",
  "data_legal_soundness": "<Excellent/Moderate/Weak>",
  "purpose_clarity": "<Strong/Moderate/Weak>"
}
```
"""

# ---------- OpenAI client ----------
api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if not client:
            session['error'] = "OpenAI API key is not configured in Replit Secrets."
            return redirect(url_for('results'))
        
        # Collect all fields from the wizard
        system_name = request.form.get("system_name", "").strip()
        short_description = request.form.get("short_description", "").strip()
        ai_type = request.form.get("ai_type", "").strip()
        new_or_update = request.form.get("new_or_update", "").strip()
        primary_intent = request.form.get("primary_intent", "").strip()
        
        # Regulatory exposure checkboxes
        reg_triggers = []
        if request.form.get("reg_biometric"):
            reg_triggers.append("Uses biometric data")
        if request.form.get("reg_minors"):
            reg_triggers.append("Involves minors")
        if request.form.get("reg_employment"):
            reg_triggers.append("Involves employment decisions")
        if request.form.get("reg_housing"):
            reg_triggers.append("Involves housing decisions")
        if request.form.get("reg_credit"):
            reg_triggers.append("Involves credit or financial eligibility")
        if request.form.get("reg_health"):
            reg_triggers.append("Involves health information")
        regulatory_exposure = ", ".join(reg_triggers) if reg_triggers else "None selected"

        problem = request.form.get("problem", "").strip()
        who_problem = request.form.get("who_problem", "").strip()
        value_created = request.form.get("value_created", "").strip()
        non_ai_alt = request.form.get("non_ai_alt", "").strip()
        success_metrics = request.form.get("success_metrics", "").strip()
        mvp_description = request.form.get("mvp_description", "").strip()

        # Jurisdictions
        jurisdictions = request.form.getlist("jurisdictions")
        jurisdictions_str = ", ".join(jurisdictions) if jurisdictions else "None selected"
        jurisdiction_notes = request.form.get("jurisdiction_notes", "").strip()
        
        data_sources = request.form.get("data_sources", "").strip()
        personal_data = request.form.get("personal_data", "").strip()
        third_parties = request.form.get("third_parties", "").strip()
        
        # Context of Use
        deployment_context = request.form.get("deployment_context", "").strip()
        level_of_autonomy = request.form.get("level_of_autonomy", "").strip()
        deployment_notes = request.form.get("deployment_notes", "").strip()
        
        provenance = request.form.get("provenance", "").strip()
        
        # Human annotators section
        uses_annotators = "Yes" if request.form.get("uses_annotators") else "No"
        annotation_source = request.form.get("annotation_source", "").strip()
        labour_safeguards = request.form.get("labour_safeguards", "").strip()
        pay_verified = request.form.get("pay_verified", "").strip()
        vulnerable_annotators = request.form.get("vulnerable_annotators", "").strip()
        
        # Planned safeguards
        safeguards = request.form.getlist("safeguards")
        safeguards_str = ", ".join(safeguards) if safeguards else "None selected"
        custom_safeguards = request.form.get("custom_safeguards", "").strip()

        primary_users = request.form.get("primary_users", "").strip()
        affected_groups = request.form.get("affected_groups", "").strip()
        harm_pathways = request.form.getlist("harm_pathways")
        harm_pathways_str = ", ".join(harm_pathways) if harm_pathways else "None selected"
        risk_tolerance = request.form.get("risk_tolerance", "").strip()

        # Build a single structured prompt for GPT
        user_input = f"""
[SECTION 1: SYSTEM INTAKE]
System name: {system_name}
Short description: {short_description}
AI type: {ai_type}
New or update: {new_or_update}
Primary intent: {primary_intent}
Regulatory exposure triggers: {regulatory_exposure}

[SECTION 2: PURPOSE & CONCEPT]
Problem it solves: {problem}
Who experiences this problem today: {who_problem}
Value created by AI: {value_created}
Non-AI alternative today: {non_ai_alt}
Success will be measured by: {success_metrics}
MVP description: {mvp_description}

[SECTION 3: LEGAL & DATA FOUNDATIONS]
Regions / Jurisdictions: {jurisdictions_str}
Jurisdiction notes: {jurisdiction_notes}
Data sources: {data_sources}
Personal / sensitive data involved: {personal_data}
Third-party models / APIs / vendors: {third_parties}
Deployment context: {deployment_context}
Level of autonomy: {level_of_autonomy}
Deployment notes: {deployment_notes}
Data provenance / licensing notes: {provenance}
Uses human annotators/reviewers/moderators: {uses_annotators}
Annotation source: {annotation_source}
Labour safeguards: {labour_safeguards}
Pay is fair & verified: {pay_verified}
Vulnerable annotator groups: {vulnerable_annotators}
Planned safeguards / mitigations: {safeguards_str}
Custom safeguards: {custom_safeguards}

[SECTION 4: STAKEHOLDERS & IMPACT]
Primary users: {primary_users}
Affected groups (including vulnerable groups): {affected_groups}
Harm pathways that may apply: {harm_pathways_str}
Stated risk tolerance: {risk_tolerance}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": BASE_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.2,
            )
            raw_result = response.choices[0].message.content or ""
            
            # Extract JSON scores from the response
            scores = None
            json_match = re.search(r'```json\s*(\{[^`]+\})\s*```', raw_result, re.DOTALL)
            if json_match:
                try:
                    scores = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    scores = None
            
            # Remove the JSON block from the markdown display
            display_result = re.sub(r'```json\s*\{[^`]+\}\s*```', '', raw_result, flags=re.DOTALL)
            
            session['result'] = markdown.markdown(display_result.strip(), extensions=['tables', 'fenced_code'])
            session['scores'] = scores
            session['error'] = None
        except Exception as e:
            session['error'] = f"An error occurred while calling the API: {str(e)}"
            session['result'] = None
            session['scores'] = None

        return redirect(url_for('results'))

    return render_template("index.html")


@app.route("/results")
def results():
    result = session.pop('result', None)
    error = session.pop('error', None)
    scores = session.pop('scores', None)
    
    if result:
        result = Markup(result)
    
    if not result and not error:
        return redirect(url_for('index'))
    
    return render_template("results.html", result=result, error=error, scores=scores)


if __name__ == "__main__":
    # On Replit, host/port are usually handled for you, but this is safe:
    app.run(host="0.0.0.0", port=5000, debug=True)
