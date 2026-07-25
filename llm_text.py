# from google import genai
# from dotenv import load_dotenv
# import os,json

# load_dotenv()

# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# def llm_generate(file_path):

#     with open(file_path,'rb') as f:
#         file_bytes=f.read()

#         if file_path.endswith(".pdf"):
#             mime_type = "application/pdf"
#         elif file_path.endswith((".jpg",'.jpeg')):
#             mime_type = "image/jpeg"
#         else:
#             mime_type = "image/png"
        
#         response=client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=[
#                  {"inline_data": {"mime_type": mime_type, "data": file_bytes}},
#                      """Extract all medicines from this prescription.
                    
#                     Return ONLY a valid JSON array containing for each medicine its name,type like gel/tablet/syringe/cream etc along with its qty in ml/mg/whatever provided.
                    
                    
                    
#                     If any field is unclear or unreadable, set its value to 
#                     null and confidence to "low".
#                     """
#             ],
#             response_format={"type": "json_object"}
#         )

#         raw_text = response.text.strip()
#         raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        
#         try:
#             medicines = json.loads(raw_text)
#         except json.JSONDecodeError:
#             print("⚠️ JSON parse failed, raw response:")
#             print(raw_text)
#             medicines = []
        
#         return medicines


from google import genai
from google.genai import types
from dotenv import load_dotenv
import os, json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

def llm_generate(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = MIME_TYPES.get(ext)

    if mime_type is None:
        raise ValueError(f"Unsupported file type: {ext}")

    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                """Extract all medicines from this prescription.

                Return ONLY a valid JSON array. Each element must have exactly
                these fields: "name", "type" (gel/tablet/syringe/cream/etc),
                "qty" (with unit, e.g. "500mg"), and "confidence" ("high" or "low").

                If any field is unclear or unreadable, set its value to null
                and confidence to "low".
                """
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
    except Exception as e:
        print(f"❌ Gemini API call failed: {e}")
        return []

    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        medicines = json.loads(raw_text)
    except json.JSONDecodeError:
        print("⚠️ JSON parse failed, raw response:")
        print(raw_text)
        medicines = []

    return medicines