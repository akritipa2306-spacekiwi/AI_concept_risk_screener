from flask import Flask, render_template, request, session, redirect, url_for
from markupsafe import Markup
from openai import OpenAI
import markdown
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
- Proposed AI system
- New vs update
- AI type

### 2. PURPOSE & CONCEPT CLARITY
Summarize and critique:
- Problem it solves
- Who experiences this problem today
- Value created by AI
- Non-AI alternative today
- How success will be measured
- MVP definition (is it realistic?)

### 3. LEGAL & DATA FOUNDATIONS
Assess:
- Personal / sensitive data
- Data sources and provenance
- Third-party models / vendors
- Any consent, IP, licensing, or data-protection risks
- Any labour / human-rights concerns for annotations or data collection

### 4. STAKEHOLDER & IMPACT ASSESSMENT
Analyse:
- Primary users
- Affected / vulnerable groups
- Potential harms if it works as intended
- Potential harms if it fails or misbehaves
- Alignment with the stated risk tolerance

### 5. IMPACT TRIAGE
Provide explicit ratings:
- External impact risk: Low / Medium / High (with one-sentence justification)
- Internal failure risk: Low / Medium / High
- Regulatory sensitivity: Low / Medium / High
- Governance level needed: Lightweight / Moderate / Full

### 6. FEASIBILITY GATE (GO / NO-GO)
Give:
- Overall recommendation: **GO**, **GO WITH CONDITIONS**, or **NO-GO**
- Bullet list of required mitigations (if any)
- Bullet list of unknowns / missing information that should be clarified
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

        problem = request.form.get("problem", "").strip()
        who_problem = request.form.get("who_problem", "").strip()
        value_created = request.form.get("value_created", "").strip()
        non_ai_alt = request.form.get("non_ai_alt", "").strip()
        success_metrics = request.form.get("success_metrics", "").strip()
        mvp_description = request.form.get("mvp_description", "").strip()

        data_sources = request.form.get("data_sources", "").strip()
        personal_data = request.form.get("personal_data", "").strip()
        third_parties = request.form.get("third_parties", "").strip()
        provenance = request.form.get("provenance", "").strip()

        primary_users = request.form.get("primary_users", "").strip()
        affected_groups = request.form.get("affected_groups", "").strip()
        harms = request.form.get("harms", "").strip()
        risk_tolerance = request.form.get("risk_tolerance", "").strip()

        # Build a single structured prompt for GPT
        user_input = f"""
[SECTION 1: SYSTEM INTAKE]
System name: {system_name}
Short description: {short_description}
AI type: {ai_type}
New or update: {new_or_update}

[SECTION 2: PURPOSE & CONCEPT]
Problem it solves: {problem}
Who experiences this problem today: {who_problem}
Value created by AI: {value_created}
Non-AI alternative today: {non_ai_alt}
Success will be measured by: {success_metrics}
MVP description: {mvp_description}

[SECTION 3: LEGAL & DATA FOUNDATIONS]
Data sources: {data_sources}
Personal / sensitive data involved: {personal_data}
Third-party models / APIs / vendors: {third_parties}
Data provenance / licensing notes: {provenance}

[SECTION 4: STAKEHOLDERS & IMPACT]
Primary users: {primary_users}
Affected groups (including vulnerable groups): {affected_groups}
Potential harms or concerns: {harms}
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
            session['result'] = markdown.markdown(raw_result, extensions=['tables', 'fenced_code'])
            session['error'] = None
        except Exception as e:
            session['error'] = f"An error occurred while calling the API: {str(e)}"
            session['result'] = None

        return redirect(url_for('results'))

    return render_template("index.html")


@app.route("/results")
def results():
    result = session.pop('result', None)
    error = session.pop('error', None)
    
    if result:
        result = Markup(result)
    
    if not result and not error:
        return redirect(url_for('index'))
    
    return render_template("results.html", result=result, error=error)


if __name__ == "__main__":
    # On Replit, host/port are usually handled for you, but this is safe:
    app.run(host="0.0.0.0", port=5000, debug=True)
