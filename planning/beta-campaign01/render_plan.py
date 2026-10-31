"""Offline readable plan; no product runtime, network, build or dependency required."""
from pathlib import Path
import json,re,html,hashlib
R=Path(__file__).resolve().parents[2];P=R/'planning/beta-campaign01';D=R/'delivery';q=json.loads((P/'campaign.json').read_text());esc=html.escape
def inline(s):
 s=esc(s);s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s);s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s);s=re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',r'<a href="\2" rel="noreferrer">\1</a>',s);return s
def slug(s):return 'section-'+str(len(nav)+1)
nav=[];out=[];lines=(P/'MASTERPLAN.md').read_text().splitlines();i=0
while i<len(lines):
 s=lines[i]
 if s.startswith('```'):
  buf=[];i+=1
  while i<len(lines)and not lines[i].startswith('```'):buf.append(lines[i]);i+=1
  out.append('<pre><code>'+esc('\n'.join(buf))+'</code></pre>');i+=1;continue
 if s.startswith('|'):
  table=[]
  while i<len(lines)and lines[i].startswith('|'):
   row=[v.strip()for v in lines[i].strip().strip('|').split('|')]
   if not all(re.fullmatch(r'[:\-\s]+',v)for v in row):table.append(row)
   i+=1
  out.append('<div class="table"><table><thead><tr>'+''.join('<th>'+inline(x)+'</th>'for x in table[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(x)+'</td>'for x in row)+'</tr>'for row in table[1:])+'</tbody></table></div>');continue
 m=re.match(r'^(#{1,3}) (.+)$',s)
 if m:
  level=len(m[1]);title=m[2]
  if level==1:out.append('<h1>'+inline(title)+'</h1>')
  elif level==2:
   ident=slug(title);nav.append((ident,title));out.append('<h2 id="'+ident+'">'+inline(title)+'</h2>')
  else:out.append('<h3>'+inline(title)+'</h3>')
  i+=1;continue
 if re.match(r'^(- |\d+\. )',s):
  ordered=bool(re.match(r'^\d+\. ',s));tag='ol'if ordered else'ul';buf=[]
  while i<len(lines)and re.match(r'^'+(r'\d+\. 'if ordered else'- '),lines[i]):buf.append(re.sub(r'^(?:- |\d+\. )','',lines[i]));i+=1
  out.append('<'+tag+'>'+''.join('<li>'+inline(x)+'</li>'for x in buf)+'</'+tag+'>');continue
 if s.strip():
  buf=[s];i+=1
  while i<len(lines)and lines[i].strip()and not re.match(r'^(#|\||```|- |\d+\. )',lines[i]):buf.append(lines[i]);i+=1
  out.append('<p>'+inline(' '.join(buf))+'</p>');continue
 i+=1
