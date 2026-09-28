import time
from PIL import Image
import streamlit as st
from app.services.ocr import extract_text
from app.rules.compliance import evaluate

st.set_page_config(page_title="TTB LabelVerify AI", page_icon="🔎", layout="wide")
st.title("TTB LabelVerify AI")
st.caption("AI-assisted alcohol beverage label verification • Prototype decision-support tool")
st.info("Screening aid only — findings require reviewer judgment and do not constitute a final TTB regulatory determination.")

with st.sidebar:
    st.header("Application Data")
    brand = st.text_input("Brand name", "OLD TOM DISTILLERY")
    class_type = st.text_input("Class / type", "Kentucky Straight Bourbon Whiskey")
    abv = st.text_input("ABV (%)", "45")
    net = st.text_input("Net contents", "750 mL")
    producer = st.text_input("Producer / bottler (optional)")
    country = st.text_input("Country of origin (imports only)")

uploaded = st.file_uploader("Upload label artwork", type=["png", "jpg", "jpeg", "webp"], help="PNG, JPEG, or WebP; maximum 10 MB. Use non-sensitive test data.")
if uploaded:
    if uploaded.size > 10 * 1024 * 1024:
        st.error("File is larger than the 10 MB prototype limit."); st.stop()
    try:
        image = Image.open(uploaded); image.verify(); uploaded.seek(0); image = Image.open(uploaded).convert("RGB")
    except Exception:
        st.error("The uploaded file could not be validated as an image."); st.stop()
    left, right = st.columns([1, 1])
    with left: st.image(image, caption="Uploaded label", use_container_width=True)
    with right:
        st.subheader("Review workflow")
        st.write("1. Extract label text locally\n2. Compare application fields\n3. Apply deterministic checks\n4. Escalate uncertainty for human review")
    if st.button("Analyze Label", type="primary", use_container_width=True):
        start = time.perf_counter()
        try:
            ocr = extract_text(image)
            expected = {"brand":brand,"class_type":class_type,"abv":abv,"net_contents":net,"producer":producer,"country":country}
            findings = evaluate(ocr.text, expected, ocr.confidence, ocr.quality_score)
            elapsed = time.perf_counter() - start
            statuses = [f.status for f in findings]
            overall = "FAIL" if "FAIL" in statuses else "REVIEW REQUIRED" if "REVIEW" in statuses else "PASS"
            st.header(f"Overall screening result: {overall}")
            a,b,c = st.columns(3)
            a.metric("Processing time", f"{elapsed:.2f} s", help="Stakeholder target: approximately 5 seconds.")
            b.metric("OCR confidence", f"{ocr.confidence:.0%}")
            c.metric("Image quality", f"{ocr.quality_score:.0%}")
            if elapsed > 5: st.warning("Processing exceeded the approximately five-second stakeholder target on this run.")
            for note in ocr.quality_notes: st.caption(note)
            for f in findings:
                icon = {"PASS":"✅","FAIL":"❌","REVIEW":"⚠️"}[f.status]
                with st.expander(f"{icon} {f.field} — {f.status}", expanded=f.status != "PASS"):
                    st.write("**Expected:**", f.expected); st.write("**Detected:**", f.detected); st.write(f.detail)
            with st.expander("Extracted OCR text"):
                st.code(ocr.text or "No text detected.")
        except RuntimeError as exc: st.error(str(exc))
        except Exception: st.error("Analysis failed safely. Please try a clearer image or review the application logs.")
