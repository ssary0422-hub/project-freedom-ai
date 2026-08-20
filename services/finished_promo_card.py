import re
import textwrap
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFilter, ImageFont


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "static" / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1080, 1350
FONT_DIR = BASE_DIR / "assets" / "fonts"

CARD_LABELS = {
    "ko": {
        "badge": "순금이 완성형 홍보물",
        "fact": "오늘 고객에게 알려야 할 한 가지",
        "footer": "사실 기반 · 바로 게시 가능",
    },
    "en": {
        "badge": "Sungeum Ready-to-Post",
        "fact": "One thing customers should know today",
        "footer": "FACT-BASED · READY TO POST",
    },
    "ja": {
        "badge": "スングム 完成型プロモーション",
        "fact": "今日お客様に伝えたいこと",
        "footer": "事実に基づく · 投稿準備完了",
    },
    "th": {
        "badge": "สื่อโปรโมตพร้อมโพสต์โดยซุนกึม",
        "fact": "สิ่งสำคัญที่ลูกค้าควรรู้วันนี้",
        "footer": "ข้อมูลจริง - พร้อมโพสต์",
    },
    "zh": {
        "badge": "顺金成品宣传图",
        "fact": "今天最想告诉顾客的一件事",
        "footer": "基于事实 · 可直接发布",
    },
    "es": {
        "badge": "Promoción lista por Sungeum",
        "fact": "Lo que tus clientes deben saber hoy",
        "footer": "BASADO EN HECHOS · LISTO PARA PUBLICAR",
    },
}


