from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "marketing"
OUT.mkdir(parents=True, exist_ok=True)
MASCOT = ROOT / "static" / "brand" / "sungeum-speaking-teacher-v1.png"
W, H = 1080, 1920
NAVY = (9, 24, 43)
MINT = (190, 245, 229)
TEAL = (32, 166, 157)
INK = (20, 39, 60)
MUTED = (110, 133, 151)

def font(path, size):
    return ImageFont.truetype(path, size)

KR = r"C:\Windows\Fonts\malgun.ttf"
KRB = r"C:\Windows\Fonts\malgunbd.ttf"
TH = r"C:\Windows\Fonts\LeelawUI.ttf"
THB = r"C:\Windows\Fonts\LeelawUI.ttf"

DATA = [
    ("한국어", "순금이 선생님의", "한마디 수업", "상사에게 조퇴를 어떻게 말하지?", "이렇게 말하면", "순금이가 정리하면", "말하기 어려운 순간,", "문장으로 바로 정리해드려요.", "다음 상황을 댓글로 적어주세요.", "오늘 조퇴해도 될까요?", "오늘 개인적인 사정으로 조퇴를 해야\n할 것 같습니다.\n업무는 미리 정리하고 필요한 내용은\n인수인계해두겠습니다.", "무료 테스트 · DM '말정리'", "tiktok-speaking-ko.png", KR, KRB),
    ("ENGLISH", "SUNGEUM TEACHER", "ONE-LINE LESSON", "How do I ask my manager\nif I can leave early?", "A QUICK WAY TO SAY IT", "SUNGEUM'S POLISHED VERSION", "When the words feel hard,", "I’ll turn them into a sentence.", "Comment the next situation.", "Can I leave early today?", "I have a personal matter to take care of today,\nso I’d like to leave early.\nI’ll organize my work and hand over\nanything necessary before I go.", "FREE TEST · DM 'SAY IT'", "tiktok-speaking-en.png", r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
    ("ภาษาไทย", "ครูซุนกึม", "บทเรียนหนึ่งประโยค", "จะขอหัวหน้ากลับก่อน\nเวลาอย่างไรดี?", "พูดแบบนี้", "ประโยคที่ครูซุนกึมเรียบเรียง", "เวลาพูดยาก", "ครูซุนกึมช่วยเรียบเรียงให้", "คอมเมนต์สถานการณ์ถัดไปได้เลย", "วันนี้ขอกลับก่อนได้ไหมคะ/ครับ", "วันนี้ฉันมีธุระส่วนตัว จึงอยากขออนุญาต\nเลิกงานก่อนเวลา\nฉันจะจัดการงานให้เรียบร้อยและส่งต่องาน\nที่จำเป็นก่อนกลับค่ะ/ครับ", "ทดสอบฟรี · DM '말정리'", "tiktok-speaking-th.png", r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\tahomabd.ttf"),
]

def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

for lang, subline, title, hook, rough_label, polished_label, tag1, tag2, footer, rough, polished, cta, filename, regular_path, bold_path in DATA:
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    # soft color fields
    d.ellipse((-220, -260, 600, 560), fill=(17, 59, 78))
    d.ellipse((640, 1270, 1230, 2020), fill=(14, 49, 65))
    f_lang = font(bold_path, 34)
    f_title = font(bold_path, 72 if lang == "한국어" else 58)
    f_sub = font(regular_path, 35)
    f_small = font(regular_path, 30)
    f_body = font(regular_path, 34 if lang != "한국어" else 38)
    f_body_b = font(bold_path, 38 if lang != "한국어" else 40)
    # Header
    rounded(d, (64, 70, 265, 126), 28, MINT)
    d.text((92, 82), lang, font=f_lang, fill=INK)
    d.text((64, 176), subline, font=f_sub, fill=(152, 211, 205))
    d.text((64, 225), title, font=f_title, fill=(245, 252, 250))
    d.text((64, 325), hook, font=f_body_b, fill=(245, 252, 250), spacing=10)
    # conversation cards
    d.text((76, 610), rough_label, font=f_small, fill=(140, 168, 181))
    rounded(d, (64, 660, 1016, 820), 30, (35, 52, 71))
    d.text((102, 710), f'“{rough}”', font=f_body, fill=(197, 211, 218), spacing=8)
    d.text((76, 900), polished_label, font=f_small, fill=MINT)
    rounded(d, (64, 950, 1016, 1245), 30, (235, 252, 247))
    d.text((102, 1000), f'“{polished}”', font=f_body_b, fill=INK, spacing=12)
    # mascot cutout
    mascot = Image.open(MASCOT).convert("RGBA")
    mascot.thumbnail((400, 580), Image.Resampling.LANCZOS)
    x = 610; y = 1290
    im.paste(mascot, (x, y), mascot)
    d = ImageDraw.Draw(im)
    d.text((64, 1390), tag1, font=f_sub, fill=(172, 213, 210))
    d.text((64, 1445), tag2, font=f_body_b, fill=(245, 252, 250))
    rounded(d, (64, 1660, 650, 1740), 35, TEAL)
    d.text((101, 1680), cta, font=f_small, fill=(255, 255, 255))
    d.text((64, 1810), footer, font=f_small, fill=(150, 179, 190))
    im.save(OUT / filename, optimize=True)
    print(OUT / filename)
