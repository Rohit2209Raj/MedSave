from sentence_transformers import SentenceTransformer,util
from jan_aushadhi_embedding import rows,vectors,model
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

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



# def get_substitues(med_name:str):
#     client=Groq(api_key=os.getenv('GROQ_API_KEY'))

#     system_prompt='''


# '''



if __name__ == "__main__":
    # Step 1: ek baar embed karo
    # rows, vectors = load_jan_aushadhi_embeddings()

    # Step 2: test queries
    test_queries = [
        "Amlodipine (5mg)  Metoprolol Succinate (50mg)"
    ]

    for query in test_queries:
        print(f"\n--- Query: {query} ---")
        candidates = get_top_candidates(query, rows, vectors, top_k=15)
        for c in candidates:
            print(f"  {c['score']:.4f}  |  {c['drug_name']}  |  MRP: {c['mrp']}")