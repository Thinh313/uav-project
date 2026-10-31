from pathlib import Path
import re,html,json
R=Path(__file__).resolve().parents[2];D=R/'delivery';E=R/'evidence/native98';v=json.loads((E/'final-verification.json').read_text());assert v['status']=='PARTIAL';md=(D/'COMPLETION-NATIVE98.md').read_text();parts=[]
def inline(s):
 s=html.escape(s);s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s);s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s);return re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
for block in md.strip().split('\n\n'):
 if block.startswith('# '):parts.append('<p class="eyebrow">RtR / AERIS · ENGINEERING</p><h1>NATIVE98</h1><p class="status">PARTIAL · Chưa nghiệm thu nhiệm vụ SITL</p>')
 elif block.startswith('## '):parts.append('<h2>'+inline(block[3:])+'</h2>')
 elif block.startswith('- '):parts.append('<ul>'+''.join('<li>'+inline(x[2:])+'</li>'for x in block.splitlines())+'</ul>')
 elif block.startswith('|'):
  lines=block.splitlines();parts.append('<div class="table"><table><thead><tr>'+''.join('<th>'+inline(x.strip())+'</th>'for x in lines[0].strip('|').split('|'))+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(x.strip())+'</td>'for x in l.strip('|').split('|'))+'</tr>'for l in lines[2:])+'</tbody></table></div>')
 else:parts.append('<p>'+inline(block)+'</p>')
css='''*{box-sizing:border-box}body{margin:0;background:#111715;color:#eaf0eb;font:16px/1.75 system-ui,sans-serif}main{max-width:1050px;margin:auto;padding:60px 36px 100px}h1{font-size:60px;letter-spacing:-2px;line-height:1;margin:18px 0}h2{font-size:24px;margin:40px 0 16px;border-top:1px solid #34413a;padding-top:24px}p,li,td{color:#bdccc1}strong{color:#f2f6f1}a{color:#ebd16c;text-decoration:none}a:hover{text-decoration:underline}code{font-size:.85em;background:#243027;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}.eyebrow{letter-spacing:2px;color:#ebd16c;font-size:12px;font-weight:700}.status{display:inline-block;border:1px solid #947d2e;color:#f4db84;border-radius:8px;padding:8px 12px;font-weight:700}.table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:14px;border-bottom:1px solid #34413a}th{color:#eaf0eb}li{margin:12px 0}@media(max-width:640px){main{padding:30px 18px}h1{font-size:44px}}'''
(D/'COMPLETION-NATIVE98.html').open('x').write('<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AERIS · NATIVE98 · PARTIAL</title><style>'+css+'</style><main>'+''.join(parts)+'</main></html>')
(D/'NATIVE98-LATEST.json').open('x').write(json.dumps({'milestone':'NATIVE98','status':'PARTIAL','apk':v['signedDevelopmentAPK'],'apkSha256':v['apkSha256'],'sourceId':v['sourceId'],'APK02Runtime':'NOT_CHECKED','requiredAirborneMission':'NOT_CHECKED','report':'delivery/COMPLETION-NATIVE98.html','verification':'evidence/native98/final-verification.json','productionSigned':False},indent=2))
print('PARTIAL_REPORT_RENDERED')
