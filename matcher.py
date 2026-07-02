import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db')


def get_generic(drug_name):
    cleaned = drug_name.lower().strip()

    match = re.search(
        r'([A-Za-z\s]+?)\s+(\d+(?:\.\d+)?)\s*(?:mg|mcg|g|ml)?\s*(tablet|capsule|syrup|injection|cream|ointment|gel|drops|suspension)?',
        drug_name,
        re.IGNORECASE
    )

    if not match:
        return []

    med = match.group(1).strip()
    qty = match.group(2)
    dosage = match.group(3)

    # Build regex pattern
    pattern = rf"{med}.*\m{qty}\M"

    if dosage:
        pattern += rf".*{dosage}"

    with engine.connect() as conn:

        result = conn.execute(
            text("""
                SELECT drug_name, unit_size, mrp
                FROM jan_aushadhi
                WHERE drug_name ~* :pattern
                AND drug_name !~* '\\band\\b'
            """),
            {
                "pattern": pattern
            }
        )

        ans = result.mappings().all()

        if not ans:
            return [f"No medicine available for: {cleaned}"]

        return ans

def get_substitutes(drug_name):

    cleaned = drug_name.lower().strip()

    with engine.connect() as conn:

        result = conn.execute(
            text("""
                SELECT drug_name,mrp,generic_med1,generic_med2
                FROM medicine
                WHERE LOWER(drug_name) ILIKE :name
            """),
            {"name": f"%{cleaned}%"}
        )

        rows = result.mappings().all()
        return rows

        if not rows:
            return {
                "message": f"No medicine available for {cleaned}"
            }

        final=[]
        for row in rows:
            temp = {
                "original_medicine": row["drug_name"],
                "original_price": row["mrp"],
                "substitutes": []
            }
             
            for generic in [ row["generic_med1"],row["generic_med2"]]:
                if generic:

                    generic_result = get_generic(generic)

                    temp["substitutes"].append({
                        "generic_name": generic,
                        "generic_price": generic_result,

                    })

            final.append(temp)
    
    return final

                

    

    


    




        