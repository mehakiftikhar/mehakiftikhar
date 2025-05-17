# 📁 File: agentic_form_collector.py

import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

st.set_page_config(page_title="Agentic Form Field Collector", layout="centered")
st.title("🤖📄 Agentic Form Field Collector")
st.markdown("Upload a form (PDF — scanned or text-based). Agent will extract missing fields and prompt you to fill them.")

# ---- Upload PDF ----
pdf_file = st.file_uploader("📤 Upload your form (PDF only)", type=["pdf"])

def extract_text_pymupdf_all_pages(path):
    doc = fitz.open(path)
    full_text = ""
    for page_num, page in enumerate(doc):
        page_text = page.get_text()
        full_text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
    return full_text.strip()

def extract_text_ocr_all_pages(path):
    doc = fitz.open(path)
    text = ""
    for page_index in range(len(doc)):
        images = doc[page_index].get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            text += f"\n\n--- Page {page_index + 1} Image {img_index + 1} ---\n"
            text += pytesseract.image_to_string(image)
    return text.strip()

def extract_fields(text):
    lines = text.split("\n")
    field_pattern = re.compile(r"([A-Za-z0-9\s\-_/]+)\s*[:\-–]\s*")
    fields = []

    for line in lines:
        matches = field_pattern.findall(line)
        for match in matches:
            cleaned = match.strip()
            if 2 < len(cleaned) < 40:
                fields.append(cleaned)

    return list(set(fields))

# ---- Process PDF ----
if pdf_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    with st.spinner("🔍 Reading form (multi-page)..."):
        text = extract_text_pymupdf_all_pages("temp.pdf")

    if not text or len(text.strip()) < 50:
        st.warning("⚠️ Not enough text found. Trying OCR on embedded images...")
        with st.spinner("🧠 Performing OCR on all pages..."):
            text = extract_text_ocr_all_pages("temp.pdf")

    if not text:
        st.error("❌ No readable text could be extracted from this file.")
    else:
        fields = extract_fields(text)

        if not fields:
            st.warning("⚠️ No field-like text (e.g. `Name:`, `DOB:`) found.")
        else:
            st.success(f"✅ Extracted {len(fields)} fields from the form!")
            st.markdown("### ✍️ Please fill in the required fields:")

            user_inputs = {}
            for field in fields:
                lower = field.lower()
                if "date" in lower:
                    date = st.date_input(field)
                    user_inputs[field] = str(date)
                elif "photo" in lower or "image" in lower:
                    image = st.file_uploader(f"{field} (Upload JPG/PNG)", type=["jpg", "jpeg", "png"])
                    user_inputs[field] = image.name if image else None
                else:
                    text_input = st.text_input(f"{field}", placeholder=f"Enter your {field}")
                    user_inputs[field] = text_input

            if st.button("📨 Submit Information"):
                st.success("✅ Info Collected Successfully!")
                st.json(user_inputs)
