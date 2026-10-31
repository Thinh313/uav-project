#!/usr/bin/env python3
"""Compare every extracted cell/formula/error to owner XLSX through a fresh two-pass read."""
import hashlib,json
from pathlib import Path
import openpyxl
ROOT=Path(__file__).resolve().parents[1];book=json.loads((ROOT/'hardware/hera/bom/workbook.json').read_text());p=Path(book['source'])
assert hashlib.sha256(p.read_bytes()).hexdigest()==book['sha256']
f=openpyxl.load_workbook(p,read_only=True,data_only=False);v=openpyxl.load_workbook(p,read_only=True,data_only=True)
assert f.sheetnames==[s['name'] for s in book['sheets']]
checked=0
for data in book['sheets']:
 s=f[data['name']];value_rows=list(v[s.title].iter_rows());captured={c['cell']:c for c in data['cells']}
 assert s.sheet_state==data['state']
 for row in s:
  for c in row:
   if c.value is None:continue
   actual=value_rows[c.row-1][c.column-1];value=actual.value.isoformat() if hasattr(actual.value,'isoformat') else actual.value;r=captured.pop(c.coordinate)
   assert r['value']==value and r['data_type']==actual.data_type,(s.title,c.coordinate)
   assert r.get('formula')==(c.value if c.data_type=='f' else None),(s.title,c.coordinate,'formula')
   checked+=1
 assert not captured,'Extraneous extracted cells'
f.close();v.close();print(json.dumps({'status':'PASS','nonempty_cells_checked':checked,'sheet_count':len(book['sheets']),'scope':'Fresh read of source cells, cached values and formulas; no recalculation or installed hardware assertion'}))
