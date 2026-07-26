from sentence_transformers import SentenceTransformer,util
import pickle
import os
from groq import Groq
import json
from dotenv import load_dotenv


load_dotenv()

EMBEDDINGS_CACHE1 = "jan_aushadhi_embeddings.pkl"
EMBEDDINGS_CACHE2 = "medicine_embedding.pkl"
model = SentenceTransformer('all-MiniLM-L6-v2')

def load_jan_aushadhi_embedding_from_cache():
    if not os.path.exists(EMBEDDINGS_CACHE1):
        raise FileNotFoundError(
            f"❌ Cache file '{EMBEDDINGS_CACHE1}' nahi mila!\n"
            f"Pehle 'jan_aushadhi_embeddings.py' run karo to cache create ho."
        )
    print(f"📦 Loading embeddings from cache: {EMBEDDINGS_CACHE1}")
    with open(EMBEDDINGS_CACHE1, 'rb') as f:
        cached_data = pickle.load(f)
    
    rows = cached_data['rows']
    vectors = cached_data['vectors']
    print(f"✅ Loaded {len(rows)} embeddings from cache")
    
    return rows, vectors




def load_medicine_embedding_from_cache():
    if not os.path.exists(EMBEDDINGS_CACHE2):
        raise FileNotFoundError(
            f"❌ Cache file '{EMBEDDINGS_CACHE2}' nahi mila!\n"
            f"Pehle 'medicine_embeddings.py' run karo to cache create ho."
        )
    print(f"📦 Loading embeddings from cache: {EMBEDDINGS_CACHE2}")
    with open(EMBEDDINGS_CACHE2, 'rb') as f:
        cached_data = pickle.load(f)
    
    rows = cached_data['rows']
    vectors = cached_data['vectors']
    print(f"✅ Loaded {len(rows)} embeddings from cache")
    
    return rows, vectors

rows,vectors=load_jan_aushadhi_embedding_from_cache()
rows2,vectors2=load_medicine_embedding_from_cache()
def get_top_candidates_jan_aushadhi(query_composition: str, rows, vectors, top_k=15):
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


def get_top_candidates_medicine(query_composition: str, rows, vectors, top_k=10):
    query_vec = model.encode(query_composition)

    scores = util.cos_sim(query_vec, vectors)[0]
    top_results = scores.topk(min(top_k, len(rows)))
 
    candidates = []
    for score, idx in zip(top_results.values, top_results.indices):
        idx = int(idx)
        candidates.append({
            "drug_name": rows[idx]["drug_name"],
            "mrp": rows[idx]["mrp"],
            "score": round(float(score), 4),
        })
 
    return candidates

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0

