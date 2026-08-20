import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "static" / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1080, 1350


def _font(size: int, bold: bool = False):
    candidates = [
        Path(r"C:\Windows\Fonts\malgunbd.ttf" if bold else r"C:\Windows\Fonts\malgun.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _first_publishable_line(text: str) -> str:
    for raw in (text or "").splitlines():
        line = _clean(re.sub(r"^(?:\d+[.)]|[-*•])\s*", "", raw))
        if line and not line.startswith("#"):
            return line
    return ""


def extract_card_copy(result: str, campaign_request: str, company: str):
    first = _first_publishable_line(result)
    parts = [_clean(part) for part in first.split("|") if _clean(part)]
    if len(parts) >= 3:
        headline, benefit, cta = parts[0], parts[1], parts[2]
    else:
        headline = first or _first_publishable_line(campaign_request) or company
        remaining = [
            _clean(line)
            for line in (result or "").splitlines()[1:]
            if _clean(line) and not _clean(line).startswith("#")
        ]
        benefit = remaining[0] if remaining else _clean(campaign_request)
        cta = remaining[1] if len(remaining) > 1 else "자세한 내용은 문의해주세요"
    return (
        headline[:42].rstrip(),
        benefit[:92].rstrip(),
        cta[:48].rstrip(),
    )


def _wrap(draw, text, font, max_width, max_lines):
    lines, current = [], ""
    words = text.split()
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
            if len(lines) == max_lines:
                break
        if draw.textbbox((0, 0), word, font=font)[2] <= max_width:
            current = word
            continue
        chunk = ""
        for char in word:
            candidate = chunk + char
            if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
                chunk = candidate
            else:
                if chunk:
                    lines.append(chunk)
                chunk = char
                if len(lines) == max_lines:
                    break
        current = chunk
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    consumed = " ".join(lines)
    if _clean(consumed) != _clean(text) and lines:
        lines[-1] = lines[-1].rstrip(" .,·") + "…"
    return lines


def _rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def create_finished_promo_card(
    *,
    business: str,
    company: str,
    campaign_request: str,
    result: str,
    output_name: str = "finished-promo-card.png",
    subject_path: str = "",
):
    """Create a publish-ready portrait card using verified user copy.

    The renderer never invents a storefront or product. An optional user-owned
    subject image can be supplied; otherwise it creates a typography-led card.
    """
    business, company = _clean(business), _clean(company)
    headline, benefit, cta = extract_card_copy(result, campaign_request, company)

    image = Image.new("RGB", (WIDTH, HEIGHT), "#07111f")
    pixels = image.load()
    for y in range(HEIGHT):
        mix = y / HEIGHT
        for x in range(WIDTH):
            glow = max(0, 1 - (((x - 880) / 760) ** 2 + ((y - 170) / 620) ** 2))
            pixels[x, y] = (
                int(7 + 12 * mix + 12 * glow),
                int(17 + 18 * mix + 34 * glow),
                int(31 + 25 * mix + 50 * glow),
            )

    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((720, -180, 1260, 360), fill=(62, 225, 196, 40))
    draw.ellipse((-260, 940, 420, 1580), fill=(92, 122, 255, 30))
    for x, y, r in ((835, 205, 9), (940, 330, 6), (760, 440, 5), (150, 1060, 7)):
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(100, 245, 216, 150))

    if subject_path and Path(subject_path).exists():
        subject = Image.open(subject_path).convert("RGBA")
        subject.thumbnail((480, 610), Image.Resampling.LANCZOS)
        shadow = Image.new("RGBA", subject.size, (0, 0, 0, 0))
        shadow.putalpha(subject.getchannel("A").filter(ImageFilter.GaussianBlur(18)))
        sx, sy = WIDTH - subject.width - 42, HEIGHT - subject.height - 150
        image.paste(shadow, (sx + 12, sy + 20), shadow)
        image.paste(subject, (sx, sy), subject)

    _rounded(draw, (58, 58, 390, 116), 29, (255, 255, 255, 22), (255, 255, 255, 55), 2)
    draw.text((88, 73), "순금이 완성형 홍보물", font=_font(24, True), fill=(198, 255, 240, 255))

    business_label = business or "BUSINESS"
    draw.text((64, 166), business_label, font=_font(27, True), fill=(93, 235, 205, 255))

    headline_font = _font(82, True)
    while headline_font.size > 54 and len(_wrap(draw, headline, headline_font, 900, 3)) > 3:
        headline_font = _font(headline_font.size - 4, True)
    title_lines = _wrap(draw, headline, headline_font, 900, 3)
    y = 226
    for line in title_lines:
        draw.text((62, y), line, font=headline_font, fill=(247, 250, 255, 255), stroke_width=1, stroke_fill=(247, 250, 255, 90))
        y += headline_font.size + 18

    draw.rounded_rectangle((62, y + 18, 152, y + 28), radius=5, fill=(93, 235, 205, 255))
    y += 72
    benefit_font = _font(38, False)
    for line in _wrap(draw, benefit, benefit_font, 820 if subject_path else 900, 4):
        draw.text((66, y), line, font=benefit_font, fill=(202, 214, 231, 255))
        y += 58

    card_top = max(y + 42, 785)
    card_width = 610 if subject_path else 950
    _rounded(draw, (58, card_top, 58 + card_width, card_top + 260), 34, (255, 255, 255, 18), (255, 255, 255, 45), 2)
    draw.text((92, card_top + 42), "오늘 고객에게 알려야 할 한 가지", font=_font(25, True), fill=(93, 235, 205, 255))
    request_text = _clean(campaign_request) or benefit
    ry = card_top + 92
    for line in _wrap(draw, request_text, _font(31, True), card_width - 68, 3):
        draw.text((92, ry), line, font=_font(31, True), fill=(246, 248, 252, 255))
        ry += 47

    cta_y = 1162
    _rounded(draw, (58, cta_y, 720, cta_y + 92), 46, (93, 235, 205, 255))
    cta_font = _font(30, True)
    cta_text = cta
    while draw.textbbox((0, 0), cta_text, font=cta_font)[2] > 595 and cta_font.size > 22:
        cta_font = _font(cta_font.size - 2, True)
    draw.text((96, cta_y + 26), cta_text, font=cta_font, fill=(5, 31, 39, 255))
    draw.text((60, 1282), company or "업체명", font=_font(28, True), fill=(247, 250, 255, 255))
    draw.text((WIDTH - 332, 1288), "FACT-BASED · READY TO POST", font=_font(17, True), fill=(133, 153, 181, 255))

    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "-", output_name) or "finished-promo-card.png"
    output_path = OUTPUT_DIR / safe_name
    image.save(output_path, "PNG", optimize=True)
    return output_path.relative_to(BASE_DIR).as_posix()
