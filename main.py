from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from markupsafe import Markup
from openai import OpenAI
import markdown
import json
import re
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Use server-side session storage to avoid cookie size limits
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
app.config['SESSION_PERMANENT'] = False
Session(app)

# ---------- Vendor Database ----------
VENDOR_DATABASE = [
    {
        "id": "openai-gpt4",
        "name": "OpenAI GPT-4",
        "aliases": ["openai", "gpt-4", "gpt4", "chatgpt", "gpt-4o", "gpt-4-turbo", "gpt"],
        "logo": "🤖",
        "category": "Large Language Model",
        "trainingData": {
            "sources": "Web crawl, licensed datasets, books, academic papers",
            "cutoffDate": "September 2021 (GPT-4), April 2023 (GPT-4 Turbo)",
            "geographicCoverage": "Global with heavy English/Western bias",
            "knownDatasets": "Common Crawl, WebText, Books corpus (proprietary mix)"
        },
        "transparency": {
            "level": "Low",
            "details": "Does not disclose training data composition, ratios, or specific sources",
            "dataLineage": False,
            "auditability": False
        },
        "knownBiases": [
            "Strong English language bias (~90% training data)",
            "Western cultural perspectives overrepresented",
            "Recency bias - limited post-2021 knowledge",
            "Academic and formal writing style bias"
        ],
        "risks": [
            {"severity": "high", "text": "No data lineage available for audit"},
            {"severity": "high", "text": "Cannot verify training data consent/licensing"},
            {"severity": "medium", "text": "Temporal data limitations (knowledge cutoff)"},
            {"severity": "medium", "text": "Geographic/cultural bias in outputs"}
        ],
        "compliance": {
            "gdpr": "Data processing addendum available",
            "euAiAct": "Self-identifies as general purpose AI",
            "licensing": "Prohibits certain use cases (weapons, surveillance, etc.)"
        },
        "dueDiligenceQuestions": [
            "What proportion of training data comes from each source category?",
            "How do you handle copyrighted material in training data?",
            "What demographic representation exists in your training data?",
            "Can you provide data lineage for specific model outputs?",
            "What is your process for removing problematic training data?"
        ],
        "lastUpdated": "2024-12-01",
        "documentationUrl": "https://openai.com/research/gpt-4"
    },
    {
        "id": "anthropic-claude",
        "name": "Anthropic Claude",
        "aliases": ["anthropic", "claude", "claude-3", "claude-3.5", "claude sonnet", "claude opus"],
        "logo": "🔶",
        "category": "Large Language Model",
        "trainingData": {
            "sources": "Web crawl, licensed datasets, books, synthetic data",
            "cutoffDate": "Early 2024 (Claude 3.5), August 2024 (Claude 3.5 Sonnet new)",
            "geographicCoverage": "Global with English focus",
            "knownDatasets": "Undisclosed proprietary mix"
        },
        "transparency": {
            "level": "Low-Medium",
            "details": "Limited disclosure of training data sources; publishes model cards",
            "dataLineage": False,
            "auditability": False
        },
        "knownBiases": [
            "English language dominant in training",
            "Constitutional AI training may affect certain viewpoints",
            "Western ethical frameworks emphasized",
            "More cautious/conservative outputs by design"
        ],
        "risks": [
            {"severity": "high", "text": "Limited training data transparency"},
            {"severity": "medium", "text": "Cannot audit data provenance"},
            {"severity": "medium", "text": "Constitutional AI approach may introduce specific biases"},
            {"severity": "low", "text": "Regular updates may change model behavior"}
        ],
        "compliance": {
            "gdpr": "DPA available, EU data residency options",
            "euAiAct": "Preparing for compliance",
            "licensing": "Commercial use permitted with restrictions"
        },
        "dueDiligenceQuestions": [
            "What is the breakdown of training data sources?",
            "How does Constitutional AI training affect outputs for my use case?",
            "What processes exist for training data quality control?",
            "Can you provide demographic breakdowns of training data?",
            "How do you handle copyrighted content in training?"
        ],
        "lastUpdated": "2024-12-01",
        "documentationUrl": "https://www.anthropic.com/claude"
    },
    {
        "id": "google-gemini",
        "name": "Google Gemini",
        "aliases": ["google", "gemini", "bard", "google ai", "gemini pro", "gemini ultra"],
        "logo": "✨",
        "category": "Multimodal AI",
        "trainingData": {
            "sources": "Web crawl, Google products data, licensed content, multimodal data",
            "cutoffDate": "April 2024 (varies by model version)",
            "geographicCoverage": "Global, multilingual",
            "knownDatasets": "YouTube, Google Search, Google Books, undisclosed web data"
        },
        "transparency": {
            "level": "Medium",
            "details": "Some disclosure in technical reports; leverages Google ecosystem data",
            "dataLineage": False,
            "auditability": False
        },
        "knownBiases": [
            "Google product ecosystem overrepresentation",
            "Search ranking biases may affect training data",
            "YouTube content biases",
            "Multiple languages but English-dominant"
        ],
        "risks": [
            {"severity": "high", "text": "Unclear separation between user data and training data"},
            {"severity": "high", "text": "YouTube training data may include problematic content"},
            {"severity": "medium", "text": "Google ecosystem creates unique bias patterns"},
            {"severity": "medium", "text": "Rapid iteration may affect consistency"}
        ],
        "compliance": {
            "gdpr": "Google Cloud DPA applies",
            "euAiAct": "Working toward compliance",
            "licensing": "Terms of service restrict certain applications"
        },
        "dueDiligenceQuestions": [
            "What Google user data is included in training?",
            "How is consent obtained for training data from Google products?",
            "What content moderation exists for YouTube training data?",
            "Can you separate model versions by training data source?",
            "What is your data retention and model retraining policy?"
        ],
        "lastUpdated": "2024-12-01",
        "documentationUrl": "https://deepmind.google/technologies/gemini/"
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "aliases": ["cohere", "cohere ai", "command", "command-r"],
        "logo": "🌊",
        "category": "Large Language Model",
        "trainingData": {
            "sources": "Web crawl, curated datasets, enterprise data (with permission)",
            "cutoffDate": "Varies by model; regularly updated",
            "geographicCoverage": "Global, multilingual focus",
            "knownDatasets": "Proprietary curation, emphasis on quality filtering"
        },
        "transparency": {
            "level": "Medium",
            "details": "More transparent about enterprise data handling; publishes model cards",
            "dataLineage": True,
            "auditability": True
        },
        "knownBiases": [
            "Curated data may introduce selection bias",
            "Enterprise focus may affect general knowledge",
            "Multilingual but quality varies by language",
            "Business content overrepresented"
        ],
        "risks": [
            {"severity": "medium", "text": "Data curation methodology not fully disclosed"},
            {"severity": "medium", "text": "Enterprise data mixing may create conflicts"},
            {"severity": "low", "text": "Better data lineage than competitors"},
            {"severity": "low", "text": "Regular updates require version tracking"}
        ],
        "compliance": {
            "gdpr": "Full DPA, data residency options",
            "euAiAct": "Active compliance preparation",
            "licensing": "Flexible commercial licensing"
        },
        "dueDiligenceQuestions": [
            "What is your data curation methodology?",
            "How do you separate enterprise customer data from model training?",
            "Can you provide data lineage for my specific deployment?",
            "What language-specific biases exist in multilingual models?",
            "What are your data refresh and versioning practices?"
        ],
        "lastUpdated": "2024-12-01",
        "documentationUrl": "https://cohere.com/"
    },
    {
        "id": "huggingface",
        "name": "Hugging Face (Hosted Models)",
        "aliases": ["huggingface", "hugging face", "hf", "transformers"],
        "logo": "🤗",
        "category": "Model Repository/Inference",
        "trainingData": {
            "sources": "Varies by model - community uploaded",
            "cutoffDate": "Model-dependent",
            "geographicCoverage": "Model-dependent",
            "knownDatasets": "Highly variable - check individual model cards"
        },
        "transparency": {
            "level": "High",
            "details": "Model cards required; community driven; variable quality",
            "dataLineage": True,
            "auditability": True
        },
        "knownBiases": [
            "Biases vary dramatically by model",
            "Community models may lack thorough bias testing",
            "Documentation quality inconsistent",
            "Older models may have outdated practices"
        ],
        "risks": [
            {"severity": "high", "text": "Quality and safety vary dramatically by model"},
            {"severity": "high", "text": "Some models lack proper documentation"},
            {"severity": "medium", "text": "Community models may not be maintained"},
            {"severity": "low", "text": "Transparency generally better than commercial options"}
        ],
        "compliance": {
            "gdpr": "User responsible for compliance",
            "euAiAct": "User responsible for compliance",
            "licensing": "Varies by model - check individual licenses"
        },
        "dueDiligenceQuestions": [
            "Does this specific model have a complete model card?",
            "Who trained this model and what is their reputation?",
            "What training data was used for this specific model?",
            "Has this model been evaluated for bias?",
            "Is this model actively maintained?",
            "What is the license for this model?"
        ],
        "lastUpdated": "2024-12-01",
        "documentationUrl": "https://huggingface.co/"
    }
]


