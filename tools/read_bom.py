#!/usr/bin/env python3
"""Read-only two-pass BOM extraction; no recalc or modification of owner workbook."""
import hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
import openpyxl
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/os/Downloads/0.BOM26.xlsx')
OUT=ROOT/'hardware/hera/bom';OUT.mkdir(parents=True,exist_ok=True)
MIRROR=ROOT/'sot/source_canonical/0.BOM26.xlsx'
sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if MIRROR.exists():
 assert hashlib.sha256(MIRROR.read_bytes()).hexdigest()==sha,'Existing canonical BOM changed; review before replacing'
else:shutil.copyfile(SOURCE,MIRROR)
f=openpyxl.load_workbook(SOURCE,data_only=False,read_only=True)
v=openpyxl.load_workbook(SOURCE,data_only=True,read_only=True)
book={'source':str(SOURCE),'canonical':'sot/source_canonical/0.BOM26.xlsx','sha256':sha,'captured_at':datetime.now(timezone.utc).isoformat(),'owner':'User — RtR project owner, supplied in this chat','scope':'Document contents only; not installed/as-built configuration','sheets':[]}
items=[];errors=[];uncached=[]
def plain(x):
 if hasattr(x,'isoformat'):return x.isoformat()
 return x
for sheet in f:
 value_rows=list(v[sheet.title].iter_rows());cells=[];count_f=0
 header={str(c.value).strip().casefold():c.column for c in next(sheet.iter_rows(min_row=3,max_row=3),[]) if c.value is not None and c.column<=24}
 mapping={k:header.get(label) for k,label in [('module','module'),('level','lvl'),('drawing','pn/dwr'),('part_name','part name'),('description_vi','tên tiếng việt'),('part_number','part number'),('name','p name'),('description','desc'),('quantity','qty'),('unit','unit'),('material','material'),('revision_raw','rev')]}
 pncol=mapping['part_number'];qtycol=mapping['quantity']
 for row_no,row in enumerate(sheet,start=1):
  rd={}
  for c in row:
   if c.value is None:continue
   vc=value_rows[c.row-1][c.column-1];r={'cell':c.coordinate,'value':plain(vc.value),'data_type':vc.data_type,'number_format':c.number_format}
   if c.data_type=='f':
    r['formula']=c.value;count_f+=1
    if vc.value is None:uncached.append({'sheet':sheet.title,'cell':c.coordinate,'formula':c.value})
   if vc.data_type=='e':errors.append({'sheet':sheet.title,'cell':c.coordinate,'error':vc.value,'formula':c.value if c.data_type=='f' else None})
   cells.append(r);rd[c.column]=r
  # Infer columns from each sheet's actual header, including shifted hidden masters.
  if pncol in rd and str(rd[pncol]['value'] or '').strip() and row_no>=4:
   part=str(rd[pncol]['value']).strip()
   if part.lower() not in ['part number','part number change history']:
    data={k:rd.get(col,{}).get('value') for k,col in mapping.items()}
    data.update(id='BOM.'+hashlib.sha256(f'{sheet.title}|{row_no}|{part}'.encode()).hexdigest()[:16],sheet=sheet.title,row=row_no,source_sha256=sha,provenance_level='claim',verified_value=None)
    data['locators']={k:f"'{sheet.title}'!{openpyxl.utils.get_column_letter(col)}{row_no}" for k,col in mapping.items() if col}
    data['quantity_state']='cached_error' if rd.get(qtycol,{}).get('data_type')=='e' else 'missing' if data['quantity'] is None else 'source_claim'
    if qtycol in rd and 'formula' in rd[qtycol]:data['quantity_formula']=rd[qtycol]['formula']
    items.append(data)
 book['sheets'].append({'name':sheet.title,'state':sheet.sheet_state,'rows':sheet.max_row,'columns':sheet.max_column,'formulas':count_f,'column_map':mapping,'cells':cells})
f.close();v.close()
book['formula_errors']=errors;book['formula_missing_cache']=uncached
(OUT/'workbook.json').write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n')
(OUT/'items.json').write_text(json.dumps({'source_sha256':sha,'scope':'Sheet-scoped BOM rows; masters/variants are not deduplicated or summed; no BOM total or as-built inference','items':items},ensure_ascii=False,indent=2)+'\n')
summary={'sha256':sha,'bytes':SOURCE.stat().st_size,'sheet_count':len(book['sheets']),'formula_count':sum(s['formulas'] for s in book['sheets']),'cached_errors':len(errors),'missing_formula_cache':len(uncached),'bom_rows':len(items),'by_sheet':{s['name']:sum(i['sheet']==s['name'] for i in items) for s in book['sheets']},'original_preserved':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==sha}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='by_sheet'},ensure_ascii=False))
