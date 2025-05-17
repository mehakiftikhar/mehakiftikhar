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
st.markdown("Upload a form (PDF - scanned or text-based). Agent will extract fillable fields and prompt you to complete them.")

# --- File uploader ---
pdf_file = st.file_uploader("📤 Upload your form (PDF only)", type=["pdf"])

# --- EasyOCR reader ---
reader = easyocr.Reader(['en'], gpu=False)

# --- Extract form fields directly from fillable PDF ---
def extract_form_fields_from_pdf(path):
    doc = fitz.open(path)
    fields = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()  # form fields on this page
        if widgets:
            for w in widgets:
                field_name = w.field_name
                if field_name and field_name.lower() not in ['submit', 'reset']:
                    cleaned = field_name.strip().title()
                    if cleaned not in fields:
                        fields.append(cleaned)
    return fields

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

# --- Extract fillable logical fields from text ---
def extract_fields(path):
    doc = fitz.open(path)
    fields = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")  # list of (x0,y0,x1,y1,text,...)
        for block in blocks:
            text = block[4].strip()
            # Check if text looks like a label followed by underscores or empty space
            # Example pattern: "Name: ________"
            if re.search(r'[:\-]\s*[_\s]{3,}', text.lower()):
                label = re.split(r'[:\-]', text)[0].strip().title()
                if label not in fields:
                    fields.append(label)
    return fields


# --- Main Logic ---
if pdf_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    # 1. Try extracting fillable form fields directly
    fields = extract_form_fields_from_pdf("temp.pdf")

    # 2. If no fields found, try text extraction
    if not fields:
        with st.spinner("🔍 Extracting text from PDF..."):
            text = extract_text_pymupdf_all_pages("temp.pdf")

        # 3. If text is too little, try OCR
        if not text or len(text.strip()) < 50:
            st.warning("⚠️ Not enough text found. Trying OCR on scanned images...")
            with st.spinner("🧠 Performing OCR..."):
                text = extract_text_ocr_all_pages("temp.pdf")

        # 4. Extract fields from text using keywords
        if text:
            fields = extract_fields(text)

    if not fields:
        st.warning("⚠️ No fillable fields detected in the document.")
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
