# Security Notes

This is a non-production proof-of-concept intended for non-sensitive test labels.

## Implemented
- Image type allow-list and Pillow validation.
- 10 MB UI upload limit.
- No shell execution or user-controlled filesystem paths.
- No required external AI API or embedded credentials.
- Generic user-facing exception handling.

## Production considerations
A federal production deployment would require a formal authorization path and controls appropriate to the system categorization, including identity/access management, encryption, centralized audit logging, dependency/SBOM management, vulnerability scanning, retention/disposal controls, privacy review, accessibility testing, incident response integration, and approved cloud/service dependencies.

OCR output is untrusted input and should remain data, never executable instructions. If a future LLM is introduced, label text must be treated as untrusted content and protected against prompt injection and data exfiltration.
