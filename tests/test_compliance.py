from app.rules.compliance import fuzzy_match, extract_abv, extract_proof, extract_net_contents, warning_similarity, evaluate, STANDARD_WARNING

def test_brand_case_and_punctuation():
    ok, _ = fuzzy_match("Stone's Throw", "STONE'S THROW")
    assert ok

def test_expected_phrase_can_be_found_inside_full_ocr():
    ok, _ = fuzzy_match("Old Tom Distillery", "OTHER TEXT OLD TOM DISTILLERY 45% ABV")
    assert ok

def test_abv():
    assert extract_abv("45% Alc./Vol. (90 Proof)") == 45.0

def test_proof():
    assert extract_proof("45% Alc./Vol. (90 Proof)") == 90.0

def test_net_contents():
    assert extract_net_contents("NET CONTENTS 750 mL").upper() == "750 ML"

def test_warning_similarity_exact():
    assert warning_similarity(STANDARD_WARNING) > .98

def test_proof_consistency_failure():
    findings = evaluate("45% ABV 100 Proof " + STANDARD_WARNING, {"abv":"45"})
    proof = next(f for f in findings if f.field == "ABV / Proof Consistency")
    assert proof.status == "FAIL"

def test_low_ocr_confidence_escalates():
    findings = evaluate(STANDARD_WARNING, {}, ocr_confidence=.4, quality_score=.9)
    assert any(f.field == "Image / OCR Quality" and f.status == "REVIEW" for f in findings)
