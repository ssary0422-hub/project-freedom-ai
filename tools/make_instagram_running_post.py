from PIL import Image, ImageDraw, ImageFont

W = H = 1080
out = r"C:\Users\ssary\Downloads\project-freedom-ai\static\marketing\instagram-running-post-20260824.png"
mascot_path = r"C:\Users\ssary\Downloads\project-freedom-ai\static\brand\sungeum-running-coach-paw-v2.png"
font_bold = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 58)
font_mid = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 33)
font_body = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 28)
font_small = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 24)

img = Image.new("RGB", (W, H))
pix = img.load()
for y in range(H):
    for x in range(W):
        t = (x + y) / (W + H)
        pix[x, y] = (8, int(24 + 48 * t), int(43 + 58 * t))
draw = ImageDraw.Draw(img)

# soft accent circles
draw.ellipse((690, -150, 1220, 380), fill=(20, 103, 117))
draw.ellipse((-180, 820, 330, 1330), fill=(13, 55, 82))

draw.rounded_rectangle((70, 70, 390, 125), radius=28, fill=(116, 232, 203))
draw.text((98, 83), "S U N G E U M  R U N", font=font_small, fill=(7, 38, 53))
draw.text((70, 190), "달릴 때", font=font_bold, fill="white")
draw.text((70, 260), "상체가 너무", font=font_bold, fill="white")
draw.text((70, 330), "흔들리나요?", font=font_bold, fill=(116, 232, 203))
draw.text((74, 435), "순금이가 러닝 자세를", font=font_mid, fill=(230, 244, 247))
draw.text((74, 480), "쉽게 체크해줄게요", font=font_mid, fill=(230, 244, 247))

draw.rounded_rectangle((70, 595, 560, 835), radius=30, fill=(255, 255, 255))
draw.text((105, 635), "오늘 한 가지만 체크!", font=font_mid, fill=(10, 50, 68))
for i, line in enumerate(("• 어깨 힘 빼기", "• 시선은 앞쪽 보기", "• 팔은 자연스럽게")):
    draw.text((112, 695 + i * 45), line, font=font_body, fill=(36, 91, 103))

draw.rounded_rectangle((70, 900, 570, 985), radius=38, fill=(116, 232, 203))
draw.text((118, 923), "내 러닝 자세도 봐줘", font=font_mid, fill=(7, 38, 53))

mascot = Image.open(mascot_path).convert("RGBA")
mascot.thumbnail((520, 710), Image.Resampling.LANCZOS)
img_rgba = img.convert("RGBA")
img_rgba.alpha_composite(mascot, (555, 330))
img_rgba.convert("RGB").save(out, quality=95)
print(out)
