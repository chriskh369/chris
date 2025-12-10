import openpyxl
import sys
sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook(r'c:\Users\Chris\OneDrive\מסמכים\GitHub\chris\college\Book1.xlsx')
ws = wb.active

for row in ws.iter_rows():
    values = [str(c.value) if c.value else '' for c in row]
    print('\t'.join(values))
