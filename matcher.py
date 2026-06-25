import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db')


def get_generic(drug_name):
    cleaned=drug_name.lower().strip()
    match = re.search(
        r'([A-Za-z\s]+)\s*\(?\s*(\d+(?:\.\d+)?)\s*mg\)?',
        drug_name,
        re.IGNORECASE
    )

    if not match:
        return []

    med = match.group(1).strip()
    qty = match.group(2)

    # print("Medicine:", med)
    # print("Qty:", qty)

    with engine.connect() as conn:

        result = conn.execute(
            text("""
                SELECT drug_name, unit_size, mrp
                FROM jan_aushadhi
                WHERE drug_name ILIKE :med
                AND drug_name ~* :qty
            """),
            {
                "med": f"%{med}%",
                "qty": rf"\m{qty}\M"
            }
        )
        ans=result.fetchall()
        if not ans:
            return [f"No medcine avaliable for: {cleaned} "]
        else:
            return ans

def get_substitute(drug_name):


        