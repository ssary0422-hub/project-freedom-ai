from PIL import Image, ImageDraw, ImageFont

W = H = 1080
out = r"C:\Users\ssary\Downloads\project-freedom-ai\static\marketing\today-speaking-coach-post.png"
mascot_path = r"C:\Users\ssary\Downloads\project-freedom-ai\static\brand\sungeum-speaking-teacher-v1.png"
bold = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 62)
mid = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 34)
body = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 29)
small = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 23)

img = Image.new("RGB", (W, H), (247, 250, 249))
d = ImageDraw.Draw(img)
navy = (14, 43, 60)
mint = (115, 226, 198)
teal = (23, 119, 119)
d.rounded_rectangle((48, 48, 1032, 1032), radius=48, fill="white", outline=(218, 235, 231), width=3)
d.rounded_rectangle((82, 86, 410, 136), radius=24, fill=mint)
d.text((108, 98), "순금이 말정리 코치", font=small, fill=navy)
d.text((82, 205), "말하고 싶은데", font=bold, fill=navy)
d.text((82, 280), "말이 안 나올 때", font=bold, fill=teal)
d.text((86, 395), "사과 · 부탁 · 거절 · 조퇴 · 상사에게 말하기", font=body, fill=(61, 88, 96))
d.rounded_rectangle((82, 485, 680, 745), radius=28, fill=(239, 250, 247))
d.text((120, 530), "상황만 적어주세요.", font=mid, fill=navy)
d.text((120, 590), "순금이가 바로 보낼 수 있는", font=body, fill=(49, 82, 90))
d.text((120, 640), "문장 3개로 정리해드릴게요.", font=body, fill=(49, 82, 90))
d.rounded_rectangle((82, 825, 680, 920), radius=34, fill=navy)
d.text((184, 852), "무료 테스트  ·  DM '말정리'", font=mid, fill="white")
mascot = Image.open(mascot_path).convert("RGBA")
mascot.thumbnail((420, 560), Image.Resampling.LANCZOS)
img_rgba = img.convert("RGBA")
img_rgba.alpha_composite(mascot, (630, 310))
img_rgba.convert("RGB").save(out, quality=96)
print(out)