def find_matching_vendors(user_input):
    """Match user input against vendor database and return matching vendors."""
    if not user_input:
        return []
    
    user_input_lower = user_input.lower()
    matched_vendors = []
    
    for vendor in VENDOR_DATABASE:
        # Check if any alias matches
        for alias in vendor.get("aliases", []):
            if alias.lower() in user_input_lower:
                matched_vendors.append(vendor)
                break
        else:
            # Also check the vendor name
            if vendor["name"].lower() in user_input_lower:
                matched_vendors.append(vendor)
    
    return matched_vendors


def calculate_vendor_risk_score(vendors):
    """Calculate a risk score based on matched vendors."""
    if not vendors:
        return None
    
    total_high = 0
    total_medium = 0
    total_low = 0
    
    for vendor in vendors:
        for risk in vendor.get("risks", []):
            if risk["severity"] == "high":
                total_high += 1
            elif risk["severity"] == "medium":
                total_medium += 1
            elif risk["severity"] == "low":
                total_low += 1
    
    # Calculate risk score (lower is worse)
    # High risks deduct 10 points, medium 5, low 2
    base_score = 100
    score = base_score - (total_high * 10) - (total_medium * 5) - (total_low * 2)
    return max(0, min(100, score))


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
- Third-party models, APIs, or vendors and their risks:
  - Review the detected vendor risk profiles provided (transparency level, high/medium risk counts)
  - Factor vendor transparency and risk levels into the overall assessment
  - Highlight any vendor-specific concerns that affect governance readiness
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

