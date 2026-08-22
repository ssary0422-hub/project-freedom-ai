from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static/showcase/sungeum-marketing-workspace-carousel"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1350
BG = (7, 17, 31)
TEAL = (97, 230, 211)
WHITE = (248, 251, 255)
MUTED = (171, 188, 211)
FONT = r"C:\Windows\Fonts\malgun.ttf"
FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"
REG = lambda n: ImageFont.truetype(FONT, n)
BOLD = lambda n: ImageFont.truetype(FONT_BOLD, n)
MASCOT = ROOT / "static/brand/sungeum-3d-official.png"
PROOF = [ROOT / "static/showcase/approved-ads-9-0.png", ROOT / "static/showcase/approved-sns-9-2.png", ROOT / "static/showcase/approved-blog-9-0.png"]


def base(slide):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.ellipse((690, -180, 1260, 390), fill=(15, 74, 91))
    d.ellipse((-240, 1030, 420, 1570), fill=(21, 43, 83))
    d.text((70, 58), "순금이의 마케팅 작업실", font=BOLD(34), fill=TEAL)
    d.text((W - 170, 70), f"{slide}/5", font=BOLD(25), fill=MUTED)
    mascot = Image.open(MASCOT).convert("RGBA")
    mascot.thumbnail((190, 230))
    im.paste(mascot, (W - mascot.width - 65, 105), mascot)
    return im, d


def fit_card(im, path, box):
    if not path.exists():
        return
    x, y, w, h = box
    card = ImageOps.fit(Image.open(path).convert("RGB"), (w, h), method=Image.Resampling.LANCZOS)
    im.paste(card, (x, y))


def save(im, n):
    im.save(OUT / f"slide-{n:02d}.png", optimize=True)


def main():
    im, d = base(1)
    d.text((70, 310), "아이디어는 있는데\n콘텐츠가 막막할 때", font=BOLD(74), fill=WHITE, spacing=12)
    d.text((74, 550), "순금이가 광고 · SNS · 블로그 · 포스터를\n우리 브랜드답게 함께 만들어줄게.", font=REG(34), fill=MUTED, spacing=10)
    d.rounded_rectangle((70, 760, 1010, 910), 28, fill=(25, 43, 65), outline=TEAL, width=2)
    d.text((105, 805), "순금이의 마케팅 작업실", font=BOLD(46), fill=TEAL)
    d.text((70, 1195), "Project Freedom AI", font=BOLD(30), fill=WHITE)
    save(im, 1)

    for n, (headline, body, path) in enumerate([
        ("사업 정보와 브랜드\n자료를 넣으면", "매번 처음부터 다시 설명하지 않아도 돼.", PROOF[0]),
        ("광고 · SNS · 블로그 · 포스터를\n한 번에", "목적에 맞는 결과물을 빠르게 비교하고 고를 수 있어.", PROOF[1]),
        ("내 로고와 실제 사진까지\n반영해서", "우리 가게와 브랜드에 어울리는 콘텐츠로 완성해.", PROOF[2]),
    ], 2):
        im, d = base(n)
        d.text((70, 300), headline, font=BOLD(58), fill=WHITE, spacing=10)
        d.text((72, 465), body, font=REG(31), fill=MUTED)
        fit_card(im, path, (70, 610, 940, 540))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((70, 1190, 1010, 1270), 30, fill=TEAL)
        d.text((105, 1210), "순금이와 같이 만들어보기 →", font=BOLD(29), fill=BG)
        save(im, n)

    im, d = base(5)
    d.text((70, 320), "오늘도 순금이가\n같이 만들어줄게", font=BOLD(76), fill=WHITE, spacing=12)
    d.text((74, 565), "순금이의 마케팅 작업실", font=BOLD(42), fill=TEAL)
    d.text((74, 650), "Project Freedom AI", font=REG(34), fill=MUTED)
    d.rounded_rectangle((70, 830, 1010, 960), 30, fill=TEAL)
    d.text((110, 872), "지금 무료로 시작하기", font=BOLD(44), fill=BG)
    d.text((74, 1120), "광고 · SNS · 블로그 · 포스터", font=BOLD(30), fill=WHITE)
    save(im, 5)


if __name__ == "__main__":
    main()
