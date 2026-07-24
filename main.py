from fastapi import FastAPI,File,UploadFile,HTTPException
from pydantic import BaseModel
from matcher import get_substitutes
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


    generic_medicines={}
    for x in response:
        generic_medicines[x['name']]=(get_substitutes(x['name']+x['type']+x['qty']))


    return generic_medicines
