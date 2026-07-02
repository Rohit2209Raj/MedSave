"""
MedSave matching pipeline — complete, standalone.

Pipeline:
    Brand name (user input)
        -> fuzzy search medicine table -> composition (generic_med1/2)
        -> normalize composition
        -> Jan Aushadhi lookup:
              1. exact dict match
              2. RapidFuzz fuzzy match
              3. embedding similarity match  (STUBBED - not implemented)
              4. Postgres regex             (last-resort fallback)
        -> return MRP, unit size, savings

Install before running:
    pip install sqlalchemy psycopg2-binary rapidfuzz --break-system-packages

Assumes tables:
    medicine(drug_name, mrp, generic_med1, generic_med2)
    jan_aushadhi(drug_name, unit_size, mrp)

If your real table/column names differ, edit the SQL in find_brand_row()
and _load_jan_aushadhi_lookup() — nothing else needs to change.
"""

import json
import re
from functools import lru_cache

from rapidfuzz import fuzz, process
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_URL = 'postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db'
engine = create_engine(DB_URL)

RAPIDFUZZ_ACCEPT_SCORE = 90     # composition-to-composition match threshold
BRAND_FUZZ_ACCEPT_SCORE = 80    # user-input-to-brand-name match threshold

SALT_SUFFIXES = [
    "hydrochloride", "hcl", "sulphate", "sulfate", "sodium",
    "potassium", "besylate", "maleate", "trihydrate", "citrate",
]

DOSAGE_FORM_WORDS = [
    "tablets", "tablet", "capsules", "capsule", "syrup", "injection",
    "cream", "ointment", "gel", "drops", "suspension", "ip", "bp", "usp",
]


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize(text_in: str) -> str:
    """
    'Fexofenadine Hydrochloride Tablets IP 120 mg' -> 'fexofenadine 120 mg'
    'Fexofenadine (120mg)'                         -> 'fexofenadine 120 mg'
    """
    if not text_in:
        return ""

    s = text_in.lower().strip()
    s = re.sub(r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml)\b', r'\1 \2', s)
    s = s.replace('(', ' ').replace(')', ' ')

    for salt in SALT_SUFFIXES:
        s = re.sub(rf'\b{salt}\b', ' ', s)
    for word in DOSAGE_FORM_WORDS:
        s = re.sub(rf'\b{word}\b', ' ', s)

    s = re.sub(r'\s+', ' ', s).strip()
    return s


# ---------------------------------------------------------------------------
# Step 1-3: brand -> composition (fuzzy search on medicine table)
# ---------------------------------------------------------------------------

def find_brand_row(user_input: str):
    """
    Fuzzy-search the medicine table by brand name.
    Returns best matching row as dict, or None if nothing clears the
    BRAND_FUZZ_ACCEPT_SCORE threshold.
    """
    cleaned = user_input.lower().strip()

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT drug_name, mrp, generic_med1, generic_med2 FROM medicine")
        )
        rows = result.mappings().all()

    if not rows:
        return None

    names = [row["drug_name"] for row in rows]
    match = process.extractOne(cleaned, names, scorer=fuzz.WRatio)

    if not match:
        return None

    matched_name, score, idx = match
    if score < BRAND_FUZZ_ACCEPT_SCORE:
        return None

    return dict(rows[idx])


# ---------------------------------------------------------------------------
# Step 4-5: composition -> Jan Aushadhi match
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_jan_aushadhi_lookup():
    """
    Loads + normalizes jan_aushadhi once. Cached for process lifetime.
    Call _load_jan_aushadhi_lookup.cache_clear() if the table changes
    at runtime and you need a fresh read.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT drug_name, unit_size, mrp FROM jan_aushadhi")
        )
        rows = result.mappings().all()

    exact = {}
    normalized_list = []
    for row in rows:
        norm = normalize(row["drug_name"])
        if not norm:
            continue
        exact.setdefault(norm, dict(row))
        normalized_list.append((norm, dict(row)))

    return exact, normalized_list


def _regex_fallback(normalized_query: str):
    """Last-resort tier: Postgres regex search."""
    parts = normalized_query.split()
    if not parts:
        return None

    pattern = re.escape(parts[0])
    for p in parts[1:]:
        pattern += rf".*{re.escape(p)}"

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT drug_name, unit_size, mrp
                FROM jan_aushadhi
                WHERE drug_name ~* :pattern
                AND drug_name !~* '\\band\\b'
                LIMIT 1
            """),
            {"pattern": pattern}
        )
        row = result.mappings().first()

    return dict(row) if row else None


