# real_download_embeddings.py
import os, requests

EMBEDDINGS_CACHE = "medicine_embedding.pkl"
URL ="https://huggingface.co/datasets/YudiCadini/medicine_embedding/resolve/main/medicine_embedding.pkl"

def ensure_embeddings():
    if not os.path.exists(EMBEDDINGS_CACHE):
        print("Downloading medicine embeddings...")
        r = requests.get(URL)
        r.raise_for_status()
        with open(EMBEDDINGS_CACHE, "wb") as f:
            f.write(r.content)
        print("Done.")
    else:
        print("Embeddings already present.")

ensure_embeddings()