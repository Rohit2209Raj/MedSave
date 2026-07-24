import pickle
import os
from sentence_transformers import SentenceTransformer,util
from sqlalchemy import create_engine,text

engine=create_engine('postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db')

model=SentenceTransformer('all-MiniLM-L6-v2')

EMBEDDINGS_CACHE = "jan_aushadhi_embeddings.pkl"

def load_jan_aushadhi_embeddings(force_recompute=True):

    if os.path.exists(EMBEDDINGS_CACHE) and not force_recompute:
        print(f'EMbedding Present: ')
        with open(EMBEDDINGS_CACHE,'rb') as f:
            cached_data=pickle.load(f)

        return cached_data['rows'],cached_data['vectors']

    print('Fetching data from Database')
    with engine.connect() as conn:
        result=conn.execute(
            text("SELECT drug_name,unit_size,mrp FROM jan_aushadhi")
        )
        rows=result.mapping().all()

    if not rows:
        raise ValueError("jan_aushadhi table is empty")

    names = [row["drug_name"] for row in rows]
    vectors = model.encode(names, show_progress_bar=True)

    caches_data={
        'rows':rows,
        'vectors':vectors
    }

    with open(EMBEDDINGS_CACHE,'wb') as f:
        pickle.dump(cached_data,f)

    return rows,vectors