import pdfplumber

with pdfplumber.open("Apolo_prescription.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)