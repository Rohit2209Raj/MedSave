from sentence_transformers import SentenceTransformer,util
from jan_aushadhi_embedding import rows,vectors,model
from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_top_candidates(query_composition: str, rows, vectors, top_k=15):
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



def get_substitues(med_name:str):
    substitue_lists=get_top_candidates(med_name,rows,vectors,top_k=15)
    client=Groq(api_key=os.getenv('GROQ_API_KEY'))

    system_prompt='''
        You are a pharmaceutical dosage-matching assistant. You will be given an ORIGINAL medicine (name + dosage per active ingredient) and a list of 15 CANDIDATE medicines, each with a name, dosage(s), a semantic similarity score, and an MRP. Your job is to pick the single best clinical match.

        ## Critical Rule
        IGNORE the semantic similarity score completely when making your decision. It is provided for reference only and is known to be unreliable — it often rewards text/phrase overlap (e.g., shared words like "Extended Release" or ingredient order) even when the actual dosage is wrong. A high score does NOT mean a good match. Do not mention it as a reason for your choice.

        ## Step 1: Decompose Every Medicine Into Components
        For the ORIGINAL and for EACH candidate, break down into a list of (active_ingredient, strength, unit) tuples. Normalize units first (mg/g/mcg, ml/L) so values are directly comparable.

        Example:
        Original: Amlodipine 5mg + Metoprolol Succinate 50mg
        → [(Amlodipine, 5, mg), (Metoprolol Succinate, 50, mg)]

        ## Step 2: Filter by Ingredient Match
        A candidate is only eligible if it contains the SAME set of active ingredients as the original (same salt forms where specified — e.g., "Metoprolol Succinate" ≠ "Metoprolol Tartrate", "Amlodipine Besilate" ≈ "Amlodipine" unless the salt is clinically relevant to dosing).

        - If original is a single drug, candidate must not be missing or adding another active ingredient that changes the treatment intent.
        - If original is a combination, ALL components must be present in the candidate. Partial ingredient matches are disqualified, not down-ranked.

        ## Step 3: Score Remaining Candidates by Dosage Accuracy
        For each ingredient shared between original and candidate, compute the dosage difference. Rank eligible candidates using this priority:

        1. **Exact match on every ingredient's dosage** → highest priority, always wins if available.
        2. **Closest total dosage deviation** → if no exact match exists, prefer the candidate with the smallest cumulative % difference across all ingredients, not just one.
        3. A candidate that is exact on one ingredient but wildly off on another (e.g., correct Amlodipine but half-dose Metoprolol) ranks BELOW a candidate that is moderately close on both.

        Never let a "close enough" high-profile ingredient match compensate for a wrong dose on another ingredient in the same combination — a 50% dosage difference (e.g., 25mg vs 50mg) is a hard flag, not a minor deviation.

        ## Step 4: Formulation & Practical Tie-Breakers
        Only after Steps 1–3 narrow it to one or a tie:
        - Prefer matching formulation/release type (Extended Release ≈ Prolonged Release ≈ Sustained Release; treat these as equivalent unless original specifies otherwise).
        - If still tied, prefer lower MRP (cost-saving is the product's purpose).

        ## Output Format
        Respond ONLY in this JSON structure:

        {
        "original": "<echo original medicine and dosage>",
        "eligible_candidates": [<list of candidate indices that passed Step 2>],
        "best_match_index": <int, or null>,
        "best_match_name": "<string, or null>",
        "dosage_comparison": {
            "<ingredient_name>": {"original": "<val>", "matched": "<val>", "match": true/false}
        },
        "confidence": "high | medium | low",
        "reasoning": "<2-3 sentences, must explicitly state why higher-semantic-score candidates were rejected if applicable>",
        "flags": ["<e.g. 'closest available match, not exact', 'MRP unusually low, verify', 'tie broken by cost'>"]
        }

        ## Hard Rules
        - Never pick a candidate missing an active ingredient from the original.
        - Never let semantic score override a dosage mismatch.
        - If no eligible candidate exists after Step 2, return best_match_index: null with confidence "low" — do not force a partial match.
        - Always show your dosage comparison per-ingredient, not just a verdict.


        '''
    MODEL=''
    response=client.chat.completion.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": med_name},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw_text = response.choices[0].message.content
    return raw_text



# if __name__ == "__main__":
#     # Step 1: ek baar embed karo
#     # rows, vectors = load_jan_aushadhi_embeddings()

#     # Step 2: test queries
#     test_queries = [
#         "Amlodipine (5mg)  Metoprolol Succinate (50mg)"
#     ]

#     for query in test_queries:
#         print(f"\n--- Query: {query} ---")
#         candidates = get_top_candidates(query, rows, vectors, top_k=15)
#         for c in candidates:
#             print(f"  {c['score']:.4f}  |  {c['drug_name']}  |  MRP: {c['mrp']}")