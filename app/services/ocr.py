from dataclasses import dataclass
from statistics import mean
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

@dataclass
class OCRResult:
    text: str
    confidence: float
    quality_score: float
    quality_notes: list[str]


def preprocess(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("L")

    # Limit the working image size before OCR. Large label artwork can make
    # Tesseract unnecessarily slow on constrained deployment environments.
    max_dimension = 1200
    width, height = image.size

    if max(width, height) > max_dimension:
        scale = max_dimension / max(width, height)
        new_size = (
            max(1, int(width * scale)),
            max(1, int(height * scale)),
        )
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)
    return ImageEnhance.Contrast(image).enhance(1.25)

def assess_quality(image: Image.Image):
    gray = ImageOps.exif_transpose(image).convert("L")
    stat = ImageStat.Stat(gray)
    brightness = stat.mean[0]
    contrast = stat.stddev[0]
    w, h = gray.size
    notes, score = [], 1.0
    if min(w, h) < 500:
        score -= .25; notes.append("Low image resolution may reduce OCR accuracy.")
    if brightness < 45 or brightness > 220:
        score -= .20; notes.append("Image is unusually dark or bright.")
    if contrast < 25:
        score -= .25; notes.append("Low contrast may make label text difficult to read.")
    if not notes:
        notes.append("Basic image-quality checks passed.")
    return max(0.0, score), notes


def extract_text(image: Image.Image) -> OCRResult:
    try:
        import pytesseract
        from pytesseract import Output
        processed = preprocess(image)
        data = pytesseract.image_to_data(processed, config="--psm 11", output_type=Output.DICT)
        words, confs = [], []
        for word, conf in zip(data.get("text", []), data.get("conf", [])):
            word = (word or "").strip()
            try: c = float(conf)
            except (TypeError, ValueError): c = -1
            if word:
                words.append(word)
                if c >= 0: confs.append(c)
        text = " ".join(words)
        quality, notes = assess_quality(image)
        return OCRResult(text=text, confidence=(mean(confs)/100 if confs else 0.0), quality_score=quality, quality_notes=notes)
    except Exception as exc:
        raise RuntimeError("OCR is unavailable. Install the Tesseract executable and ensure it is on PATH.") from exc
