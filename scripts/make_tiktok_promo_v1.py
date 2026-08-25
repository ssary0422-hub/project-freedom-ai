from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "marketing" / "tiktok-project-freedom-promo-v2.mp4"
PREVIEW = ROOT / "static" / "marketing" / "tiktok-project-freedom-promo-v2-preview.png"
W, H, FPS, DURATION = 1080, 1920, 30, 15
FONT = Path("C:/Windows/Fonts/malgun.ttf")
FONT_B = Path("C:/Windows/Fonts/malgunbd.ttf")

def font(size, bold=False):
    return ImageFont.truetype(str(FONT_B if bold else FONT), size)

def fit(img, box):
    img = img.convert("RGBA")
    img.thumbnail(box, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", box, (0, 0, 0, 0))
    canvas.alpha_composite(img, ((box[0]-img.width)//2, (box[1]-img.height)//2))
    return canvas

def rounded(base, xy, radius, fill, outline=None, width=1):
    ImageDraw.Draw(base).rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def clean_result_card(img):
    """Normalize embedded demo URLs so every visible CTA uses the live domain."""
    img = img.copy().convert("RGBA")
    d = ImageDraw.Draw(img)
    h = img.height
    # The source card contains an outdated host near its footer. Replace the
    # whole footer band so no obsolete URL can leak into the TikTok export.
    d.rectangle((0, h-250, img.width, h), fill=(8, 20, 38, 255))
    d.rounded_rectangle((70, h-190, img.width-70, h-105), 24, fill=(102, 239, 214, 255))
    text_center(d, (img.width//2, h-148), "무료로 직접 만들어봐", font(28, True), (7, 28, 49, 255))
    text_center(d, (img.width//2, h-52), "projectfreedom-ai.com", font(19, True), (102, 239, 214, 255))
    return img

def make_sns_mock():
    """Create a clean social-result mock without retired blog/poster copy."""
    card = Image.new("RGBA", (1080, 1350), (10, 22, 42, 255))
    d = ImageDraw.Draw(card)
    d.text((72, 74), "순금이 실제 결과", font=font(30, True), fill=(102, 239, 214, 255))
    d.text((72, 170), "사업 정보만 넣었는데", font=font(58, True), fill=(255, 255, 255, 255))
    d.text((72, 245), "홍보물이 이렇게 나왔어", font=font(58, True), fill=(102, 239, 214, 255))
    rounded(card, (72, 395, 1008, 840), 28, (21, 42, 69, 255), (71, 112, 163, 255), 2)
    d.text((110, 445), "오늘의 홍보 문구", font=font(26, True), fill=(255, 221, 130, 255))
    d.text((110, 525), "고객이 바로 이해하는", font=font(36, True), fill=(255, 255, 255, 255))
    d.text((110, 580), "친근한 SNS 게시물을 준비했어요.", font=font(32), fill=(220, 233, 247, 255))
    d.rounded_rectangle((110, 700, 970, 790), 20, fill=(228, 204, 133, 255))
    text_center(d, (540, 745), "무료로 직접 만들어봐", font(32, True), (9, 26, 47, 255))
    d.text((72, 1000), "업종·상호·홍보 내용만 입력하면 돼", font=font(30), fill=(151, 190, 214, 255))
    d.text((72, 1080), "projectfreedom-ai.com", font=font(28, True), fill=(102, 239, 214, 255))
    return card

def text_center(draw, xy, text, f, fill):
    b = draw.textbbox((0, 0), text, font=f)
    draw.text((xy[0]-(b[2]-b[0])/2, xy[1]-(b[3]-b[1])/2), text, font=f, fill=fill)

def frame(t):
    bg = Image.new("RGBA", (W, H), (7, 16, 34, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((170, 120, 950, 960), fill=(20, 92, 150, 90))
    gd.ellipse((400, 920, 1300, 1900), fill=(27, 183, 157, 55))
    bg = Image.alpha_composite(bg, glow.filter(ImageFilter.GaussianBlur(110)))
    d = ImageDraw.Draw(bg)
    d.text((70, 70), "PROJECT FREEDOM AI", font=font(30, True), fill=(102, 239, 214, 255))
    d.text((70, 116), "순금이의 마케팅 작업실", font=font(22), fill=(180, 197, 221, 255))

    mascot = Image.open(ROOT / "static" / "brand" / "sungeum-3d-official.png")
    ad = clean_result_card(Image.open(ROOT / "static" / "marketing" / "instagram-ai-content-lineup.png"))
    sns = make_sns_mock()

    if t < 3.8:
        p = min(1, t / 0.6)
        text_center(d, (W//2, 360), "사업 정보 한 줄이면", font(76, True), (255, 255, 255, 255))
        text_center(d, (W//2, 455), "홍보물이 완성돼요", font(76, True), (102, 239, 214, 255))
        rounded(bg, (80, 650, 1000, 925), 28, (16, 28, 52, 245), (69, 109, 151, 255), 3)
        d.text((125, 700), "업종·가게명·홍보할 내용", font=font(28, True), fill=(145, 170, 198, 255))
        typed = "태국 파타야 마사지샵의 편안한 분위기를 알려줘"
        shown = typed[:max(1, min(len(typed), int((t-1.2)*18)))] if t > 1.2 else ""
        d.text((125, 790), shown, font=font(32), fill=(255, 255, 255, 255))
        d.rounded_rectangle((125, 990, 955, 1085), 24, fill=(62, 125, 255, 255))
        text_center(d, (540, 1038), "순금이에게 만들어달라고 하기", font(28, True), (255, 255, 255, 255))
    elif t < 8.8:
        text_center(d, (W//2, 330), "입력은 한 번", font(66, True), (255, 255, 255, 255))
        text_center(d, (W//2, 420), "결과는 바로 확인", font(66, True), (102, 239, 214, 255))
        rounded(bg, (75, 620, 1005, 1325), 32, (16, 28, 52, 245), (69, 109, 151, 255), 3)
        d.text((130, 700), "순금이가 정리했어요", font=font(28, True), fill=(102, 239, 214, 255))
        for i, s in enumerate(["광고 문구", "SNS 게시물", "브랜드에 맞는 이미지"]):
            y = 805 + i*125
            d.ellipse((135, y, 185, y+50), fill=(102, 239, 214, 255))
            text_center(d, (160, y+25), "✓", font(28, True), (7, 31, 50, 255))
            d.text((220, y+3), s, font=font(34, True), fill=(255, 255, 255, 255))
        m = fit(mascot, (270, 300)); bg.alpha_composite(m, (690, 1440))
    elif t < 12.8:
        text_center(d, (W//2, 330), "광고도", font(62, True), (255, 255, 255, 255))
        text_center(d, (W//2, 410), "SNS도 한 번에", font(62, True), (102, 239, 214, 255))
        phase = min(1, max(0, (t - 8.8) / 0.65))
        ease = 1 - (1 - phase) ** 3
        for target_x, im, label, direction in [(55, ad, "광고", -1), (565, sns, "SNS", 1)]:
            x = int(target_x + direction * (1 - ease) * 360)
            rounded(bg, (x, 560, x+460, 1365), 28, (18, 28, 50, 255), (82, 122, 170, 255), 3)
            d.text((x+28, 600), label, font=font(32, True), fill=(255, 255, 255, 255))
            card = fit(im, (400, 680)); bg.alpha_composite(card, (x+30, 660))
        d.text((90, 1480), "실제 결과물을 직접 확인하고", font=font(34, True), fill=(255, 255, 255, 255))
        d.text((90, 1540), "마음에 들면 바로 저장하세요", font=font(34, True), fill=(102, 239, 214, 255))
    else:
        m = fit(mascot, (430, 480)); bg.alpha_composite(m, (325, 230))
        text_center(d, (W//2, 900), "사업 정보만 입력해보세요", font(58, True), (255, 255, 255, 255))
        text_center(d, (W//2, 985), "광고 · SNS 콘텐츠 완성", font(52, True), (102, 239, 214, 255))
        rounded(bg, (90, 1190, 990, 1405), 40, (102, 239, 214, 255), None)
        text_center(d, (W//2, 1298), "projectfreedom-ai.com", font(43, True), (7, 28, 49, 255))
        text_center(d, (W//2, 1510), "순금이와 무료로 시작하기", font(38, True), (255, 255, 255, 255))
    return bg.convert("RGB")

def main():
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([exe, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)], stdin=subprocess.PIPE)
    last = None
    for i in range(FPS * DURATION):
        last = frame(i / FPS)
        proc.stdin.write(last.tobytes())
    proc.stdin.close(); proc.wait()
    last.save(PREVIEW)
    print(OUT)
    print(PREVIEW)

if __name__ == "__main__":
    main()
