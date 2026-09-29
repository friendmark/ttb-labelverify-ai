# TTB LabelVerify AI

A standalone proof-of-concept for AI-assisted alcohol beverage label verification, created in response to the U.S. Treasury take-home assessment. The application extracts text from label artwork and compares key fields against application data using explainable, deterministic rules.

> Prototype decision support only. It does not make a final TTB regulatory determination.

## Live prototype

**Deployed application:** https://ttb-labelverify-ai.onrender.com

The public prototype can be tested directly in a browser. Because it is hosted on a free Render instance, the first request after a period of inactivity may require additional startup time.

## Automated testing

Automated tests run through GitHub Actions on pushes and pull requests to `main`. The workflow uses Python 3.11, installs the project dependencies, and executes the test suite with `pytest`.

## Core capabilities

- Upload PNG/JPEG/WebP label artwork.
- OCR with local Tesseract; no generative-AI API is required for the core path.
- Compare brand, class/type, ABV, net contents, producer/bottler, and country of origin when supplied.
- Check for the statutory government-warning text using OCR-tolerant matching.
- Return PASS / REVIEW REQUIRED / FAIL findings with evidence and processing time.
- Validate uploads and fail safely on unreadable/invalid input.

## Architecture

`Browser → Streamlit UI → image preprocessing → Tesseract OCR → field/rule evaluation → explainable findings`

AI/OCR is used for the fuzzy perception problem. Deterministic code is used for regulatory comparisons. This reduces hallucination risk and makes findings auditable.

## Setup

### Prerequisites

- Python 3.11+
- Tesseract OCR installed and available on `PATH`

### Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

### Tests

```bash
pytest -q
```

## Assumptions and trade-offs

- The prototype is optimized first for the distilled-spirits example in the assessment, while the rule layer is designed to be extended for wine and malt beverages.
- OCR can verify text content, but this version does **not** claim reliable automated verification of physical font size, boldness, contrast, or placement from arbitrary photographs. Those attributes are escalated to human review.
- No COLA integration is attempted, per the assessment context.
- No uploaded document is intentionally persisted by application code.
- Batch processing is a logical next increment after the single-label core is validated.

## Security considerations

- File extensions are allow-listed and image content is validated with Pillow.
- Uploads are limited to 10 MB in the UI.
- The core path requires no API keys or outbound ML endpoint.
- Secrets are excluded by `.gitignore`.
- Production deployment would require agency-approved hosting, authorization, logging/retention controls, accessibility review, vulnerability management, privacy assessment, and appropriate federal security controls.

See `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, and `docs/ASSUMPTIONS.md`.

## Deployment

### Docker

```bash
docker build -t ttb-labelverify-ai .
docker run --rm -p 8501:8501 ttb-labelverify-ai
```

Then open `http://localhost:8501`.

### Hosted prototype

The repository includes `render.yaml` for a Docker-based Render deployment and `packages.txt` for platforms that support system-package installation. Tesseract must be present in the deployed runtime. Before submitting a public URL, test the application from a browser that is not signed into the hosting account.

## Verification logic

The prototype deliberately separates perception from policy logic:

- **OCR / perception:** local Tesseract extracts text and word-level confidence.
- **Quality gate:** basic resolution, brightness, contrast, and OCR-confidence checks identify inputs that should be routed to a human.
- **Field checks:** application values are normalized and compared against extracted text.
- **Numeric checks:** ABV is compared numerically; if proof is also present, the prototype checks that proof is approximately twice ABV.
- **Health warning:** OCR text is compared with the statutory warning, but typography and physical presentation remain a human-review item because arbitrary photographs do not provide a reliable physical scale.

## Current scope

Version 2 prioritizes the single-label distilled-spirits workflow. It does not claim automated verification of same-field-of-vision placement, physical type size, bold styling, or contrast. Those are documented production extensions rather than silently inferred.