def _font(size: int, bold: bool = False, language: str = "ko"):
    bundled = {
        "ko": FONT_DIR / "NotoSansKR-VF.otf",
        "en": FONT_DIR / "NotoSansKR-VF.otf",
        "ja": FONT_DIR / "NotoSansJP-VF.otf",
        "th": FONT_DIR / ("NotoSansThai-Bold.ttf" if bold else "NotoSansThai-Regular.ttf"),
        "zh": FONT_DIR / "NotoSansSC-VF.otf",
        "es": FONT_DIR / "NotoSansKR-VF.otf",
    }
    candidates = [
        bundled.get(language, bundled["ko"]),
        Path(r"C:\Windows\Fonts\malgunbd.ttf" if bold else r"C:\Windows\Fonts\malgun.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            font = ImageFont.truetype(str(candidate), size=size)
            if bold and candidate.name.endswith("-VF.otf"):
                try:
                    font.set_variation_by_name("Bold")
                except (OSError, ValueError):
                    pass
            return font
    return ImageFont.load_default()


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _thai_font_runs(text, primary_font, bold=False):
    """Split Thai and non-Thai text so Latin brand names use a Latin font."""
    latin_font = _font(primary_font.size, bold, "en")
    runs = []
    for char in text:
        font = primary_font if "\u0e00" <= char <= "\u0e7f" else latin_font
        if char.isspace() and runs:
            font = runs[-1][1]
        if runs and runs[-1][1] is font:
            runs[-1] = (runs[-1][0] + char, font)
        else:
            runs.append((char, font))
    return runs


def _text_width(draw, text, font, language="ko", bold=False):
    if language != "th":
        return draw.textlength(text, font=font)
    return sum(draw.textlength(run, font=run_font) for run, run_font in _thai_font_runs(text, font, bold))


def _draw_text(draw, position, text, font, fill, language="ko", bold=False, **kwargs):
    if language != "th":
        draw.text(position, text, font=font, fill=fill, **kwargs)
        return
    x, y = position
    for run, run_font in _thai_font_runs(text, font, bold):
        draw.text((x, y), run, font=run_font, fill=fill, **kwargs)
        x += draw.textlength(run, font=run_font)


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


def _wrap(draw, text, font, max_width, max_lines, language="ko", bold=False):
    lines, current = [], ""
    words = text.split()
    for word in words:
        candidate = f"{current} {word}".strip()
        if _text_width(draw, candidate, font, language, bold) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
            if len(lines) == max_lines:
                break
        if _text_width(draw, word, font, language, bold) <= max_width:
            current = word
            continue
        chunk = ""
        for char in word:
            candidate = chunk + char
            if _text_width(draw, candidate, font, language, bold) <= max_width:
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
    without_spacing = lambda value: re.sub(r"\s+", "", value)
    if without_spacing(consumed) != without_spacing(text) and lines:
        lines[-1] = lines[-1].rstrip(" .,·") + "..."
    return lines


def _rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _cover(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Crop an uploaded photo to a predictable area without stretching it."""
    target_width, target_height = size
    scale = max(target_width / source.width, target_height / source.height)
    resized = source.resize(
        (max(target_width, round(source.width * scale)), max(target_height, round(source.height * scale))),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - target_width) // 2
    top = (resized.height - target_height) // 2
    return resized.crop((left, top, left + target_width, top + target_height))


def card_quality_score(*, headline: str, benefit: str, cta: str, subject_path: str = "") -> int:
    """Return the renderer's release score; anything below 90 is not publish-ready."""
    score = 100
    if not all((_clean(headline), _clean(benefit), _clean(cta))):
        score -= 20
    if len(_clean(headline)) > 42:
        score -= 5
    if len(_clean(benefit)) > 92:
        score -= 5
    if len(_clean(cta)) > 48:
        score -= 5
    combined = " ".join((headline, benefit, cta))
    if "\ufffd" in combined or re.search(r"\?{2,}", combined):
        score -= 30
    if subject_path and not Path(subject_path).exists():
        score -= 15
    return max(0, score)


def create_finished_promo_card(
    *,
    business: str,
    company: str,
    campaign_request: str,
    result: str,
    output_name: str = "finished-promo-card.png",
    subject_path: str = "",
    logo_path: str = "",
    website_url: str = "",
    map_url: str = "",
    language: str = "ko",
):
    """Create a publish-ready portrait card using verified user copy.

    The renderer never invents a storefront or product. An optional user-owned
    subject image can be supplied; otherwise it creates a typography-led card.
    """
    business, company = _clean(business), _clean(company)
    language = language if language in CARD_LABELS else "ko"
    labels = CARD_LABELS[language]
    headline, benefit, cta = extract_card_copy(result, campaign_request, company)
    quality_score = card_quality_score(
        headline=headline,
        benefit=benefit,
        cta=cta,
        subject_path=subject_path,
    )
    if quality_score < 90:
        raise ValueError(f"Promotional card failed the 90-point release gate: {quality_score}")

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

    has_subject = bool(subject_path and Path(subject_path).exists())
    photo_box = (574, 708, 1022, 1092)
    if has_subject:
        subject = _cover(Image.open(subject_path).convert("RGBA"), (448, 384))
        mask = Image.new("L", subject.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 447, 383), radius=30, fill=255)
        shadow = Image.new("RGBA", (472, 408), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((12, 12, 459, 395), radius=30, fill=(0, 0, 0, 165))
        shadow = shadow.filter(ImageFilter.GaussianBlur(14))
        image.paste(shadow, (photo_box[0] - 12, photo_box[1] - 8), shadow)
        image.paste(subject, (photo_box[0], photo_box[1]), mask)

    if logo_path and Path(logo_path).exists():
        logo = Image.open(logo_path).convert("RGBA")
        alpha_box = logo.getchannel("A").getbbox()
        if alpha_box:
            logo = logo.crop(alpha_box)
        logo.thumbnail((158, 158), Image.Resampling.LANCZOS)
        lx, ly = WIDTH - logo.width - 72, 62
        if logo.getchannel("A").getextrema()[0] == 255:
            _rounded(draw, (lx - 18, ly - 12, lx + logo.width + 18, ly + logo.height + 12), 20, (255, 255, 255, 235))
        else:
            logo_shadow = Image.new("RGBA", logo.size, (0, 0, 0, 0))
            logo_shadow.putalpha(logo.getchannel("A").filter(ImageFilter.GaussianBlur(10)))
            image.paste(logo_shadow, (lx + 5, ly + 8), logo_shadow)
        image.paste(logo, (lx, ly), logo)

    badge_font = _font(24, True, language)
    badge_width = min(930, max(332, _text_width(draw, labels["badge"], badge_font, language, True) + 60))
    _rounded(draw, (58, 58, 58 + badge_width, 116), 29, (255, 255, 255, 22), (255, 255, 255, 55), 2)
    _draw_text(draw, (88, 73), labels["badge"], badge_font, (198, 255, 240, 255), language, True)

    business_label = business or "BUSINESS"
    _draw_text(draw, (64, 166), business_label, _font(27, True, language), (93, 235, 205, 255), language, True)

    headline_font = _font(76, True, language)
    title_lines = _wrap(draw, headline, headline_font, 900, 2, language, True)
    y = 226
    for line in title_lines:
        _draw_text(draw, (62, y), line, headline_font, (247, 250, 255, 255), language, True, stroke_width=1, stroke_fill=(247, 250, 255, 90))
        y += headline_font.size + 18

    draw.rounded_rectangle((62, y + 18, 152, y + 28), radius=5, fill=(93, 235, 205, 255))
    y += 72
    benefit_font = _font(38, False, language)
    benefit_lines = _wrap(draw, benefit, benefit_font, 900, 2, language)
    while y + len(benefit_lines) * 58 > 654 and benefit_font.size > 28:
        benefit_font = _font(benefit_font.size - 2, False, language)
        benefit_lines = _wrap(draw, benefit, benefit_font, 900, 2, language)
    for line in benefit_lines:
        _draw_text(draw, (66, y), line, benefit_font, (202, 214, 231, 255), language)
        y += 58

    card_top = max(y + 34, 708)
    card_width = 480 if has_subject else 964
    card_height = 384 if has_subject else 300
    _rounded(draw, (58, card_top, 58 + card_width, card_top + card_height), 34, (255, 255, 255, 18), (255, 255, 255, 45), 2)
    _draw_text(draw, (92, card_top + 42), labels["fact"], _font(25, True, language), (93, 235, 205, 255), language, True)
    request_text = _clean(campaign_request) or benefit
    ry = card_top + 92
    for line in _wrap(draw, request_text, _font(31, True, language), card_width - 68, 3, language, True):
        _draw_text(draw, (92, ry), line, _font(31, True, language), (246, 248, 252, 255), language, True)
        ry += 47

    cta_y = 1148
    _rounded(draw, (58, cta_y, 1022, cta_y + 92), 46, (93, 235, 205, 255))
    cta_font = _font(30, True, language)
    cta_text = cta
    while _text_width(draw, cta_text, cta_font, language, True) > 890 and cta_font.size > 22:
        cta_font = _font(cta_font.size - 2, True, language)
    _draw_text(draw, (96, cta_y + 26), cta_text, cta_font, (5, 31, 39, 255), language, True)
    _draw_text(draw, (60, 1282), company or "업체명", _font(28, True, language), (247, 250, 255, 255), language, True)
    footer_font = _font(17, True, language)
    footer_width = _text_width(draw, labels["footer"], footer_font, language, True)
    _draw_text(draw, (WIDTH - footer_width - 58, 1288), labels["footer"], footer_font, (133, 153, 181, 255), language, True)

    link_labels = []
    if website_url:
        parsed = urlparse(website_url if "://" in website_url else f"https://{website_url}")
        link_labels.append((parsed.netloc or website_url).replace("www.", ""))
    if map_url:
        link_labels.append({"ko": "지도에서 위치 확인", "en": "View on map", "ja": "地図で確認", "th": "ดูตำแหน่งบนแผนที่", "zh": "在地图上查看", "es": "Ver en el mapa"}[language])
    if link_labels:
        link_text = "  ·  ".join(link_labels)
        link_font = _font(22, True, language)
        while _text_width(draw, link_text, link_font, language, True) > 950 and link_font.size > 18:
            link_font = _font(link_font.size - 1, True, language)
        _draw_text(draw, (60, 1107), link_text, link_font, (93, 235, 205, 255), language, True)

    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "-", output_name) or "finished-promo-card.png"
    output_path = OUTPUT_DIR / safe_name
    image.save(output_path, "PNG", optimize=True)
    return output_path.relative_to(BASE_DIR).as_posix()
