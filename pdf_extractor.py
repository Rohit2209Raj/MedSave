import pdfplumber
from llm_text import llm_generate

# def extract_text(pdf_path):
#     text=""
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             text += page.extract_text()

#     if text and len(text.strip())>20:
#         return text
#     else :
#         return llm_generate(pdf_path)


def extract_medicine_table(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        
        medicines = []
        
        for table in tables:
            for row in table:
                # Row mein medicine name, dosage, etc. columns honge
                print(row)  # pehle dekh lo structure kaisa hai
                
        return tables