import streamlit as st
import requests

st.set_page_config(
    page_icon='',
    layout='centered',
    page_title='MedSave'
)

st.title("MedSave")
st.write("Upload your Medical Prescription and get Genric Alternative...")

prescription = st.file_uploader("Upload your prescription here")
if st.button("Submit"):
    with st.spinner("Analyzing"):
        response=requests.post(
            url="http://localhost:8000/upload",
            files={"prescription":prescription}
        )
        # st.success(response.status_code)
        st.success(response.json())

