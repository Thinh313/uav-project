"""Build the current grayscale H10 handoff PDF from editable Markdown.
Use an existing Python with reportlab; no downloads, SDK or runtime actor.
"""
from pathlib import Path
import html,re,textwrap
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,HRFlowable,CondPageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[2]
O=R/'output/pdf/UAV-PROJECT-HANDOVER.pdf';O.parent.mkdir(parents=True,exist_ok=True)
F=R/'native/betasim-integrated01/assets/fonts'
for name,filename in [('Body','Barlow-Medium.ttf'),('Bold','Barlow-Bold.ttf'),('Semi','Barlow-SemiBold.ttf')]:
 pdfmetrics.registerFont(TTFont(name,str(F/filename)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
W=491
S={
 'body':ParagraphStyle('body',fontName='Body',fontSize=11.1,leading=15.4,spaceAfter=7.5,textColor=colors.black,allowWidows=0,allowOrphans=0),
 'h1':ParagraphStyle('h1',fontName='Bold',fontSize=22,leading=27,spaceAfter=14,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='Semi',fontSize=13.5,leading=17.5,spaceBefore=11,spaceAfter=7,keepWithNext=True),
 'small':ParagraphStyle('small',fontName='Body',fontSize=9,leading=12.5,spaceAfter=6,textColor=colors.HexColor('#4a4a4a')),
 'table':ParagraphStyle('table',fontName='Body',fontSize=9.1,leading=12.4,spaceAfter=1),
 'code':ParagraphStyle('code',fontName='Courier',fontSize=7.7,leading=10.7,spaceAfter=0),
 'title':ParagraphStyle('title',fontName='Bold',fontSize=35,leading=40,spaceAfter=18),
 'kicker':ParagraphStyle('kicker',fontName='Semi',fontSize=10,leading=14,spaceAfter=9,textColor=colors.HexColor('#555555'),keepWithNext=True),
}
def rich(text):
 text=text.replace('\u2014',':').replace('\u2013','-').replace('\u2011','-')
 # Preserve final prose pair. Code/URLs/SHA may wrap and are QA'd separately.
 text=re.sub(r'(?<=\S) +([^ ]+)\s*$',lambda m:'\u00a0'+m[1],text)
 text=html.escape(text).replace('&lt;br/&gt;','<br/>')
 text=re.sub(r'`([^`]+)`',lambda m:'<font name="Courier" size="8.1">'+m[1]+'</font>',text)
 text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
 text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:'<b>'+m[1]+'</b>',text)
 return text
P=lambda text,kind='body':Paragraph(rich(text),S[kind])
class Numbered(canvas.Canvas):
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.states=[]
 def showPage(self):self.states.append(dict(self.__dict__));self._startPage()
 def save(self):
  total=len(self.states)
  for state in self.states:
   self.__dict__.update(state);w,h=A4;self.setFillColor(colors.HexColor('#4a4a4a'));self.setFont('Body',8)
   self.drawString(52,h-30,'RtR / AERIS / RESEARCH HANDOFF / H10')
   self.setStrokeColor(colors.HexColor('#bdbdbd'));self.setLineWidth(.4);self.line(52,h-39,w-52,h-39)
   self.drawString(52,28,'02.11.2026 | Engineering alpha / beta NOT READY')
   self.drawRightString(w-52,28,f'{self._pageNumber} / {total}');super().showPage()
  super().save()
def markdown(text):
 lines=text.splitlines();flows=[];i=0;para=[]
 def flush():
  if para:flows.append(P(' '.join(para)));para.clear()
 while i<len(lines):
  line=lines[i].strip()
  if line.startswith('```'):
   flush();block=[];i+=1
   while i<len(lines)and not lines[i].strip().startswith('```'):block.append(lines[i]);i+=1
   wrapped=[]
   for item in block:wrapped+=textwrap.wrap(item,width=96,break_long_words=True,break_on_hyphens=False,replace_whitespace=False,drop_whitespace=False)or[' ']
   content='<br/>'.join(html.escape(x).replace(' ','&#160;')for x in wrapped)
   t=Table([[Paragraph(content,S['code'])]],colWidths=[W]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f2f2f2')),('BOX',(0,0),(-1,-1),.4,colors.HexColor('#bdbdbd')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));flows.extend([t,Spacer(1,10)]);i+=1;continue
  if line.startswith('|'):
   flush();rows=[]
   while i<len(lines)and lines[i].strip().startswith('|'):
    row=[x.strip()for x in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r':?-+:?',x or' ')for x in row):rows.append(row)
    i+=1
   n=len(rows[0]);widths=[91,180,220]if n==3 else[140,351]if n==2 else[W/n]*n
   t=Table([[P(x,'table')for x in row]for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
   t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8e8e8')),('LINEBELOW',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#cccccc')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));flows.extend([t,Spacer(1,11)]);continue
  if line.startswith('# '):flush();flows.append(P(line[2:],'h1'))
  elif line.startswith('## '):flush();flows.append(P(line[3:],'h2'))
  elif line.startswith('- ')or re.match(r'^\d+\. ',line):
   flush();item=line;i+=1
   while i<len(lines)and lines[i].strip()and not re.match(r'^(?:#|- |\d+\. |```|\|)',lines[i].strip()):item+=' '+lines[i].strip();i+=1
   flows.append(P(item));continue
  elif not line:flush()
  else:para.append(line)
  i+=1
 flush();return flows
