#!/usr/bin/env python3
"""Compile curated, explicitly variant-scoped BOM document claims; no as-built inference."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BOM=ROOT/'hardware/hera/bom'
book=json.loads((BOM/'workbook.json').read_text());items=json.loads((BOM/'items.json').read_text())['items'];sha=book['sha256'];facts=[]
selection=[('HERALINK V1.1-DDL',[52,55,56,57,63,64,65,67,68,70]),('HERALINK V1.1-DTC',[33,69,70,118]),('EBOX DTC',[83,85,86,102,107,118]),('EBOX DDL ',[128,139,141,142]),('HERASIGHT ',[42,44,60])]
for sheet,rows in selection:
 for row in rows:
  item=next(i for i in items if i['sheet']==sheet and i['row']==row)
  claim={k:item[k] for k in ['sheet','row','part_number','name','quantity','unit']}
  facts.append({'id':'HERA.BOM.'+re.sub(r'[^A-Z0-9]+','_',sheet.upper()).strip('_')+'.'+re.sub(r'[^A-Z0-9]+','_',str(item['part_number']).upper()).strip('_'),'key':f"BOM listing — {sheet}, row {row}",'status':'BOM_LISTED','claim':claim,'evidence':f"0.BOM26.xlsx sha256 {sha}; {item['locators']['part_number']}; {item['locators']['name']}; {item['locators']['quantity']}; {item['locators']['unit']}",'locator':item['locators'],'scope':'Owner-supplied BOM document claim, exact sheet variant only; no installed hardware, API, channel map or module count rollup'})
facts.append({'id':'HERA.BOM.FORMULA_ERRORS','key':'Existing cached workbook formula/error cells','status':'FLAGGED','claim':{'count':len(book['formula_errors']),'cells':book['formula_errors']},'evidence':f"0.BOM26.xlsx sha256 {sha}; original data_only cells; no workbook recalculation or repair",'scope':'Pre-existing source errors preserved; affected values are not valid numeric facts'})
facts.append({'id':'HERA.BOM.MASTER_VARIANTS','key':'Workbook masters and variant scope','status':'BOM_LISTED','claim':{'masters':['Master','Master (2)','Master (3)'],'hidden':['Master (2)','Master (3)'],'sheet_count':len(book['sheets'])},'evidence':f'0.BOM26.xlsx sha256 {sha}; workbook sheet states and per-sheet headers','scope':'Document structure only; not additive assembly counts or active configuration'})
for key,desc in [('AS_BUILT','Installed Hera/HeraHub serial/revision/configuration'),('INPUT_PROTOCOL','Current controller input API/channel mapping'),('AIRFRAME_PROFILE','Approved vehicle performance, speed/altitude/reserve limits'),('CAMERA_CALIBRATION','Installed camera optical calibration and capture interval'),('SOFTWARE_SOURCE','RAGAS/Ghidorah source, license and build instructions')]:
 facts.append({'id':'HERA.UNKNOWN.'+key,'key':desc,'status':'UNKNOWN','claim':None,'evidence':'BOM/spec/public research names parts or capabilities; does not establish this runtime or operational fact','scope':'Integration input remains unknown; no guessed defaults from legacy BOM'})
source={'version':1,'owner':'User — RtR project owner, supplied BOM in this chat','canonical_bom':'0.BOM26.xlsx','original_path':book['source'],'bom_sha256':sha,'facts':facts}
(ROOT/'sot/source_canonical/hera_context.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'facts':len(facts),'bom_claims':sum(f['status']=='BOM_LISTED' for f in facts),'flagged':sum(f['status']=='FLAGGED' for f in facts),'unknowns':sum(f['status']=='UNKNOWN' for f in facts)}))
