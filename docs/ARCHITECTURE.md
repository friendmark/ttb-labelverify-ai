# Architecture

## Design goals
1. Results near the stakeholder's ~5-second usability target on ordinary label images.
2. Simple workflow for users with mixed technical comfort.
3. Explainable findings rather than an opaque model verdict.
4. Minimal outbound dependencies because stakeholder notes identify restrictive network egress.
5. Separation of OCR/perception from compliance policy logic.

## Components
- **Streamlit UI:** application fields, upload, results and error handling.
- **Image preprocessing:** EXIF correction, grayscale, autocontrast and sharpening.
- **OCR:** local Tesseract via `pytesseract`.
- **Compliance engine:** normalization, fuzzy textual comparison, numeric ABV comparison, net-content parsing, and health-warning content coverage.

## Future production path
A production implementation could place the same rule engine behind an authenticated API and agency-approved UI, add layout-aware computer vision, beverage-specific policy packs, batch queues, audit logging, human overrides, model/rule versioning, and formal evaluation datasets.
