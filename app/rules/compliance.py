import re
from dataclasses import dataclass
from difflib import SequenceMatcher

STANDARD_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or operate "
    "machinery, and may cause health problems."
)

@dataclass
class Finding:
    field: str
    expected: str
    detected: str
    status: str
    detail: str


def norm(value: str) -> str:
    value = (value or "").upper().replace("’", "'")
    return re.sub(r"[^A-Z0-9]+", " ", value).strip()


def fuzzy_match(expected: str, detected: str, threshold: float = .88):
    if not expected:
        return True, 1.0

    a = norm(expected)
    b = norm(detected)

    if not a:
        return True, 1.0

    # Exact normalized phrase found anywhere in OCR text.
    if a in b:
        return True, 1.0

    # Compare the expected value against similarly sized word windows.
    # This handles OCR line breaks and surrounding unrelated label text.
    expected_words = a.split()
    detected_words = b.split()
    window_size = len(expected_words)

    best_score = SequenceMatcher(None, a, b).ratio() if b else 0.0

    if window_size and len(detected_words) >= window_size:
        for extra in (0, 1, 2):
            size = window_size + extra
            if size > len(detected_words):
                continue

            for i in range(len(detected_words) - size + 1):
                candidate = " ".join(detected_words[i:i + size])
                score = SequenceMatcher(None, a, candidate).ratio()
                best_score = max(best_score, score)

    return best_score >= threshold, best_score


def extract_abv(text: str):
    patterns = [r"(\d{1,2}(?:\.\d+)?)\s*%\s*(?:ALC(?:OHOL)?\.?\s*/?\s*VOL(?:UME)?\.?|ABV)", r"ALCOHOL\s+(\d{1,2}(?:\.\d+)?)\s*%"]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m: return float(m.group(1))
    return None


def extract_proof(text: str):
    m = re.search(r"\b(\d{1,3}(?:\.\d+)?)\s*PROOF\b", text, re.I)
    return float(m.group(1)) if m else None


def extract_net_contents(text: str):
    # Tolerate common OCR spacing and punctuation variations such as
    # "750 mL", "750ml", "750 m L", and "750 ML".
    patterns = [
        r"\b(\d+(?:[.,]\d+)?)\s*M\s*L\b",
        r"\b(\d+(?:[.,]\d+)?)\s*C\s*L\b",
        r"\b(\d+(?:[.,]\d+)?)\s*(LITERS?|LITRES?)\b",
        r"\b(\d+(?:[.,]\d+)?)\s*L\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            value = match.group(1).replace(",", ".")

            if re.search(r"M\s*L", match.group(0), re.I):
                unit = "mL"
            elif re.search(r"C\s*L", match.group(0), re.I):
                unit = "cL"
            else:
                unit = "L"

            return f"{value} {unit}"

    return ""


def warning_similarity(text: str):
    required, observed = norm(STANDARD_WARNING), norm(text)
    # Compare against a window beginning at GOVERNMENT WARNING when possible.
    pos = observed.find("GOVERNMENT WARNING")
    candidate = observed[pos:pos+len(required)+100] if pos >= 0 else observed
    return SequenceMatcher(None, required, candidate).ratio()


def evaluate(text: str, expected: dict, ocr_confidence: float = 1.0, quality_score: float = 1.0):
    findings = []
    for key, label in [("brand", "Brand Name"), ("class_type", "Class / Type"), ("producer", "Producer / Bottler"), ("country", "Country of Origin")]:
        exp = expected.get(key, "").strip()
        if not exp: continue
        ok, score = fuzzy_match(exp, text)
        status = "PASS" if ok else "REVIEW"
        findings.append(Finding(label, exp, "Detected in OCR text" if ok else "Not confidently detected", status, f"Normalized text match: {score:.0%}."))

    exp_abv = expected.get("abv")
    got_abv = extract_abv(text)
    if exp_abv not in (None, ""):
        try: exp = float(exp_abv); ok = got_abv is not None and abs(exp-got_abv) < .01
        except ValueError: ok = False
        findings.append(Finding("Alcohol Content", f"{exp_abv}% ABV", f"{got_abv}% ABV" if got_abv is not None else "Not detected", "PASS" if ok else "FAIL", "Exact numeric comparison of application and label ABV."))

    proof = extract_proof(text)
    if proof is not None and got_abv is not None:
        delta = abs(proof - (2 * got_abv))
        findings.append(Finding("ABV / Proof Consistency", f"Proof ≈ {2*got_abv:g}", f"{proof:g} Proof", "PASS" if delta <= .1 else "FAIL", "Proof should be approximately twice ABV when both are displayed."))

    exp_net = expected.get("net_contents", "").strip()
    if exp_net:
        got = extract_net_contents(text); ok, score = fuzzy_match(exp_net, got, .95)
        findings.append(Finding("Net Contents", exp_net, got or "Not detected", "PASS" if ok else "FAIL", f"Normalized match: {score:.0%}."))

    similarity = warning_similarity(text)
    if similarity >= .94: status = "REVIEW"
    elif similarity >= .75: status = "REVIEW"
    else: status = "FAIL"
    findings.append(Finding("Government Health Warning", "Statutory warning text", "Warning text detected" if similarity >= .75 else "Warning incomplete/not detected", status, f"OCR text similarity: {similarity:.0%}. Exact wording, punctuation, bold/caps, type size, contrast, separation, and continuous-paragraph presentation require visual verification."))

    if ocr_confidence < .65 or quality_score < .60:
        findings.append(Finding("Image / OCR Quality", "Sufficient for reliable automated screening", f"OCR confidence {ocr_confidence:.0%}; quality score {quality_score:.0%}", "REVIEW", "Low-confidence extraction should be routed to a human reviewer rather than treated as a definitive mismatch."))
    return findings