def table(headers,rows):return '<div class="table"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>'for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(str(c))+'</td>'for c in row)+'</tr>'for row in rows)+'</tbody></table></div>'
extra='<h2 id="contracts">Phụ lục A · 28 yêu cầu MUST</h2><p>Toàn bộ là NOT_CHECKED trên campaign mới. Source cũ có thể là nền, không tự cấp PASS.</p>'+table(['ID','Mốc','Yêu cầu','Nghiệm thu'],[[r['id'],r['milestone'],r['title'],r['acceptance']]for r in q['requirements']])
extra+='<h2 id="cases">Phụ lục B · 48 nhóm case</h2><p>Đây là case design, chưa là test executable hoặc kết quả. Sáu polygon/corridor case có repeat3 tạo18 nominal missions; không nhân tất cả profile/seed thành tuyên bố số lần đã bay.</p>'+table(['ID','Bài kiểm','Lớp','REQ','Phương pháp','Expected'],[[c['id'],c['title'],c['layer'],', '.join(c['requirements']),c['method'],c['expected']]for c in q['cases']])
extra+='<h2 id="mapping">Phụ lục C · Ánh xạ 48 nhóm chức năng</h2>'+table(['ID','Chức năng','Phạm vi beta','REQ'],[[f['featureID'],f['title'],f['scope'],', '.join(f['requirementIDs'])]for f in q['featureMapping']])
extra+='<h2 id="tasks">Phụ lục D · 22 work package</h2>'+table(['Task','Mốc','Dependency','Công việc','Đầu ra'],[[t['id'],t['milestone'],', '.join(t['dependsOn'])or'—',t['work'],t['deliverable']]for t in q['taskGraph']])
extra+='<h2 id="sources">Nguồn và provenance</h2><p>Primary references định nghĩa giao thức/hành vi công bố; target AERIS là đề xuất engineering. Các tài liệu này không chứng nhận AERIS an toàn, tốt hơn DJI hoặc tương thích mọi thiết bị.</p><ul>'+''.join('<li><a href="'+esc(s['url'])+'">'+esc(s['title'])+'</a>: '+esc(s['use'])+'</li>'for s in q['sources'])+'</ul>'
nav+= [('contracts','A · Yêu cầu MUST'),('cases','B · Corpus'),('mapping','C · 48 chức năng'),('tasks','D · Work package'),('sources','Nguồn / provenance')]
doc='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AERIS · Beta Campaign 01</title><style>*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:#f4f4ef;color:#202521;font:16px/1.7 system-ui,-apple-system,sans-serif}header{background:#17201b;color:#fff;padding:24px 34px;display:flex;justify-content:space-between;gap:22px;align-items:center}.brand{font-weight:850;font-size:28px;font-style:italic}.stamp{font-size:12px;font-weight:750;border:1px solid #a9b3a9;padding:6px 12px;color:#efdb84}main{max-width:1560px;margin:auto;display:grid;grid-template-columns:250px minmax(0,1fr);gap:36px;padding:30px 28px 70px}aside{position:sticky;top:20px;align-self:start;max-height:92vh;overflow:auto;font-size:13px}aside a{display:block;text-decoration:none;color:#465248;border-left:2px solid #d9ded6;padding:7px 12px}aside a:hover{border-color:#9c811f;background:#eee8d4}article{min-width:0;max-width:1140px}h1{font-size:clamp(32px,4vw,52px);line-height:1.12;letter-spacing:-1.4px;margin:10px 0 18px}h2{font-size:27px;line-height:1.3;margin:48px 0 16px;letter-spacing:-.6px;padding-top:15px;border-top:1px solid #cbd3c8}h3{font-size:20px;margin-top:30px}p{margin:13px 0}li{margin:9px 0}a{color:#445124;text-underline-offset:3px}strong{font-weight:750}.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#cad2c6;border:1px solid #cad2c6;margin:0 0 20px}.summary div{background:#fbfcf8;padding:17px}.summary b{font-size:30px;display:block}.summary small{font-size:12px;color:#5d695e}.callout{border-left:4px solid #baa348;background:#eeead8;padding:15px 20px;margin:20px 0}.downloads{display:flex;gap:14px;flex-wrap:wrap;font-size:14px}.table{max-width:100%;overflow-x:auto;margin:20px 0}table{width:100%;border-collapse:collapse;min-width:650px;font-size:13px}th{background:#223329;color:#fff;text-align:left;vertical-align:top;padding:12px}td{padding:12px;vertical-align:top;border-bottom:1px solid #d4dace;overflow-wrap:anywhere}tr:nth-child(even){background:#eeefe8}code{font:13px/1.6 ui-monospace,monospace;background:#e6e9df;border-radius:3px;padding:1px 4px;overflow-wrap:anywhere}pre{overflow:auto;background:#17231c;color:#e4eee4;padding:22px;border-radius:6px;font-size:12px;line-height:1.65}pre code{background:none;color:inherit;padding:0;white-space:pre}footer{border-top:1px solid #ccd1c5;padding:25px;margin-top:40px;font-size:13px;color:#4f5a50}@media(max-width:1000px){main{grid-template-columns:1fr;padding:22px 18px}aside{position:static;max-height:220px;display:grid;grid-template-columns:1fr 1fr}header{padding:20px}.summary{grid-template-columns:1fr 1fr}h2{font-size:24px}}@media print{body{background:#fff;font-size:11pt}header{background:#fff;color:#000}main{display:block;padding:0}aside,.downloads{display:none}h1{font-size:28pt}h2{break-after:avoid;font-size:18pt}.table{overflow:visible}table{min-width:0;font-size:9pt}tr{break-inside:avoid}pre{white-space:pre-wrap}.summary div{background:#fff}.stamp{color:#000}}</style><header><div><span class="brand">RtR</span>　AERIS / BETA CAMPAIGN 01</div><span class="stamp">KẾ HOẠCH · CHƯA TRIỂN KHAI</span></header><main><aside>'''+''.join('<a href="#'+ident+'">'+esc(title)+'</a>'for ident,title in nav)+'''</aside><article><div class="summary"><div><small>Milestone sản phẩm</small><b>7</b></div><div><small>Yêu cầu MUST</small><b>28</b></div><div><small>Nhóm kịch bản</small><b>48</b></div><div><small>Quality contracts</small><b>13</b></div></div><div class="callout"><strong>Một phiên bản tích hợp phải vượt tất cả gate bắt buộc.</strong><br>Beta giả lập trên Android, khả năng cài trên thiết bị và vận hành Hera thật là ba phạm vi nghiệm thu riêng. Không lấy tổng module hoặc PASS từ nhiều APK làm beta hoàn chỉnh.</div><p class="downloads"><a href="../planning/beta-campaign01/MASTERPLAN.md">Đọc Markdown</a><a href="../planning/beta-campaign01/campaign.json">Campaign JSON</a><a href="../planning/beta-campaign01/TIP-M0.md">Bắt đầu M0</a><a href="../planning/beta-campaign01/PLAN-VALIDATION.json">Kiểm nhất quán kế hoạch</a></p>'''+''.join(out)+extra+'''<footer>Ngày lập 26/10/2026 · Asia/Ho_Chi_Minh · Vibecode6.3 + PRD. Đề xuất kiến trúc của assistant; chưa có independent human flight review. Không build/sign APK, chạy Android/SITL, tạo campaign24h hoặc sửa source/candidate/ENDURE khi lập kế hoạch này. Validation chỉ kiểm kế hoạch, không xác nhận sản phẩm PASS.</footer></article></main></html>'''
(D/'PLAN-BETA-CAMPAIGN01.html').open('x').write(doc)
print(json.dumps({'html':'delivery/PLAN-BETA-CAMPAIGN01.html','bytes':len(doc.encode()),'masterplanBytes':(P/'MASTERPLAN.md').stat().st_size,'status':'PLAN_ONLY'},indent=2))
