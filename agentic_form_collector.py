# 📁 File: agentic_form_collector.py
import re
import streamlit as st
import fitz  # PyMuPDF

st.set_page_config(page_title="Agentic Form Field Collector", layout="centered")
st.title("🤖📄 Agentic Form Field Collector")
st.markdown("Upload a form PDF and the agent will extract missing fields and ask you to fill them in.")

# ---- Step 1: Upload the form ----
pdf_file = st.file_uploader("📤 Upload your form (PDF only)", type=["pdf"])

def extract_fields_via_text(path):
    """Improved: Extract field-like labels from the PDF using PyMuPDF and regex."""
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    
    # Use regex to find lines like 'Name:', 'Address', 'Date of Birth:', etc.
    lines = text.split("\n")
    field_pattern = re.compile(r"([A-Za-z0-9\s\-_/]+)\s*[:\-–]\s*")  # better field matching

    fields = []
    for line in lines:
        matches = field_pattern.findall(line)
        for match in matches:
            cleaned = match.strip()
            if 2 < len(cleaned) < 40:
                fields.append(cleaned)

    return list(set(fields))


# ---- Step 2: Extract fields ----
if pdf_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    with st.spinner("🔍 Reading and analyzing the form..."):
        fields = extract_fields_via_text("temp.pdf")

    if not fields:
        st.warning("⚠️ No field-like entries found in the form.")
    else:
        st.success("✅ Fields extracted successfully!")
        st.markdown("### ✍️ Please fill in the missing fields:")

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
                text = st.text_input(f"{field}", placeholder=f"Enter your {field}")
                user_inputs[field] = text

        if st.button("📨 Submit Information"):
            st.success("✅ Info Collected Successfully!")
            st.json(user_inputs)
