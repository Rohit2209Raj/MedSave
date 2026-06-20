from google import genai
from dotenv import load_dotenv
import os,json

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
                     """Extract all medicines from this prescription.
                    
                    Return ONLY a valid JSON array in this exact format, 
                    with no extra text or explanation:
                    
                    [
                    {
                        "medicine_name": "...",
                        "dosage": "...",
                        "frequency": "...",
                        "duration": "...",
                        "confidence": "high/medium/low"
                    }
                    ]
                    
                    If any field is unclear or unreadable, set its value to 
                    null and confidence to "low".
                    """
            ]
        )

        raw_text = response.text.strip()
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        
        try:
            medicines = json.loads(raw_text)
        except json.JSONDecodeError:
            print("⚠️ JSON parse failed, raw response:")
            print(raw_text)
            medicines = []
        
        return medicines


