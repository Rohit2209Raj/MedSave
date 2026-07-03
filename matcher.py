"""
Jan Aushadhi semantic search — standalone, isolated.

Sirf ek kaam karta hai: koi bhi composition string do,
Jan Aushadhi table mein sabse similar top 5 rows nikaal ke do.

Install:
    pip install sentence-transformers

Run:
    python semantic_search.py
"""

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


def get_top_candidates(query_composition: str, rows, vectors, top_k=5):
    """
    Query composition ko embed karta hai, saare Jan Aushadhi vectors
    se cosine similarity nikaalta hai, top_k sabse similar return karta hai.
    """
    query_vec = model.encode(query_composition)
    scores = util.cos_sim(query_vec, vectors)[0]

    top_results = scores.topk(min(top_k, len(rows)))

    candidates = []
    for score, idx in zip(top_results.values, top_results.indices):
        idx = int(idx)
        candidates.append({
            "drug_name": rows[idx]["drug_name"],
            "unit_size": rows[idx]["unit_size"],
            "mrp": rows[idx]["mrp"],
            "score": round(float(score), 4),
        })

    return candidates


if __name__ == "__main__":
    # Step 1: ek baar embed karo
    rows, vectors = load_jan_aushadhi_embeddings()

    # Step 2: test queries
    test_queries = [
        "Hydrocortisone (1% w/w)",
        "Fexofenadine (120mg)",
        "Amoxycillin (500mg)",
        "Paracetamol (650mg)",
    ]

    for query in test_queries:
        print(f"\n--- Query: {query} ---")
        candidates = get_top_candidates(query, rows, vectors, top_k=5)
        for c in candidates:
            print(f"  {c['score']:.4f}  |  {c['drug_name']}  |  MRP: {c['mrp']}")