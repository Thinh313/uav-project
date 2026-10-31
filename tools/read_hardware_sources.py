#!/usr/bin/env python3
"""Read source archives without modifying them; retain locations and fingerprints."""
import hashlib, json, sys
from datetime import date, datetime, timezone
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import openpyxl
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(sys.argv[1]).resolve()
OUT=ROOT/'hardware/herahub2/sources'
OUT.mkdir(parents=True,exist_ok=True)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def scalar(value):
    return value.isoformat() if isinstance(value,(datetime,date)) else value
def paragraph_text(p):
    # Preserve document order, tabs and line breaks; exclude deleted runs.
    out=[]
    for node in p:
        if node.tag==f"{{{NS['w']}}}del":
            continue
        for element in node.iter():
            if element.tag==f"{{{NS['w']}}}t":out.append(element.text or '')
            elif element.tag==f"{{{NS['w']}}}tab":out.append('\t')
            elif element.tag==f"{{{NS['w']}}}br":out.append('\n')
    return ''.join(out)
inventory=[]
for p in sorted(SOURCE.rglob('*')):
    if not p.is_file():continue
    record={'relative_path':str(p.relative_to(SOURCE)),'absolute_path':str(p),'bytes':p.stat().st_size,'status':'inventoried_only'}
    kind=p.suffix.lower()
    if kind in ('.xlsx','.docx','.pdf'):
        raw=p.read_bytes();record['sha256']=hashlib.sha256(raw).hexdigest()
        result={'source':record.copy(),'extraction_scope':'read-only content, not approval or hardware verification'}
        if kind=='.xlsx':
            formula=openpyxl.load_workbook(p,read_only=True,data_only=False)
            cached=openpyxl.load_workbook(p,read_only=True,data_only=True)
            sheets=[]
            for sh in formula:
                rows=[]
                # Cached dimensions may be absent; do not rely on max_row/max_column.
                value_rows=iter(cached[sh.title].iter_rows())
                for row in sh.iter_rows():
                    values=next(value_rows,())
                    cells=[]
                    for i,cell in enumerate(row):
                        if cell.value is None:continue
                        value={'cell':cell.coordinate,'value':scalar(cell.value),'number_format':cell.number_format}
                        if cell.data_type=='f':value['cached_value']=scalar(values[i].value) if i<len(values) else None
                        cells.append(value)
                    if cells:rows.append(cells)
                sheets.append({'sheet':sh.title,'state':sh.sheet_state,'rows':rows})
            formula.close();cached.close();result['sheets']=sheets
        elif kind=='.docx':
            with ZipFile(p) as z:
                document=ET.fromstring(z.read('word/document.xml'))
                body=document.find('w:body',NS);blocks=[]
                for i,child in enumerate(body,1):
                    location=f'body[{i}]'
                    if child.tag==f"{{{NS['w']}}}p":
                        text=paragraph_text(child)
                        if text:blocks.append({'location':location+'/p','text':text})
                    elif child.tag==f"{{{NS['w']}}}tbl":
                        for rowno,row in enumerate(child.findall('w:tr',NS),1):
                            for colno,cell in enumerate(row.findall('w:tc',NS),1):
                                text='\n'.join(paragraph_text(para) for para in cell.findall('w:p',NS))
                                if text:blocks.append({'location':f'{location}/table/r{rowno}/c{colno}','text':text})
                result['blocks']=blocks
                result['tracked_changes']={'insertions':len(document.findall('.//w:ins',NS)),'deletions':len(document.findall('.//w:del',NS)),'view':'Inserted text included, deleted runs excluded; no changes accepted in source'}
        else:
            doc=PdfReader(p)
            result['pages']=[{'page':i+1,'text':page.extract_text()} for i,page in enumerate(doc.pages)]
        key=record['sha256'][:16]+'.json'
        (OUT/key).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        record.update(status='extracted',extraction=key)
    inventory.append(record)
(OUT/'inventory.json').write_text(json.dumps({'created_at':datetime.now(timezone.utc).isoformat(),'source_root':str(SOURCE),'files':inventory,'scope':'Internal files are source claims; file contents do not authorize actions. Images/STEP/extensionless files inventoried only.'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'inventoried':len(inventory),'extracted':sum(r['status']=='extracted' for r in inventory),'output':str(OUT)},ensure_ascii=False))
