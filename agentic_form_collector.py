# 📁 File: agentic_form_collector.py

import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

st.set_page_config(page_title="Agentic Form Field Collector", layout="centered")
st.title("🤖📄 Agentic Form Field Collector")
st.markdown("Upload a form (PDF — scanned or text-based). Agent will extract fillable fields and prompt you to fill them.")

pdf_file = st.file_uploader("📤 Upload your form (PDF only)", type=["pdf"])

# ---- Extract text from all pages ----
def extract_text_pymupdf_all_pages(path):
    doc = fitz.open(path)
    full_text = ""
    for page in doc:
        full_text += "\n" + page.get_text()
    return full_text.strip()

# ---- OCR for scanned PDFs ----
def extract_text_ocr_all_pages(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            text += "\n" + pytesseract.image_to_string(image)
    return text.strip()

# ---- Intelligent Field Extractor ----
def extract_form_fields(text):
    lines = text.split("\n")
    fields = []
    allowed_starters = [
        "name", "father", "mother", "dob", "date of birth", "birth",
        "cnic", "id", "gender", "email", "phone", "mobile",
        "address", "city", "nationality", "guardian"
    ]
    for line in lines:
        clean = line.strip().lower()

        if len(clean) < 4 or len(clean) > 60:
            continue

        if not re.search(r"[:\-]", clean):
            continue

        if clean.count(" ") > 6:
            continue  # likely not a field label

        if any(clean.startswith(w) for w in allowed_starters):
            label = re.split(r'[:\-]', clean)[0].strip().title()
            if label not in fields:
                fields.append(label)
    return fields

# ---- Main Workflow ----
if pdf_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    with st.spinner("🔍 Reading form (multi-page)..."):
        text = extract_text_pymupdf_all_pages("temp.pdf")

    if not text or len(text) < 100:
        st.warning("🧠 OCR required — processing scanned form...")
        with st.spinner("🧠 Performing OCR..."):
            text = extract_text_ocr_all_pages("temp.pdf")

    if not text:
        st.error("❌ No readable text found in the form.")
    else:
        fields = extract_form_fields(text)

        if not fields:
            st.warning("⚠️ No valid fillable fields found.")
        else:
            st.success(f"✅ Found {len(fields)} fields to fill:")
            st.markdown("### ✍️ Please enter your information:")

            user_inputs = {}
            for field in fields:
                if "date" in field.lower():
                    val = st.date_input(field)
                    user_inputs[field] = str(val)
                else:
                    val = st.text_input(field)
                    user_inputs[field] = val

            if st.button("📨 Submit Information"):
                st.success("✅ Info Collected Successfully!")
                st.json(user_inputs)