---

INTERNAL SCORING METHODOLOGY (use these rules to calculate, do not display in output):
- External Harm Risk (0-30 pts): Low=30, Medium=15, High=5
- Internal Failure Risk (0-20 pts): Low=20, Medium=10, High=5
- Regulatory Sensitivity (0-20 pts): Low=20, Medium=10, High=5
- Data & Legal Soundness (0-20 pts): Excellent=20, Moderate=10, Weak=5
- Purpose & MVP Clarity (0-10 pts): Strong=10, Moderate=5, Weak=2

Return the scores in this EXACT format at the end of your response (this JSON block will be hidden from display):
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

        # Find matching vendors from third_parties input
        matched_vendors = find_matching_vendors(third_parties)
        vendor_risk_score = calculate_vendor_risk_score(matched_vendors)
        
        # Build vendor summary for GPT
        vendor_summary = ""
        if matched_vendors:
            vendor_lines = []
            for v in matched_vendors:
                high_risks = sum(1 for r in v.get("risks", []) if r["severity"] == "high")
                medium_risks = sum(1 for r in v.get("risks", []) if r["severity"] == "medium")
                vendor_lines.append(
                    f"- {v['name']} (Transparency: {v['transparency']['level']}, "
                    f"High Risks: {high_risks}, Medium Risks: {medium_risks})"
                )
            vendor_summary = "\n".join(vendor_lines)
        else:
            vendor_summary = "No known vendors detected"

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
Detected vendor risk profiles:
{vendor_summary}
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
            session['vendors'] = matched_vendors
            session['vendor_risk_score'] = vendor_risk_score
            session['error'] = None
        except Exception as e:
            session['error'] = f"An error occurred while calling the API: {str(e)}"
            session['result'] = None
            session['scores'] = None
            session['vendors'] = matched_vendors
            session['vendor_risk_score'] = vendor_risk_score

        return redirect(url_for('results'))

    return render_template("index.html")


@app.route("/results")
def results():
    result = session.pop('result', None)
    error = session.pop('error', None)
    scores = session.pop('scores', None)
    vendors = session.pop('vendors', [])
    vendor_risk_score = session.pop('vendor_risk_score', None)
    
    if result:
        result = Markup(result)
    
    if not result and not error:
        return redirect(url_for('index'))
    
    return render_template("results.html", result=result, error=error, scores=scores, 
                          vendors=vendors, vendor_risk_score=vendor_risk_score)


if __name__ == "__main__":
    # On Replit, host/port are usually handled for you, but this is safe:
    app.run(host="0.0.0.0", port=5000, debug=True)
