import streamlit as st
import requests
from download_embedding import ensure_embeddings


ensure_embeddings()
st.set_page_config(
    page_icon='💊',
    layout='centered',
    page_title='MedSave'
)
st.title("💊 MedSave")
st.write("Upload your prescription and get generic alternatives with price comparison.")

prescription = st.file_uploader("Upload your prescription", type=["pdf", "jpg", "jpeg", "png"])

if st.button("Submit", disabled=(prescription is None)):
    with st.spinner("Analyzing your prescription..."):
        try:
            response = requests.post(
                url="http://localhost:8000/upload",
                files={"prescription": prescription},
                timeout=60
            )
        except requests.exceptions.ConnectionError:
            st.error("❌ Backend server se connect nahi ho paya. Check karo FastAPI server chal raha hai ya nahi.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timeout ho gaya — server response dene mein bahut time le raha hai.")
            st.stop()

    if response.status_code != 200:
        st.error(f"Server error ({response.status_code}): {response.text}")
        st.stop()

    results = response.json()

    if not results:
        st.warning("Koi medicine detect nahi hui prescription mein.")
        st.stop()

    st.subheader("Results")

    for med_name, data in results.items():
        with st.container(border=True):
            st.markdown(f"### {med_name}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Branded**")
                popular = data.get("popular_name")
                if popular:
                    st.write(popular)
                    st.write(f"MRP: ₹{data.get('mrp', 0)}")
                else:
                    st.write("Not found")

            with col2:
                st.markdown("**Generic Alternative**")
                generic = data.get("generic_medicine")
                if generic:
                    st.write(generic)
                    st.write(f"MRP: ₹{data.get('generic_mrp', 0)}")
                else:
                    st.write("Not found")

            savings = data.get("money_saved")
            if savings == "Undefined" or savings is None:
                st.info("Savings Calculation not possible, as no match found for generic")
            elif isinstance(savings, (int, float)) and savings > 0:
                st.success(f"💰 You save ₹{savings}")
            else:
                st.info("No savings found for this medicine.")