story=[Spacer(1,40),P('ANH GỬI CÁC EM','kicker'),P('UAV PROJECT<br/>AERIS / H10','title'),P('Hồ sơ chuyển giao nghiên cứu','h2'),P('Source hiện tại, cách tiếp nhận, bằng chứng và lộ trình tiếp tục.'),Spacer(1,18)]
box=Table([[P('ENGINEERING ALPHA','h2')],[P('Beta tích hợp NOT READY. G1-G4 chưa được nghiệm thu. Bản này dùng để tiếp nhận và tiếp tục R&D, chưa là release vận hành máy bay thật.')]],colWidths=[W]);box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f1f1f1')),('BOX',(0,0),(-1,-1),.7,colors.black),('LEFTPADDING',(0,0),(-1,-1),15),('RIGHTPADDING',(0,0),(-1,-1),15),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]));story.extend([box,Spacer(1,22),P('Ngày bàn giao: 02/11/2026. Repo public: github.com/nclamvn/uav-project. Tag: research-handoff-2026-11-02-h10.'),P('Bản gốc private của anh: nclamvn/aeris, tag development-handoff-2026-11-02-h10. Các tag 31/10 vẫn giữ nguyên.'),P('Anh gửi các em source và hồ sơ có đối chiếu để bắt đầu nghiên cứu. Giữ rõ điều đã chứng minh, điều là mock/replay và phần runtime hoặc phần cứng còn cần kiểm. Không coi số test, elapsed time, một ACK hoặc UI đẹp là nghiệm thu sản phẩm.'),P('Phạm vi: toàn bộ code theo policy public; BOM, dữ liệu khách hàng, raw, candidate và engineering artifact được giao riêng.','small'),P('Ghi chú trình bày: SHA, URL, tên file và lệnh có thể xuống dòng kỹ thuật. Khi chạy, dùng bản Markdown trong đúng tag. INTAKE01/MILESTONE05 được giữ như lịch sử, không thay hướng dẫn hiện tại của H10.','small'),PageBreak()])
chapters=['HANDOVER.md','STATUS.md','ARCHITECTURE.md','SETUP-AND-VERIFY.md','CONTENTS.md','NEXT-MILESTONE.md','ACCEPTANCE.md','MILESTONE06-H10.md','MESSAGE-TO-TEAM.md']
for i,name in enumerate(chapters):
 story.append(P('PHẦN '+str(i+1).zfill(2),'kicker'));story+=markdown((R/'docs/handoff'/name).read_text())
 if i<len(chapters)-1:story.extend([Spacer(1,13),HRFlowable(width='100%',thickness=.4,color=colors.HexColor('#bdbdbd')),Spacer(1,12),CondPageBreak(170)])
SimpleDocTemplate(str(O),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=58,bottomMargin=50,title='UAV Project / AERIS H10 / Ho so chuyen giao',author='Anh gui cac em / AERIS',subject='H10 research handoff; integrated beta not ready').build(story,canvasmaker=Numbered)
print(O)
