# AI Governance Ideation Assistant

## Overview

This is a Flask-based web application that helps early-stage startups evaluate whether their proposed AI systems should be built from a governance perspective. The tool guides users through a 4-step wizard to assess AI initiatives during the ideation phase, covering system intake, purpose clarity, legal/data foundations, and stakeholder impact analysis. It uses OpenAI's API to generate governance evaluations based on structured form inputs and provides actionable recommendations (GO/GO WITH CONDITIONS/NO-GO).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Multi-step Form Wizard Pattern**
- The application implements a 4-step wizard interface to collect governance information progressively
- Each step is rendered as a separate template (step1.html through step4.html) extending a base template
- Step indicator dots provide visual feedback on progress through the wizard
- Form data is accumulated across steps using Flask sessions
- *Rationale*: Breaking complex governance assessment into digestible chunks reduces cognitive load and improves completion rates for non-technical startup founders

**Template Inheritance Strategy**
- Uses Jinja2 template inheritance with a base.html layout
- Consistent header/branding across all pages through the base template
- Block-based content injection for step indicators and main content
- *Rationale*: DRY principle, easier maintenance, consistent UX

**CSS Design System**
- Custom CSS with CSS variables for theming (cyan/seafoam color palette)
- Gradient backgrounds and card-based layouts
- Responsive grid system for form fields
- *Alternatives considered*: Could use a CSS framework like Tailwind or Bootstrap, but custom CSS provides smaller footprint and precise control for this focused use case

### Backend Architecture

**Flask Application Structure**
- Simple monolithic Flask application in main.py
- Session-based state management for wizard flow
- Route handlers for each step + results page
- *Rationale*: Lightweight framework appropriate for MVP; no need for complex routing or ORM at this stage

**AI Integration Pattern**
- OpenAI API integration for governance evaluation
- Compressed governance prompt (BASE_PROMPT) defines evaluation framework
- Structured markdown output format enforced through prompt engineering
- The AI evaluates across 6 key mechanisms: intake, purpose assessment, legal foundations, stakeholder analysis, impact triage, and feasibility gating
- *Rationale*: Leverages LLM reasoning capabilities to provide expert-level governance guidance without requiring human governance experts on staff

**Vendor Risk Profiling**
- Built-in database (VENDOR_DATABASE) with 5 major AI vendors: OpenAI GPT-4, Anthropic Claude, Google Gemini, Cohere, Hugging Face
- Automatic vendor detection from user input in "Third-party models/APIs/vendors" field
- Each vendor profile includes:
  - Training data provenance (sources, cutoff dates, geographic coverage, known datasets)
  - Transparency level (Low/Low-Medium/Medium/High)
  - Known biases and limitations
  - Risk flags (High/Medium/Low severity)
  - Compliance notes (GDPR, EU AI Act, licensing)
  - Due diligence questions to ask the vendor
- Vendor risk score calculation based on aggregate risk flags
- Results page displays detailed vendor cards with all provenance information
- *Rationale*: Pre-populated vendor intelligence enables accurate risk assessment without requiring users to research each AI vendor

**Deterministic Python Scoring Engine**
- Prevents AI math hallucinations by separating classification from calculation
- AI acts as "Risk Classifier" outputting only tier classifications (Low/Medium/High, etc.)
- GOVERNANCE_WEIGHTS dictionary defines point values for each tier:
  - external_impact: Low=30, Medium=15, High=5
  - internal_failure: Low=20, Medium=10, High=5
  - regulatory_sensitivity: Low=20, Medium=10, High=5
  - data_legal_soundness: Excellent=20, Moderate=10, Weak=5
  - purpose_clarity: Strong=10, Moderate=5, Weak=2
- calculate_governance_score() function performs deterministic lookup and summation
- Maximum possible score: 100 (all favorable tiers)
- *Rationale*: Python-based scoring ensures consistent, auditable results without relying on LLM arithmetic

**Session Management**
- Flask session storage for multi-step form data persistence
- Session secret key from environment variable with fallback
- Data accumulated across wizard steps and submitted to AI on final step
- *Rationale*: Server-side sessions ensure data integrity; no client-side storage reduces security risks for sensitive business information

**Markdown Rendering Pipeline**
- AI responses in markdown format
- Server-side conversion to HTML using python-markdown library
- MarkupSafe for XSS protection when rendering
- *Rationale*: Markdown provides structured, readable AI output; server-side rendering prevents injection attacks

### Data Storage Solutions

**No Database Currently Implemented**
- Application is stateless beyond session data
- No persistent storage of evaluations or user data
- *Rationale*: MVP focuses on immediate evaluation; adding persistence later would enable features like evaluation history, comparison, and iterative refinement
- *Future consideration*: Could add SQLite/PostgreSQL with Drizzle ORM for storing evaluation history, user accounts, and audit trails

### Authentication & Authorization

**No Authentication Currently Implemented**
- Open access to all wizard steps
- Session-based flow control only
- *Rationale*: MVP prioritizes functionality over access control; appropriate for internal tools or beta testing
- *Security consideration*: Production deployment should add authentication to protect proprietary AI system information

## External Dependencies

### Third-Party Services

**OpenAI API**
- Primary AI reasoning engine for governance evaluations
- Requires API key configuration via environment variable
- Processes structured form inputs and returns markdown-formatted assessments
- Used for: Evaluating AI system proposals across governance frameworks (GDPR, EU AI Act, US sectoral laws, PIPEDA, DPDP Act, PDPA)

### Python Libraries

**Flask** - Web framework
- Core application framework
- Template rendering with Jinja2
- Session management
- Request/response handling

**python-markdown** - Markdown processing
- Converts AI-generated markdown to HTML
- Enables rich formatting in evaluation results

**MarkupSafe** - XSS protection
- Safe HTML rendering
- Prevents injection attacks when displaying AI output

**OpenAI Python SDK** - API client
- Official OpenAI API wrapper
- Handles authentication and request formatting

### Environment Configuration

**Required Environment Variables**
- `SESSION_SECRET`: Flask session encryption key (defaults to "dev-secret-key" for development)
- OpenAI API key (implied by OpenAI client initialization)

**Deployment Considerations**
- Static file serving via Flask (development mode)
- No database connections required
- Minimal infrastructure needs (can run on basic PaaS)