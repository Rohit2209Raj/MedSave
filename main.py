from fastapi import FastAPI
from pydantic import BaseModel
from pdf_extractor import extract_text

app=FastAPI()


@app.get('/')
def home():
    return {'message':'Welcome to MedSave'}

@app.post('/paste')
def get_med(pdf_path:str):
    response=extract_text(pdf_path)

    return {'message':response}
