import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db')


def clean_name(name):
    words = name.strip().split()
    if words and words[0] in ['cheaper', 'costlier']:
        words = words[1:]
    return ' '.join(words)


def remove_substring_duplicates(medicines):
    cleaned = []
    names = [m[0].strip() for m in medicines]
    for i, name in enumerate(names):
        is_substring_of_another = False
        for j, other_name in enumerate(names):
            if i != j and other_name in name and len(other_name) < len(name):
                is_substring_of_another = True
        if not is_substring_of_another:
            cleaned.append(medicines[i])
    return cleaned


def get_substitutes(drug_name):
    # Database se query karo (pandas/CSV nahi, seedha DB se)
    with engine.connect() as conn:
        query = text("SELECT substitute_list FROM medicines WHERE drug_name = :name")
        result = conn.execute(query, {"name": drug_name}).fetchone()

    if not result:
        return []

    raw_text = result[0]
    if not raw_text:
        return []

    matches = re.findall(
        r'([A-Za-z][A-Za-z0-9\-\s]*?(?:Tablet|Capsule|Injection|Syrup))[A-Za-z\s.&]*?\?(\d+\.\d+)',
        raw_text
    )

    unique_matches = list(set(matches))
    final_matches = remove_substring_duplicates(unique_matches)

    return [(clean_name(name), price) for name, price in final_matches]
