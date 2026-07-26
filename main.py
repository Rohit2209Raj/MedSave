from fastapi import FastAPI,File,UploadFile,HTTPException
from pydantic import BaseModel
from matcher import get_substitutes
import json
# from pdf_extractor import extract_text
from llm_text import llm_generate
import shutil,os

app=FastAPI()

@app.get('/')
def home():
    return {'message':'Welcome to MedSave'}

@app.post('/upload')
async def get_med(prescription:UploadFile=File(...)):

    temp_path=f'temp_{prescription.filename}'
    with open(temp_path,'wb') as f:
        shutil.copyfileobj(prescription.file,f)
    
    response=llm_generate(temp_path)

    os.remove(temp_path)

    ans={}

    for c in response:
        result_string = ""

        if c.get("name") is not None:
            result_string += c["name"]

        if c.get("type") is not None:
            result_string += c["type"]

        if c.get("qty") is not None:
            result_string += c["qty"]

        ans[c.get("name")] = get_substitutes(result_string)


    return ans