def get_substitutes(med_name: str):
    candidates=get_top_candidates_jan_aushadhi(med_name,rows,vectors)
    candidates_medicine=get_top_candidates_medicine(med_name,rows2,vectors2)
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
 
    system_prompt1 = '''
    You are a pharmaceutical dosage-matching assistant. You will be given an ORIGINAL medicine 
    (name + dosage per active ingredient) and 
    1 list of 15 CANDIDATE medicines with their names, 
    dosages, similarity scores, and MRP. Your job is to pick the single best clinical match.

    ## Critical Rules:
    1. IGNORE the similarity score completely — it is unreliable and often rewards text/phrase overlap.
    2. Match by DOSAGE first, not by name similarity.
    3. If unsure or confidence < 90%, return "Don't found any medicine" — do NOT guess.
    4. Always provide exact names, MRP, and dosage — no summaries or shortcuts.
 
    ## Output Format (JSON ONLY):
    {
        "generic_medicine": "Exact name of best match",
        "generic_mrp": MRP value,
        "generic_dosage": "Exact dosage info",
    }
    '''

    system_prompt2 = '''
        You are a pharmaceutical dosage-matching assistant. You will be given an ORIGINAL medicine 
        (name + dosage per active ingredient) and 
        1 list of 10 CANDIDATE medicines with their names, 
        similarity scores, and MRP. Your job is to pick the single best clinical match based on name.

    
        ## Critical Rules:
        1. IGNORE the similarity score completely — it is unreliable and often rewards text/phrase overlap.
        2. Match by name only, not by similarity.
        3. If unsure or confidence < 90%, return "Don't found any medicine" — do NOT guess.
        4. Always provide exact names, MRP no summaries or shortcuts.
     
        ## Output Format (JSON ONLY):
        {
            "popular_name": "Exact name of best match",
            "mrp": MRP value,
        }
        '''

    # system_prompt3 = '''
    # You are a merge assistant for a pharmaceutical price-comparison pipeline. You will be given:

    # 1. OUTPUT_A (dosage-matched generic result): generic_medicine name, mrp, dosage.
    # 2. OUTPUT_B (name-matched popular/branded result): popular_name, mrp.

    # Your job is ONLY to merge these into one clean record and compute the price saved. 
    # Do NOT re-match, re-rank, or second-guess either input — treat both as already final.

    # ## Critical Rules:
    # 1. Copy popular_name and popular_mrp directly from OUTPUT_B, unchanged.
    # 2. Copy generic_name and generic_mrp directly from OUTPUT_A, unchanged.
    # 3. If EITHER OUTPUT_A or OUTPUT_B is "Don't found any medicine" (or missing/null), 
    # set that side's name/mrp fields to null and set price_saved to null — 
    # do NOT attempt to compute a partial or estimated saving.
    # 4. price_saved = popular_mrp - generic_mrp, rounded to 2 decimals. 
    # If negative (generic is pricier than the branded/popular version), return the actual 
    # negative number — do not clip to zero or hide it.
    # 5. Never invent, average, or alter any name or price. Every value must trace directly 
    # back to OUTPUT_A or OUTPUT_B.
    # 6. Output valid JSON only — no prose, no markdown fences, no extra keys, no explanations.

    # ## Output Format (JSON ONLY, use actual values not placeholders):
    # {
    #     "popular_name": null,
    #     "popular_mrp": null,
    #     "generic_name": null,
    #     "generic_mrp": null,
    #     "price_saved": null
    # }
    # '''

    



    MODEL = 'llama-3.3-70b-versatile'
    
    # Candidates ko formatted string mein convert kar
    candidates_text_generic = f"Original Medicine: {med_name}\n\nCandidates:\n"
    for i, c in enumerate(candidates):
        candidates_text_generic += f"{i+1}. {c['drug_name']} ({c['unit_size']}) - MRP: {c['mrp']} - Similarity Score: {c['score']}\n"
 
    response1 = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt1},
            {"role": "user", "content": candidates_text_generic},
        ],
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
    )
 
    raw_text1 = response1.choices[0].message.content


    # Candidates ko formatted string mein convert kar
    # Candidates ko formatted string mein convert kar
    candidates_text_medicine = f"Original Medicine: {med_name}\n\nCandidates:\n"
    for i, c in enumerate(candidates_medicine):
        candidates_text_medicine += f"{i+1}. {c['drug_name']}- MRP: {c['mrp']} - Similarity Score: {c['score']}\n"
     
    response2 = client.chat.completions.create(
        messages=[
                {"role": "system", "content": system_prompt2},
                {"role": "user", "content": candidates_text_medicine},
            ],
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        )   

    raw_text2 = response2.choices[0].message.content
    # return raw_text1,raw_text2

    js1 = json.loads(raw_text1)
    js2 = json.loads(raw_text2)

    generic_mrp = safe_float(js1.get('generic_mrp'))
    branded_mrp = safe_float(js2.get('mrp'))

    answer = {}
    answer['generic_medicine'] = js1.get('generic_medicine')
    answer['generic_mrp'] = generic_mrp
    answer['popular_name'] = js2.get('popular_name')
    answer['mrp'] = branded_mrp
    if generic_mrp!=0 and branded_mrp!=0:
        answer['money_saved'] = max(0,round(branded_mrp - generic_mrp, 2))
    else:
        answer['money_saved']='Undefined'
    return answer


    # total_output = f"OUTPUT_A:\n{raw_text1}\n\nOUTPUT_B:\n{raw_text2}"

    # response3 = client.chat.completions.create(
    #         messages=[
    #                 {"role": "system", "content": system_prompt3},
    #                 {"role": "user", "content": total_output},
    #             ],
    #         model=MODEL,
    #         temperature=0,
    #         response_format={"type": "json_object"},
    #         ) 

    # raw_text3 = response3.choices[0].message.content

    # return raw_text3















# if __name__ == "__main__":
#     # Step 1: Cache se embeddings load kar
#     # rows, vectors = load_embeddings_from_cache()
 
#     # Step 2: Test queries
#     test_queries = [
#         "Amlodipine 5mg Metoprolol Succinate 50mg",
#         "Paracetamol 500mg",
#         "Aspirin 75mg",
#     ]
 
#     for query in test_queries:
#         print(f"\n{'='*70}")
#         print(f"🔍 Query: {query}")
#         print(f"{'='*70}")
        
#         # # Step 3: Top candidates nikalo
#         # candidates = get_top_candidates(query, rows, vectors, top_k=15)
        
#         # print("\n📊 Top 15 Candidates:")
#         # for i, c in enumerate(candidates, 1):
#         #     print(f"  {i:2d}. [{c['score']:.4f}] {c['drug_name']:40s} | {c['unit_size']:15s} | MRP: ₹{c['mrp']}")
 
#         # # Step 4: AI se best match select karwao
#         # print("\n🤖 AI Analysis (Groq):")
#         result = get_substitutes(query)
#         print(result)
 