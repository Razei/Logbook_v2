import pandas as pd

df = pd.read_excel(r'Reports2020.xlsx', sheet_name='Sheet1', usecols='D')
print(df)
