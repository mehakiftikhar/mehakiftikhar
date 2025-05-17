# 📁 File: agentic_form_collector.py

import streamlit as st
import fitz  # PyMuPDF
import easyocr
import numpy as np
from PIL import Image
import io
import re

# --- Streamlit UI setup ---
st.set_page_config(page_title="Agentic Form Field Collector", layout="centered")
st.title("🤖📄 Agentic Form Field Collector")
st.markdown("Upload a form (PDF — scanned or text-based). Agent will extract fillable fields and prompt you to complete them.")

# --- File uploader ---
pdf_file = st.file_uploader("📤 Upload your form (PDF only)", type=["pdf"])

# --- EasyOCR reader ---
reader = easyocr.Reader(['en'], gpu=False)

# --- Text-based PDF reader ---
def extract_text_pymupdf_all_pages(path):
    doc = fitz.open(path)
    full_text = ""
    for page_num, page in enumerate(doc):
        page_text = page.get_text()
        full_text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
    return full_text.strip()

# --- OCR from scanned images in PDF ---
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
            result = reader.readtext(np.array(image), detail=0)
            text += f"\n\n--- Page {page_index + 1} Image {img_index + 1} ---\n" + "\n".join(result)
    return text.strip()

# --- Extract fillable logical fields ---
def extract_fields(text):
    allowed_keywords = [
        "name", "dob", "birth", "date", "address", "email", "phone", 
        "mobile", "number", "cnic", "id", "gender", "nationality", 
        "city", "father", "mother", "guardian", "occupation", "religion"
    ]
    banned_keywords = ["page", "info", "section", "form", "table", "instructions", "code"]

    lines = text.lower().split("\n")
    fields = []

    for line in lines:
        if ":" in line or "-" in line:
            if any(bad in line for bad in banned_keywords):
                continue
            if any(ok in line for ok in allowed_keywords):
                match = re.split(r'[:\-]', line)[0].strip().title()
                if 2 < len(match) < 40 and match not in fields:
                    fields.append(match)

    return fields

# --- Main Logic ---
if pdf_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    with st.spinner("🔍 Reading form (multi-page)..."):
        text = extract_text_pymupdf_all_pages("temp.pdf")

    if not text or len(text.strip()) < 50:
        st.warning("⚠️ Not enough text found. Trying OCR on scanned images...")
        with st.spinner("🧠 Performing OCR..."):
            text = extract_text_ocr_all_pages("temp.pdf")

    if not text:
        st.error("❌ No readable text could be extracted from this file.")
    else:
        fields = extract_fields(text)

        if not fields:
            st.warning("⚠️ No fillable fields like 'Name:', 'DOB:', etc. were found.")
        else:
            st.success(f"✅ {len(fields)} fillable fields found!")
            st.markdown("### ✍️ Please provide your information:")

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
                st.success("✅ Information collected successfully!")
                st.json(user_inputs)
