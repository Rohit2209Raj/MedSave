from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
def llm_generate(file_path):

    with open(file_path,'rb') as f:
        file_bytes=f.read()

        if file_path.endswith(".pdf"):
            mime_type = "application/pdf"
        elif file_path.endswith((".jpg",'.jpeg')):
            mime_type = "image/jpeg"
        else:
            mime_type = "image/png"
        
        response=client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                 {"inline_data": {"mime_type": mime_type, "data": file_bytes}},
                    "Extract all medicine names, dosages, and instructions. "
                    "Mark unclear text with [UNCERTAIN]."
            ]
        )

        return response.text


