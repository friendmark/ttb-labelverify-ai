# Assumptions and Limitations

- Expected application values are entered manually because COLA integration is explicitly out of scope for the prototype.
- The distilled-spirits example is the primary V1 path; beverage-specific rule packs should be added before broader use.
- Semantic normalization is appropriate for fields such as brand capitalization/punctuation, but numeric fields use stricter comparisons.
- Government-warning textual content is checked conservatively. Visual typography requirements are not asserted as automatically verified in V1.
- OCR quality depends on resolution, glare, curvature, orientation and contrast. Low-confidence/unreadable cases should be routed to a human rather than guessed.
- The application is decision support, not an approval authority.
