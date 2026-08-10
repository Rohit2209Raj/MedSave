# real_download_embeddings.py
import os
import requests
import time

EMBEDDINGS_CACHE = "medicine_embedding.pkl"
URL = "https://huggingface.co/datasets/YudiCadini/medicine_embedding/resolve/main/medicine_embedding.pkl"
MAX_RETRIES = 5
TIMEOUT = 60  # seconds per chunk stall

def download_with_retries():
    tmp_path = EMBEDDINGS_CACHE + ".part"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Downloading medicine embeddings... (attempt {attempt}/{MAX_RETRIES})")
            with requests.get(URL, stream=True, timeout=TIMEOUT) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                # Verify full file downloaded
                if total and downloaded != total:
                    raise IOError(f"Incomplete download: got {downloaded}, expected {total}")

            os.rename(tmp_path, EMBEDDINGS_CACHE)
            print("Done.")
            return

        except Exception as e:
            print(f"Download failed: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if attempt < MAX_RETRIES:
                wait = 5 * attempt
                print(f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise RuntimeError("Failed to download embeddings after multiple retries.")

def ensure_embeddings():
    if not os.path.exists(EMBEDDINGS_CACHE):
        download_with_retries()
    else:
        print("Embeddings already present.")

ensure_embeddings()