def _embedding_fallback(normalized_query, normalized_list):
    """
    STUB. Not implemented. Returns None always.

    Do not wire this up until you've measured how often tiers 1-2 actually
    fail on real jan_aushadhi data. If you do implement it later:
        - use sentence-transformers to embed normalized_query and all
          normalized_list entries
        - cosine similarity, threshold ~0.90-0.95
        - cache jan_aushadhi embeddings the same way _load_jan_aushadhi_lookup
          caches the normalized strings, so you don't re-embed every request
    """
    return None


def match_jan_aushadhi(composition: str):
    """
    Returns: {matched: bool, method: str|None, row: dict|None, score: float|None}
    """
    normalized_query = normalize(composition)
    if not normalized_query:
        return {"matched": False, "method": None, "row": None, "score": None}

    exact, normalized_list = _load_jan_aushadhi_lookup()

    # Tier 1: exact
    if normalized_query in exact:
        return {"matched": True, "method": "exact", "row": exact[normalized_query], "score": 100}

    # Tier 2: RapidFuzz
    candidates = [n for n, _ in normalized_list]
    best = process.extractOne(normalized_query, candidates, scorer=fuzz.ratio)
    if best:
        matched_norm, score, idx = best
        if score >= RAPIDFUZZ_ACCEPT_SCORE:
            return {
                "matched": True, "method": "rapidfuzz",
                "row": normalized_list[idx][1], "score": score,
            }

    # Tier 3: embeddings (stub)
    embedding_result = _embedding_fallback(normalized_query, normalized_list)
    if embedding_result:
        return embedding_result

    # Tier 4: regex fallback
    regex_row = _regex_fallback(normalized_query)
    if regex_row:
        return {"matched": True, "method": "regex_fallback", "row": regex_row, "score": None}

    return {"matched": False, "method": None, "row": None, "score": None}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_substitutes(user_input: str):
    """Full pipeline: brand -> composition(s) -> Jan Aushadhi match(es) -> savings."""
    brand_row = find_brand_row(user_input)

    if not brand_row:
        return {"message": f"No medicine found for: {user_input}"}

    original_price = float(brand_row["mrp"]) if brand_row["mrp"] is not None else None

    result = {
        "original_medicine": brand_row["drug_name"],
        "original_price": original_price,
        "substitutes": [],
    }

    for generic in [brand_row.get("generic_med1"), brand_row.get("generic_med2")]:
        if not generic:
            continue

        match = match_jan_aushadhi(generic)

        entry = {
            "generic_name": generic,
            "matched": match["matched"],
            "match_method": match["method"],
            "match_score": match["score"],
        }

        if match["matched"]:
            row = match["row"]
            ja_mrp = float(row["mrp"]) if row["mrp"] is not None else None
            entry["jan_aushadhi_name"] = row["drug_name"]
            entry["unit_size"] = row["unit_size"]
            entry["mrp"] = ja_mrp

            if ja_mrp is not None and original_price is not None:
                savings = round(original_price - ja_mrp, 2)
                entry["savings"] = savings
                entry["savings_pct"] = round((savings / original_price) * 100, 1) if original_price else None
        else:
            entry["message"] = f"No Jan Aushadhi match for: {generic}"

        result["substitutes"].append(entry)

    return result


if __name__ == "__main__":
    for query in ["Allegra 120mg Tablet", "Azithral 500 Tablet", "Dolo 650", "allegra 120"]:
        print(f"\n--- {query} ---")
        print(json.dumps(get_substitutes(query), indent=2, default=str))