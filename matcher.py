import re
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db')

GENERIC_MEDICINES = {
    # Your original + expansions (antibiotics, pain, CV, etc.)
    "paracetamol", "azithromycin", "cetirizine", "ibuprofen", "amoxicillin", "metformin", "amlodipine", "atorvastatin", "omeprazole", "pantoprazole",
    "cefixime", "doxycycline", "diclofenac", "aspirin", "losartan", "telmisartan", "levothyroxine", "metronidazole", "ranitidine", "domperidone",

    # More Antibiotics / Anti-infectives (very common in India)
    "amoxicillin clavulanate", "ciprofloxacin", "levofloxacin", "ofloxacin", "clarithromycin", "erythromycin", "roxithromycin", "norfloxacin",
    "nitrofurantoin", "cephalexin", "cefuroxime", "ceftriaxone", "cefoperazone", "meropenem", "piperacillin tazobactam", "clindamycin",
    "linezolid", "vancomycin", "gentamicin", "amikacin", "cotrimoxazole", "isoniazid", "rifampicin", "pyrazinamide", "ethambutol", "acyclovir",
    "oseltamivir", "ivermectin", "albendazole", "mebendazole", "tinidazole", "secnidazole", "fluconazole", "itraconazole", "ketoconazole",
    "terbinafine", "griseofulvin", "artemether lumefantrine", "chloroquine", "primaquine",

    # Pain / Anti-inflammatory / Analgesics
    "naproxen", "aceclofenac", "etoricoxib", "tramadol", "codeine", "morphine", "fentanyl", "buprenorphine", "pregabalin", "gabapentin",
    "chlorzoxazone", "thiocolchicoside", "nimesulide", "meloxicam", "piroxicam", "indomethacin", "ketorolac", "aspirin dispersible",

    # Cardiovascular / Antihypertensives / Lipid-lowering
    "atenolol", "metoprolol", "bisoprolol", "carvedilol", "nebivolol", "ramipril", "enalapril", "lisinopril", "perindopril", "valsartan",
    "olmesartan", "candesartan", "hydrochlorothiazide", "chlorthalidone", "furosemide", "spironolactone", "torsemide", "clopidogrel",
    "aspirin cardio", "rosuvastatin", "simvastatin", "ezetimibe", "fenofibrate", "isosorbide dinitrate", "glyceryl trinitrate", "digoxin",
    "verapamil", "diltiazem", "nicorandil",

    # Antidiabetics
    "glimepiride", "glipizide", "gliclazide", "pioglitazone", "vildagliptin", "sitagliptin", "dapagliflozin", "empagliflozin", "canagliflozin",
    "insulin human", "insulin glargine", "insulin aspart", "insulin lispro", "teneligliptin", "linagliptin", "saxagliptin", "acarbose",
    "miglitol", "repaglinide",

    # Gastrointestinal / Anti-ulcer / Antacids
    "rabeprazole", "esomeprazole", "lansoprazole", "famotidine", "ondansetron", "granisetron", "metoclopramide", "itopride", "mosapride",
    "lactulose", "polyethylene glycol", "senna", "bisacodyl", "dicyclomine", "hyoscine butylbromide", "mebeverine", "sucralfate", "misoprostol",

    # Respiratory / Anti-allergic / Asthma
    "montelukast", "levocetirizine", "fexofenadine", "desloratadine", "budesonide", "fluticasone", "salmeterol", "formoterol", "theophylline",
    "ambroxol", "acetylcysteine", "salbutamol", "ipratropium", "terbutaline", "doxofylline", "roflumilast",

    # CNS / Neuropsychiatric
    "alprazolam", "clonazepam", "diazepam", "lorazepam", "escitalopram", "sertraline", "fluoxetine", "paroxetine", "venlafaxine", "duloxetine",
    "amitriptyline", "imipramine", "olanzapine", "risperidone", "quetiapine", "haloperidol", "carbamazepine", "sodium valproate", "phenytoin",
    "levetiracetam", "topiramate", "donepezil", "memantine", "methylphenidate",

    # Hormones / Thyroid / Others
    "prednisolone", "dexamethasone", "hydrocortisone", "betamethasone", "thyroxine", "estradiol", "progesterone", "testosterone", "folic acid",
    "vitamin d3", "calcium carbonate", "vitamin b12", "iron sucrose", "ferrous sulfate", "cyanocobalamin",

    # Anticancer / Others (common in oncology)
    "methotrexate", "cyclophosphamide", "doxorubicin", "paclitaxel", "cisplatin", "imatinib", "gefitinib", "erlotinib", "tamoxifen", "letrozole",

    # Additional common ones (vitamins, supplements, antimalarials, etc. to reach scale)
    "multivitamin", "zinc sulfate", "ascorbic acid", "thiamine", "pyridoxine", "riboflavin", "calcitriol", "alendronate", "raloxifene",
    "denosumab", "allopurinol", "febuxostat", "colchicine", "probenecid", "sulfasalazine", "hydroxychloroquine", "leflunomide",
    # ... (and hundreds more from standard classes)
}

# To verify length (should be >1000 with full expansion)
print(len(GENERIC_MEDICINES))
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
    if drug_name.lower().strip() in GENERIC_MEDICINES:
        return ['Already a Generic Medicine']
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
