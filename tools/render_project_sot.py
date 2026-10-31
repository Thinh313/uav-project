#!/usr/bin/env python3
"""Reviewable local SOT index from current registry; no remote assets or promotions."""
import html,json,os
from pathlib import Path
from collections import Counter
import yaml
ROOT=Path(__file__).resolve().parents[1];facts=[]
for file in ['product_truth.yaml','hera_context.yaml']:
 for f in yaml.safe_load((ROOT/'sot/registry'/file).read_text())['facts']:facts.append({**f,'registry_file':file})
escape=html.escape
rows=[]
for f in facts:
 v=f.get('value') if f.get('provenance_level')=='verified_primary' else f.get('claim')
 if isinstance(v,dict):
  if f['id']=='HERA.BOM.FORMULA_ERRORS':value=f"{v['count']} existing cached errors; see canonical context and workbook extraction."
  else:value=json.dumps(v,ensure_ascii=False)
 else:value='Unknown' if v is None else str(v)
 rows.append(f"<tr><td><code>{escape(f['id'])}</code><br>{escape(f['key'])}</td><td><span class='tag'>{escape(f['status'])}</span><small>{escape(f['provenance_level'])}</small></td><td>{escape(value)}<small>{escape(f['scope'])}</small></td><td>{escape(f['evidence'])}</td></tr>")
counts=Counter(f['status'] for f in facts)
text="""<!doctype html><html lang='vi'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>RtR Hera · Project SOT</title><style>body{margin:0;color:#151515;background:#fafafa;font:14px -apple-system,BlinkMacSystemFont,sans-serif}header{background:#0b0b0b;color:#fff;padding:36px 40px;border-bottom:3px solid #f2ca30}h1{font-size:32px;font-weight:500;margin:10px 0}header p{max-width:900px;line-height:1.7;color:#ccc}main{padding:28px 40px}nav{display:flex;gap:20px;margin:20px 0}a{color:inherit}table{width:100%;border-collapse:collapse;background:white}th,td{padding:15px;border:1px solid #ddd;vertical-align:top;text-align:left;line-height:1.6;overflow-wrap:anywhere}th{background:#111;color:white;font-weight:500}code{font-size:11px}small{display:block;color:#666;margin-top:8px;font-size:12px}.tag{font-size:11px;border:1px solid #aaa;padding:4px 6px;white-space:nowrap}td:nth-child(1){width:23%}td:nth-child(2){width:12%}td:nth-child(3){width:33%}td:nth-child(4){font-size:12px;color:#555}article{padding:18px 22px;border:1px solid #bbb;background:#fff;margin-bottom:24px;line-height:1.7}@media(max-width:760px){header,main{padding:22px}table{min-width:1000px}.scroll{overflow:auto}}</style><header><span>RtR / AERIS / HERA</span><h1>Project source of truth</h1><p>Owner: chủ việc RtR trong cuộc trò chuyện. Nội bộ · cập nhật 13/10/2026. Intent, BOM theo biến thể và khoảng trống tích hợp; claim không trở thành capability đã lắp.</p></header><main>"""
text+=f"<article><strong>{len(facts)} facts trong hai registry</strong><p>{escape(json.dumps(dict(counts),ensure_ascii=False))}</p>41 sheet BOM · 6.483 main-column rows · 32 lỗi cache có sẵn. Không cộng master/variant; không xác nhận cấu hình thực. Những fields chưa kiểm giữ verified_value=null. Độ sáng đủ theo quyết định owner, non-blocking.</article>"
links=[('Runbook/owner',ROOT/'sot/README.md'),('Current workflow contract',ROOT/'docs/ENDURE20-CONTRACT.md'),('BOM context canonical',ROOT/'sot/source_canonical/hera_context.json'),('BOM source',ROOT/'sot/source_canonical/0.BOM26.xlsx')]
text+='<nav>'+''.join(f"<a href='{escape(str(p))}'>{escape(title)}</a>" for title,p in links)+'</nav><div class="scroll"><table><thead><tr><th>Fact / identity</th><th>Status / provenance</th><th>Value hoặc claim · scope</th><th>Evidence / locator</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></main></html>'
out=ROOT/os.environ.get('AERIS_EVIDENCE_DIR','evidence/survey01')/'project-sot.review.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
print(json.dumps({'facts':len(facts),'status_counts':dict(counts),'review_html':str(out),'scope':'Local registry view; gate publication occurs after review/check'}))
