import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv('Medicine.csv')
df2=pd.read_csv('Jan_Aushadhi.csv')

engine=create_engine('postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db')

df_medicine_subset = df[['name', 'price', 'short_composition1', 'short_composition2']].copy()
df_medicine_subset.columns = ['drug_name', 'mrp', 'generic_med1', 'generic_med2']

df_medicine_subset.to_sql('medicine', engine, if_exists='replace', index=False)


df_jan_subset=df2[['Generic Name','Unit Size','MRP']]
df_jan_subset.columns=['drug_name','unit_size','mrp']

df_jan_subset.to_sql('jan_aushadhi', engine, if_exists='replace', index=False)
print("✅ Data loaded into PostgreSQL!")