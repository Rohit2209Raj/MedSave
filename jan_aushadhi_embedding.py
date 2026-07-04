from sentence_transformers import SentenceTransformer, util
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db')

# Model ek baar load hota hai, poore script ke liye reuse hota hai
model = SentenceTransformer('all-MiniLM-L6-v2')


def load_jan_aushadhi_embeddings():
    """
    Jan Aushadhi table ka pura data padhta hai, saare drug_name ko
    ek saath embed karta hai. Ye function sirf EK BAAR chalna chahiye
    (server start pe, ya script ke shuru mein) — baar baar nahi.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT drug_name, unit_size, mrp FROM jan_aushadhi")
        )
        rows = result.mappings().all()

    if not rows:
        raise ValueError("jan_aushadhi table empty hai ya query fail hui")

    names = [row["drug_name"] for row in rows]
    print(f"Embedding {len(names)} Jan Aushadhi entries...")
    vectors = model.encode(names, show_progress_bar=True)

    return rows, vectors


rows,vectors=load_jan_aushadhi_embeddings()

