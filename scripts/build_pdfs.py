"""Produce a concise executive brief and a PDF copy of the rendered pitch."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
FONT=Path('/System/Library/Fonts/Supplemental')
for name,file in [('RelaySans','Arial.ttf'),('RelayBold','Arial Bold.ttf'),('RelaySerif','Georgia.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
GREEN=HexColor('#173e32'); INK=HexColor('#24382e'); MUTED=HexColor('#66736a'); CREAM=HexColor('#f5f3e9'); LIME=HexColor('#d9ed9c')
W,H=595.276,841.89
c=canvas.Canvas(str(OUT/'Pantry-Relay-Brief.pdf'),pagesize=(W,H))
c.setTitle('Pantry Relay - Executive Brief');c.setAuthor('Shivam Gupta')
c.setFillColor(CREAM);c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColor(GREEN);c.rect(0,H-226,W,226,fill=1,stroke=0)
def line(t,x,y,size=12,color=INK,font='RelaySans'):
 c.setFillColor(color);c.setFont(font,size);c.drawString(x,y,t)
def paragraph(t,x,y,w,size=11,color=INK,leading=16,bold=False):
 p=Paragraph(t,ParagraphStyle('p',fontName='RelayBold' if bold else 'RelaySans',fontSize=size,leading=leading,textColor=color));_,height=p.wrap(w,1000);p.drawOn(c,x,y-height);return y-height
line('PANTRY RELAY',42,H-44,12,LIME,'RelayBold')
line('Make the food already',40,H-99,31,CREAM,'RelaySerif')
line('here go further.',40,H-137,31,CREAM,'RelaySerif')
line('Shivam Gupta  /  Hack Away Hunger 2026',42,H-190,11,CREAM)
y=H-253
line('THE JOB',42,y,10,GREEN,'RelayBold');y-=17
y=paragraph('Help an approved pantry network fill upcoming food-category gaps with nearby surplus, protect each location\'s own reserve, and record what the receiving pantry actually accepts.',42,y,511,12,leading=17)-21
line('WHY IOWA',42,y,10,GREEN,'RelayBold');y-=17
y=paragraph('Food Bank of Iowa\'s FY2025 report describes 700 partners and programs across 55 counties. That scale makes coordination relevant. The frequency of transferable surplus and willingness to pay remain questions for a real pilot.',42,y,511,11,leading=16)-20
line('A WORKING HANDOFF',42,y,10,GREEN,'RelayBold');y-=17
y=paragraph('A coordinator records food and service needs, reviews explained proposals, reserves stock, records receiver acceptance, and follows pickup through receipt. The app checks restrictions, reserves, expiry, storage, space and carrying capacity. It records partial rejection and delivery failure without inventing accepted pounds.',42,y,511,11,leading=16)-20
line('120 LB DISPATCHED. 112 LB ACCEPTED.',42,y,13,GREEN,'RelayBold');y-=20
y=paragraph('In the fictional demo, 8 lb arrive damaged. The report counts 112 lb, preserves the exception and reopens the missing need. These are sample records, not real-world impact. Pounds do not establish meals served or people reached.',42,y,511,11,leading=16)-20
line('A BUSINESS HYPOTHESIS',42,y,10,GREEN,'RelayBold');y-=17
y=paragraph('Proposed price: $149 per network per month for up to 10 sites. Free self-hosting remains available. At an illustrative $25/hour staff cost, the price requires roughly 6 hours saved monthly. No customers, revenue or validated savings are claimed.',42,y,511,11,leading=16)-20
line('THE NEXT TEST',42,y,10,GREEN,'RelayBold');y-=17
y=paragraph('One coordinator, three nearby pantries and six weeks. Establish a baseline, run supervised transfers, then compare service gaps, staff time, transport effort and actual accepted weight. A named operator owns transfer permissions and food safety.',42,y,511,11,leading=16)
if y<85: raise ValueError(f'Brief body overflow: {y}')
line('SOURCE / Food Bank of Iowa FY2025 Impact Report',42,63,8,MUTED)
c.linkURL('https://foodbankiowa.org/app/uploads/2025/08/FY_2025_impact_report_v8.pdf',(42,59,430,73),relative=0)
line('github.com/shi1720/Hack-Away-Hunger',42,45,9,GREEN,'RelayBold');c.linkURL('https://github.com/shi1720/Hack-Away-Hunger',(42,40,460,55),relative=0)
line('Supervised-pilot release. AI-assisted development disclosed in the repository.',42,28,8,MUTED)
c.showPage();c.save()
slides=sorted((ROOT/'tmp/slides/rendered').glob('slide-*.png'))
if slides:
 c=canvas.Canvas(str(OUT/'Pantry-Relay-Pitch.pdf'),pagesize=(960,540));c.setTitle('Pantry Relay - Pitch');c.setAuthor('Shivam Gupta')
 for image in slides:
  c.drawImage(ImageReader(str(image)),0,0,width=960,height=540)
  c.showPage()
 c.save()
print('PDF artifacts built')
