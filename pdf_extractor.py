import pdfplumber
from llm_text import llm_generate

def extract_text(pdf_path):
    text=""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    if text and len(text.strip())>20:
        return text
    else :
        return llm_generate(pdf_path)