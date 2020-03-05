import pandas as pd

df = pd.read_excel(r'Report Log 2020.xlsx', sheet_name='January')

for index, column in df.iterrows():
    print(column)

print(' ')