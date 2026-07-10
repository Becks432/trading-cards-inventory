import pandas as pd
import json

xls = pd.ExcelFile(r'C:\Users\Admin\Desktop\Purchase Log.xlsx')
df = pd.read_excel(xls, sheet_name='Collection')

for_sale = df[df['Status'].str.contains('For Sale', na=False)].copy()

cols = ['Player Label', 'Set Name', 'Variant', 'Value', 'Number', 'product-name', 'grading-cert-id', 'id']
for_sale = for_sale[cols].rename(columns={
    'Player Label': 'Player',
    'Set Name': 'Set',
    'Variant': 'Variant',
    'Value': 'Value',
    'Number': 'Card Number',
    'id': 'id',
    'grading-cert-id': 'Item #'
})

for_sale['Value'] = pd.to_numeric(for_sale['Value'], errors='coerce')
for_sale = for_sale[for_sale['Value'] > 0]

data = for_sale.to_dict(orient='records')

with open(r'C:\Users\Admin\Desktop\cards_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Exported {len(data)} cards")
print("Sample:", data[0] if data else "No data")