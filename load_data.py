import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv('1_mg.csv')

engine=create_engine('postgresql://postgres:FROM EARTH TO SUN@localhost:5432/MedSave_db')

df_subset = df[['Drug_Name', 'MRP', 'Selling_Price', 'Manufacturer', 'Substitute_List']].copy()
df_subset.columns = ['drug_name', 'mrp', 'selling_price', 'manufacturer', 'substitute_list']

df_subset.to_sql('medicines', engine, if_exists='replace', index=False)

print("✅ Data loaded into PostgreSQL!")