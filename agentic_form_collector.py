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

# ---- Upload PDF ----
pdf_file = st.file_uploader("📤 Upload your form (PDF only)", type=["pdf"])

# ---- Helper: Extract text from all pages ----
def extract_text_pymupdf_all_pages(path):
    doc = fitz.open(path)
    full_text = ""
    for page_num, page in enumerate(doc):
        page_text = page.get_text()
        full_text += f"\n{page_text}"
    return full_text.strip()

# ---- Helper: OCR scanned PDFs ----
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
            text += "\n" + pytesseract.image_to_string(image)
    return text.strip()

# ---- Helper: Clean and detect form fields ----
def extract_fields(text):
    allowed_keywords = [
        "name", "dob", "birth", "date", "address", "email", "phone", "mobile",
        "number", "cnic", "id", "gender", "nationality", "father", "mother",
        "guardian", "contact", "city", "zip", "postal"
    ]
    banned_keywords = [
        "page", "info", "section", "form", "table", "instruction",
        "note", "title", "heading", "signature", "marks", "roll"
    ]

    lines = text.lower().split("\n")
    fields = []

    for line in lines:
        line = line.strip()

        if not line or len(line) < 4 or len(line) > 60:
            continue

        # Only accept lines that look like field prompts
        if not (":" in line or "-" in line):
            continue

        if any(bad in line for bad in banned_keywords):
            continue

        if any(ok in line for ok in allowed_keywords):
            match = re.split(r'[:\-]', line)[0].strip().title()
            if match and len(match) > 2:
                fields.append(match)

    return sorted(set(fields))

# ---- Main App Logic ----
if pdf_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    with st.spinner("🔍 Reading form (multi-page)..."):
        text = extract_text_pymupdf_all_pages("temp.pdf")

    # If not enough text, try OCR
    if not text or len(text.strip()) < 50:
        st.warning("⚠️ Not enough text found. Trying OCR on embedded images...")
        with st.spinner("🧠 Performing OCR on all pages..."):
            text = extract_text_ocr_all_pages("temp.pdf")

    if not text:
        st.error("❌ No readable text could be extracted from this file.")
    else:
        fields = extract_fields(text)

        if not fields:
            st.warning("⚠️ No fillable fields found.")
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
