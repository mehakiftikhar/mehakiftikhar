# agentic_form_collector.py

import streamlit as st
import fitz               # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from typing import List

st.set_page_config(page_title="Agentic Form Collector", layout="centered")
st.title("🧾 Agentic Form Collector")
st.markdown(
    "Upload any form (fillable or scanned). "
    "Our agent will detect missing fields and ask you to fill them."
)

# 1️⃣ Upload PDF
uploaded = st.file_uploader("Upload your PDF form", type=["pdf"])
if not uploaded:
    st.stop()

# Save to a temp file
with open("temp_form.pdf", "wb") as f:
    f.write(uploaded.read())
pdf_path = "temp_form.pdf"


# 2️⃣ Extract fillable fields (AcroForm)
def extract_fillable_fields(path: str) -> List[str]:
    doc = fitz.open(path)
    names = []
    for page in doc:
        for widget in page.widgets() or []:
            if widget.field_name:
                names.append(widget.field_name.strip())
    return list(dict.fromkeys(names))


# 3️⃣ If no fillable fields, fallback to OCR text headings
def extract_fields_via_ocr(path: str) -> List[str]:
    # very basic heuristic: take each line as a potential field
    pages = convert_from_path(path)
    text = ""
    for img in pages:
        text += pytesseract.image_to_string(img) + "\n"
    # split lines, keep short ones as “fields”
    candidates = [line.strip() for line in text.splitlines() if 3 < len(line) < 40]
    # dedupe and return top 10
    seen, fields = set(), []
    for line in candidates:
        if line not in seen:
            seen.add(line)
            fields.append(line)
        if len(fields) >= 10:
            break
    return fields


# gather fields
fields = extract_fillable_fields(pdf_path)
if not fields:
    st.info("No interactive fields found; using OCR to detect labels…")
    fields = extract_fields_via_ocr(pdf_path)

st.markdown("**Detected fields:**  " + ", ".join(fields))

# 4️⃣ Ask user to fill each detected field
user_data = {}
for field in fields:
    lf = field.lower()
    if "date" in lf:
        val = st.date_input(field, key=field)
        user_data[field] = str(val)
    elif any(k in lf for k in ("photo", "image", "file")):
        up = st.file_uploader(f"{field} (upload image)", type=["jpg","png","jpeg"], key=field)
        user_data[field] = up
    else:
        user_data[field] = st.text_input(field, key=field)

# 5️⃣ Submit and show collected data
if st.button("📨 Submit Missing Info"):
    st.success("✅ Collected the following information:")
    st.json(user_data)
    # Here you could call your PDF-filling function and pass `user_data`
    # e.g. filled_path = fill_pdf("temp_form.pdf", "filled.pdf", user_data)
    # and then st.download_button(...) for the filled result.
