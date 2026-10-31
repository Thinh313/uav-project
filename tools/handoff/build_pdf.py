"""Rebuild the grayscale handoff guide from the editable Markdown chapters.
Requires reportlab. Fonts are repository-owned OFL Barlow assets; no downloads.
"""
from pathlib import Path
import re,html,textwrap,json
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether,HRFlowable,CondPageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[2];O=R/'output/pdf/UAV-PROJECT-HANDOVER.pdf';O.parent.mkdir(parents=True,exist_ok=True)
F=R/'native/betasim-integrated01/assets/fonts'
for n,file in [('Body','Barlow-Medium.ttf'),('Bold','Barlow-Bold.ttf'),('Semi','Barlow-SemiBold.ttf')]:pdfmetrics.registerFont(TTFont(n,str(F/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
S={
 'body':ParagraphStyle('body',fontName='Body',fontSize=11.4,leading=16,spaceAfter=8,textColor=colors.black),
 'h1':ParagraphStyle('h1',fontName='Bold',fontSize=25,leading=30,spaceAfter=16,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='Semi',fontSize=15,leading=20,spaceBefore=12,spaceAfter=8,keepWithNext=True),
 'small':ParagraphStyle('small',fontName='Body',fontSize=9,leading=12,spaceAfter=6,textColor=colors.HexColor('#4b4b4b')),
 'table':ParagraphStyle('table',fontName='Body',fontSize=9.5,leading=13,spaceAfter=1),
 'code':ParagraphStyle('code',fontName='Courier',fontSize=8,leading=11,spaceAfter=0),
 'title':ParagraphStyle('title',fontName='Bold',fontSize=38,leading=42,spaceAfter=20),
 'kicker':ParagraphStyle('kicker',fontName='Semi',fontSize=11,leading=15,spaceAfter=12,textColor=colors.HexColor('#555555')),
}
def rich(s):
 s=s.replace('\u2014',':').replace('\u2013','-').replace('\u2011','-')
 # Protect the final two prose words, including headings/cells. Technical identifiers
 # may wrap and are recorded separately by PDF QA.
 bits=s.rsplit(' ',1)
 if len(bits)==2:s='\u00a0'.join(bits)
 s=html.escape(s).replace('&lt;br/&gt;','<br/>')
 s=re.sub(r'`([^`]+)`',lambda m:'<font name="Courier" size="8.5">'+m.group(1)+'</font>',s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:'<b>'+m.group(1)+'</b>',s)
 return s
P=lambda s,kind='body':Paragraph(rich(s),S[kind])
class Numbered(canvas.Canvas):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.states=[]
 def showPage(self):self.states.append(dict(self.__dict__));self._startPage()
 def save(self):
  total=len(self.states)
  for state in self.states:
   self.__dict__.update(state);w,h=A4;self.setFillColor(colors.HexColor('#4b4b4b'));self.setFont('Body',8.5)
   self.drawString(52,h-31,'RtR  /  AERIS  /  RESEARCH HANDOFF')
   self.setStrokeColor(colors.HexColor('#bbbbbb'));self.setLineWidth(.4);self.line(52,h-40,w-52,h-40)
   self.drawString(52,29,'31.10.2026  |  Engineering alpha - beta NOT READY')
   self.drawRightString(w-52,29,f'{self._pageNumber} / {total}');super().showPage()
  super().save()
def markdown(text):
 lines=text.splitlines();flows=[];i=0;para=[]
 def flush():
  if para:flows.append(P(' '.join(para)));para.clear()
 while i<len(lines):
  l=lines[i].strip()
  if l.startswith('```'):
   flush();block=[];i+=1
   while i<len(lines)and not lines[i].strip().startswith('```'):block.append(lines[i]);i+=1
   cooked=[]
   for item in block:
    cooked+=textwrap.wrap(item,width=94,break_long_words=True,break_on_hyphens=False,replace_whitespace=False,drop_whitespace=False) or [' ']
   content='<br/>'.join(html.escape(x).replace(' ','&#160;')for x in cooked)
   t=Table([[Paragraph(content,S['code'])]],colWidths=[491]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f1f1f1')),('BOX',(0,0),(-1,-1),.4,colors.HexColor('#bbbbbb')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]));flows.extend([t,Spacer(1,10)]);i+=1;continue
  if l.startswith('|'):
   flush();rows=[]
   while i<len(lines)and lines[i].strip().startswith('|'):
    row=[c.strip()for c in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r':?-+:?',c or' ')for c in row):rows.append(row)
    i+=1
   n=len(rows[0]);widths=[105,180,206]if n==3 else [491/n]*n
   t=Table([[P(c,'table')for c in row]for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
   t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5e5e5')),('LINEBELOW',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#cccccc')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));flows.extend([t,Spacer(1,12)]);continue
  if l.startswith('# '):flush();flows.append(P(l[2:],'h1'))
  elif l.startswith('## '):flush();flows.append(P(l[3:],'h2'))
  elif l.startswith('- ')or re.match(r'^\d+\. ',l):
   flush();item=l;i+=1
   while i<len(lines)and lines[i].strip()and not re.match(r'^(?:#|- |\d+\. |```|\|)',lines[i].strip()):item+=' '+lines[i].strip();i+=1
   flows.append(P(item));continue
  elif not l:flush()
  else:para.append(l)
  i+=1
 flush();return flows
story=[]
story+=[Spacer(1,43),P('ANH GỬI CÁC EM','kicker'),P('UAV PROJECT<br/>AERIS','title'),P('Hồ sơ chuyển giao nghiên cứu và phát triển','h2'),P('Source hiện tại, cách tái lập, bằng chứng và lộ trình hoàn thiện sản phẩm.'),Spacer(1,16)]
box=Table([[P('ENGINEERING ALPHA','h2')],[P('Beta tích hợp chưa đạt. Mục đích của bản này là tiếp nhận và tiếp tục R&D; chưa là bản phát hành vận hành máy bay thật.')]],colWidths=[491]);box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f1f1f1')),('BOX',(0,0),(-1,-1),.7,colors.black),('LEFTPADDING',(0,0),(-1,-1),16),('RIGHTPADDING',(0,0),(-1,-1),16),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]));story+=[box,Spacer(1,22),P('Mốc bàn giao: 31/10/2026. Repo public: github.com/nclamvn/uav-project. Tag tiếp nhận: research-runtime-2026-10-31-r2.'),P('Anh gửi các em bộ source có đối chiếu, hướng dẫn và các gói private đi kèm. Anh mong nhóm chủ động tiếp nhận, phát triển theo outcome và giữ rõ ranh giới giữa điều đã chứng minh, điều mới mô phỏng và điều còn chưa biết.'),P('Bản source gốc: 6ea4f5027bc93d4f67e10da53c098391d9553f2f. Lịch sử private không được nhập vào repo public.','small'),PageBreak()]
chapters=[('HANDOVER.md','01'),('CONTENTS.md','02'),('STATUS.md','03'),('ARCHITECTURE.md','04'),('SETUP-AND-VERIFY.md','05'),('NEXT-MILESTONE.md','06'),('ACCEPTANCE.md','07'),('INTAKE01.md','08'),('MILESTONE05.md','09'),('MESSAGE-TO-TEAM.md','10')]
for index,(name,n)in enumerate(chapters):
 story.append(P('PHẦN '+n,'kicker'));story+=markdown((R/'docs/handoff'/name).read_text())
 if index<len(chapters)-1:story.extend([Spacer(1,16),HRFlowable(width='100%',thickness=.5,color=colors.HexColor('#bbbbbb')),Spacer(1,12),CondPageBreak(180)])
story.append(PageBreak());story.append(P('PHỤ LỤC KỸ THUẬT','kicker'));story.append(P('Định danh và bản đồ đọc source','h1'))
for label,value in [('Source nền','6ea4f5027bc93d4f67e10da53c098391d9553f2f'),('Candidate S01','afe0878d1b98751f66c657c8eed6653d28d59778c46de012b2a16e8a8ef43395'),('APK development','8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1'),('AP executable','77344f3c6f715cb326b99356815e8315769e9331dcb1e4c88bc4076804cb0d53')]:story.extend([P(label,'h2'),P('`'+value+'`')])
story.append(P('Các em đối chiếu SHA của file thực, không chỉ tên file hoặc tag. Image ID, SHA archive và SHA executable là các loại định danh khác nhau. Thông số platform/API/firmware chỉ hợp lệ với cấu hình và phạm vi đã ghi.'))
story.append(P('Bản đồ tài liệu','h2'))
for s in ['README.md: clone, kiểm nhanh và giới hạn.', 'docs/handoff/: tài liệu biên tập có thể cập nhật.', 'handoff/SOURCE-MANIFEST.json: cây public và checksum.', 'handoff/VALIDATION.json: kết quả kiểm bản chuyển giao.', 'planning/vidlife12/TIP-ADR.md: contract và điều kiện kiểm.', 'delivery/COMPLETION-VIDLIFE12.md: kết luận milestone gốc.', 'NOTICE.md và reference/DEPENDENCIES.md: giấy phép/nguồn thành phần.']:story.append(P(s))
story.append(P('Lưu ý trình bày','h2'));story.append(P('Các identifier, SHA, URL và lệnh dài có thể xuống dòng trình bày; khi chạy, các em dùng bản Markdown hoặc source gốc trong repo. Việc xuống dòng kỹ thuật không thay đổi giá trị định danh.'))
SimpleDocTemplate(str(O),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=58,bottomMargin=51,title='UAV Project - AERIS - Ho so chuyen giao nghien cuu',author='Nguoi ban giao du an',subject='Research handoff; engineering alpha, integrated beta not ready').build(story,canvasmaker=Numbered)
print(O)
