from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "marketing"; OUT.mkdir(parents=True, exist_ok=True)
MASCOT = ROOT / "static" / "brand" / "sungeum-running-coach-mascot-clean.png"
W,H=1080,1920
KR=r"C:\Windows\Fonts\malgun.ttf"; KRB=r"C:\Windows\Fonts\malgunbd.ttf"
EN=r"C:\Windows\Fonts\arial.ttf"; ENB=r"C:\Windows\Fonts\arialbd.ttf"
TH=r"C:\Windows\Fonts\tahoma.ttf"; THB=r"C:\Windows\Fonts\tahomabd.ttf"

def ft(p,s): return ImageFont.truetype(p,s)
def box(d,b,r,fill,outline=None,w=1): d.rounded_rectangle(b,radius=r,fill=fill,outline=outline,width=w)
def mascot(im, xy, size):
    m=Image.open(MASCOT).convert('RGBA'); m.thumbnail(size,Image.Resampling.LANCZOS); im.paste(m,xy,m)

def ko():
    bg=(255,244,224); ink=(30,47,58); coral=(240,108,83); mint=(206,241,220)
    im=Image.new('RGB',(W,H),bg); d=ImageDraw.Draw(im)
    d.ellipse((-220,-280,620,560),fill=(255,218,157)); d.polygon([(0,790),(1080,530),(1080,1100),(0,1370)],fill=(255,231,190))
    d.text((72,72),'RUNNING FORM',font=ft(KRB,30),fill=coral)
    d.text((72,145),'영상 하나 올리면,',font=ft(KRB,70),fill=ink)
    d.text((72,235),'러닝 자세를 봐드려요.',font=ft(KRB,70),fill=ink)
    box(d,(72,420,610,520),30,coral); d.text((110,444),'순금이 러닝코치 · 1분 분석',font=ft(KR,30),fill='white')
    steps=[('01','영상 업로드','옆모습 러닝 영상을 올려요.'),('02','착지·팔·상체','자세 포인트를 찾아드려요.'),('03','다음 미션','바로 실천할 한 가지를 받아요.')]
    y=650
    for n,t,s in steps:
        d.ellipse((72,y,152,y+80),fill=ink); d.text((94,y+20),n,font=ft(KRB,25),fill='white')
        d.text((180,y+3),t,font=ft(KRB,42),fill=ink); d.text((180,y+55),s,font=ft(KR,28),fill=(89,110,116)); y+=150
    mascot(im,(650,1000),(360,520)); d=ImageDraw.Draw(im)
    d.text((72,1355),'오늘의 미션',font=ft(KRB,32),fill=coral)
    d.text((72,1410),'러닝 영상 하나 찍어두기.',font=ft(KRB,42),fill=ink)
    box(d,(72,1640,680,1725),38,(36,164,139)); d.text((112,1664),'무료 러닝코치 · 프로필 링크',font=ft(KR,30),fill='white')
    d.text((72,1800),'다음 러닝 고민을 댓글로 남겨줘요.',font=ft(KR,28),fill=(97,118,122)); im.save(OUT/'tiktok-running-ko.png',optimize=True)

def en():
    bg=(8,29,48); white=(245,250,248); teal=(80,211,183); orange=(255,160,95)
    im=Image.new('RGB',(W,H),bg); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,430),fill=(14,57,70)); d.ellipse((650,80,1250,680),fill=(22,87,92))
    d.text((70,72),'RUNNING COACH / 01',font=ft(ENB,31),fill=teal)
    d.text((70,160),'One video.',font=ft(ENB,76),fill=white); d.text((70,250),'Better running form.',font=ft(ENB,62),fill=white)
    d.text((70,520),'UPLOAD YOUR RUNNING VIDEO',font=ft(ENB,28),fill=(154,190,192))
    box(d,(70,580,1010,1040),34,(242,248,245));
    lines=['01  Upload a side-view video','02  Get form feedback','03  Receive one next mission']
    y=650
    for line in lines:
        d.text((120,y),line,font=ft(ENB,43),fill=(15,53,67)); y+=120
    d.line((120,1000,950,1000),fill=orange,width=5)
    mascot(im,(620,1090),(370,520)); d=ImageDraw.Draw(im)
    d.text((70,1260),'TODAY\'S EASY MISSION',font=ft(ENB,29),fill=orange)
    d.text((70,1320),'Film one side-view run\nand send it to Sungeum.',font=ft(ENB,48),fill=white,spacing=10)
    box(d,(70,1650,680,1735),40,teal); d.text((108,1674),'FREE RUN COACH · PROFILE LINK',font=ft(ENB,26),fill=bg)
    d.text((70,1810),'Comment your next running question.',font=ft(EN,28),fill=(154,190,192)); im.save(OUT/'tiktok-running-en.png',optimize=True)

def th():
    bg=(245,237,255); ink=(48,35,74); purple=(117,83,190); peach=(255,174,133); mint=(198,239,218)
    im=Image.new('RGB',(W,H),bg); d=ImageDraw.Draw(im)
    d.ellipse((560,-180,1240,500),fill=(224,207,255)); d.ellipse((-180,1180,480,1860),fill=(255,218,188))
    d.text((70,74),'RUNNING COACH',font=ft(THB,31),fill=purple)
    d.text((70,150),'ส่งวิดีโอเดียว',font=ft(THB,72),fill=ink); d.text((70,250),'ให้ครูซุนกึมดูฟอร์ม',font=ft(THB,62),fill=ink)
    box(d,(70,410,710,505),42,purple); d.text((112,438),'วิเคราะห์ท่าวิ่งแบบง่าย ๆ',font=ft(TH,30),fill='white')
    items=[('01','ส่งวิดีโอด้านข้าง','ถ่ายตอนวิ่งสั้น ๆ'),('02','ดูจุดสำคัญ','ลงเท้า แขน และลำตัว'),('03','รับภารกิจถัดไป','แก้ทีละจุดให้ดีขึ้น')]
    y=650
    for n,t,s in items:
        d.text((90,y),n,font=ft(THB,30),fill=purple); d.text((190,y),t,font=ft(THB,43),fill=ink); d.text((190,y+57),s,font=ft(TH,27),fill=(105,89,130)); y+=150
    mascot(im,(650,1120),(360,510)); d=ImageDraw.Draw(im)
    d.text((70,1370),'ภารกิจวันนี้',font=ft(THB,32),fill=purple)
    d.text((70,1430),'ถ่ายวิดีโอวิ่งด้านข้างไว้ 1 คลิป',font=ft(THB,40),fill=ink)
    box(d,(70,1650,700,1735),40,peach); d.text((110,1675),'โค้ชฟรี · ลิงก์ในโปรไฟล์',font=ft(THB,29),fill=ink)
    d.text((70,1810),'คอมเมนต์คำถามเรื่องการวิ่งได้เลย',font=ft(TH,28),fill=(105,89,130)); im.save(OUT/'tiktok-running-th.png',optimize=True)

ko(); en(); th()
