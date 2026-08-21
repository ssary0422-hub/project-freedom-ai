"""Render structurally distinct campaign concepts with exact brand copy."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

from services.campaign_art_direction import ArtDirection
from services.finished_promo_card import _cover, _draw_text, _font, _rounded, _wrap


WIDTH, HEIGHT = 1080, 1350


def create_safe_typographic_background(*, direction: ArtDirection,
                                       output_path: str | Path,
                                       size: tuple[int, int] = (WIDTH, HEIGHT)) -> Path:
    """Create a deterministic photo-free background without a model call."""
    width, height = size
    base = ImageColor.getrgb(direction.palette[0]) + (255,)
    accent = ImageColor.getrgb(direction.palette[1]) + (255,)
    secondary = ImageColor.getrgb(direction.palette[2]) + (255,)
    image = Image.new("RGBA", size, base)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon(((int(width * .55), 0), (width, 0), (width, int(height * .7)),
                  (int(width * .72), int(height * .53))), fill=accent)
    draw.ellipse((int(width * .7), int(height * .08), int(width * 1.08),
                  int(height * .38)), outline=secondary, width=max(8, width // 70))
    for offset in range(-height, width, max(48, width // 14)):
        draw.line((offset, height, offset + height, 0), fill=secondary[:3] + (36,),
                  width=max(2, width // 360))
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(target, "PNG", optimize=True)
    return target


def _compact_copy(text: str, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[:limit + 1].rsplit(" ", 1)[0]
    return (shortened if len(shortened) >= limit // 2 else cleaned[:limit]).rstrip(" ,.!?")


def _contrast_text(fill: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    red, green, blue = fill[:3]
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
    return (8, 22, 28, 255) if luminance > 0.58 else (255, 255, 255, 255)


def _background(path: str | Path) -> Image.Image:
    with Image.open(path) as source:
        return _cover(source.convert("RGBA"), (WIDTH, HEIGHT))


def _text_block(draw, *, direction: ArtDirection, x: int, y: int, width: int,
                title_size: int, title_lines: int = 3, light: bool = True) -> int:
    ink = (248, 251, 255, 255) if light else (16, 27, 35, 255)
    body = (245, 249, 252, 255) if light else (45, 59, 68, 255)
    accent = ImageColor.getrgb(direction.palette[1]) + (255,)
    font = _font(title_size, True, "ko")
    for line in _wrap(draw, direction.headline, font, width, title_lines, "ko", True):
        _draw_text(draw, (x, y), line, font, ink, "ko", True)
        y += title_size + 18
    draw.rounded_rectangle((x, y + 8, x + 104, y + 19), radius=6, fill=accent)
    y += 62
    body_font = _font(31, False, "ko")
    supporting_copy = _compact_copy(direction.supporting_copy, 34 if width < 400 else 58)
    for line in _wrap(draw, supporting_copy, body_font, width, 3, "ko"):
        _draw_text(draw, (x, y), line, body_font, body, "ko")
        y += 48
    return y


def _footer(draw, *, company: str, direction: ArtDirection, light: bool = True):
    ink = (248, 251, 255, 255) if light else (16, 27, 35, 255)
    _draw_text(draw, (58, 1280), company, _font(25, True, "ko"), ink, "ko", True)


def _proof_chips(draw, items: tuple[str, ...], *, x: int, y: int,
                 max_width: int, light: bool = True) -> int:
    """Draw exact, compact proof labels without relying on image-model text."""
    if not items:
        return y
    ink = (244, 250, 255, 255) if light else (18, 31, 41, 255)
    fill = (7, 19, 32, 190) if light else (235, 242, 247, 235)
    outline = (114, 232, 214, 190)
    font = _font(22, True, "ko")
    cursor_x = x
    for item in items[:4]:
        label = _compact_copy(item, 10)
        bounds = draw.textbbox((0, 0), label, font=font)
        chip_width = min(max_width, bounds[2] - bounds[0] + 38)
        if cursor_x + chip_width > x + max_width:
            break
        _rounded(draw, (cursor_x, y, cursor_x + chip_width, y + 54), 27, fill, outline, 2)
        _draw_text(draw, (cursor_x + 19, y + 13), label, font, ink, "ko", True)
        cursor_x += chip_width + 12
    return y + 54


def _proof_previews(draw, items: tuple[str, ...], *, x: int, y: int,
                    max_width: int) -> int:
    """Show visibly different output formats as deterministic mini mockups."""
    if not items:
        return y
    gap = 12
    card_width = (max_width - gap * 3) // 4
    colors = ((89, 225, 203, 255), (255, 112, 67, 255),
              (255, 214, 92, 255), (129, 140, 248, 255))
    font = _font(19, True, "ko")
    for index, item in enumerate(items[:4]):
        left = x + index * (card_width + gap)
        top = y + (10 if index % 2 else 0)
        _rounded(draw, (left, top, left + card_width, top + 118), 10, (247, 250, 252, 245))
        accent = colors[index]
        if index == 0:
            draw.rectangle((left + 9, top + 9, left + card_width - 9, top + 64), fill=accent)
        elif index == 1:
            draw.rectangle((left + 9, top + 9, left + 43, top + 81), fill=accent)
            draw.rectangle((left + 50, top + 9, left + card_width - 9, top + 81), fill=(23, 39, 55, 255))
        elif index == 2:
            draw.rectangle((left + 9, top + 9, left + card_width - 9, top + 47), fill=(23, 39, 55, 255))
            draw.rectangle((left + 9, top + 53, left + card_width - 9, top + 81), fill=accent)
        else:
            draw.rectangle((left + 22, top + 9, left + card_width - 22, top + 81), fill=accent)
        _draw_text(draw, (left + 10, top + 90), item, font, (16, 28, 37, 255), "ko", True)
    return y + 128


def render_campaign_concept(*, background_path: str | Path, direction: ArtDirection,
                            company: str, output_path: str | Path,
                            proof_items: tuple[str, ...] = (),
                            logo_path: str | Path | None = None,
                            footer_detail: str = "") -> Path:
    """Render one of the core layouts without asking the image model to draw text."""
    image = _background(background_path)
    accent = ImageColor.getrgb(direction.palette[1]) + (255,)

    if direction.layout_family == "split_scene":
        photo = image.crop((430, 0, WIDTH, HEIGHT))
        panel = Image.new("RGBA", (WIDTH, HEIGHT), ImageColor.getrgb(direction.palette[0]) + (255,))
        panel.paste(photo, (430, 0))
        image = panel
        draw = ImageDraw.Draw(image, "RGBA")
        _draw_text(draw, (58, 62), company, _font(25, True, "ko"), accent, "ko", True)
        _text_block(draw, direction=direction, x=58, y=245, width=326, title_size=58, title_lines=4, light=False)
        _proof_chips(draw, proof_items, x=58, y=976, max_width=326, light=False)
        _rounded(draw, (58, 1082, 382, 1176), 16, accent)
        _draw_text(draw, (86, 1110), direction.cta, _font(27, True, "ko"), _contrast_text(accent), "ko", True)
        _footer(draw, company=company, direction=direction, light=False)

    elif direction.layout_family == "editorial_type":
        photo = image.crop((360, 360, 1030, 1160)).rotate(-3, expand=True, resample=Image.Resampling.BICUBIC)
        image = Image.new("RGBA", (WIDTH, HEIGHT), (247, 242, 232, 255))
        draw = ImageDraw.Draw(image, "RGBA")
        draw.rectangle((0, 0, 24, HEIGHT), fill=accent)
        _draw_text(draw, (62, 58), company, _font(27, True, "ko"), (12, 30, 47, 255), "ko", True)
        _text_block(draw, direction=direction, x=62, y=190, width=900, title_size=76, title_lines=2, light=False)
        image.alpha_composite(photo, (390, 600))
        draw = ImageDraw.Draw(image, "RGBA")
        _rounded(draw, (58, 1120, 520, 1210), 8, accent)
        _draw_text(draw, (90, 1146), direction.cta, _font(29, True, "ko"), _contrast_text(accent), "ko", True)
        _footer(draw, company=direction.concept_name, direction=direction, light=False)

    elif direction.layout_family == "photo_collage":
        source = image.copy()
        image = Image.new("RGBA", (WIDTH, HEIGHT), ImageColor.getrgb(direction.palette[0]) + (255,))
        draw = ImageDraw.Draw(image, "RGBA")
        crops = (
            (_cover(source.crop((0, 0, 700, 850)), (430, 520)), (58, 520), -4),
            (_cover(source.crop((360, 180, 1080, 1050)), (430, 520)), (570, 460), 4),
            (_cover(source.crop((120, 520, 950, 1350)), (390, 300)), (340, 930), -1),
        )
        for panel, position, angle in crops:
            framed = Image.new("RGBA", (panel.width + 18, panel.height + 18), (250, 248, 241, 255))
            framed.alpha_composite(panel, (9, 9))
            framed = framed.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
            image.alpha_composite(framed, position)
        draw = ImageDraw.Draw(image, "RGBA")
        _draw_text(draw, (58, 55), company, _font(25, True, "ko"), accent, "ko", True)
        _text_block(draw, direction=direction, x=58, y=145, width=900, title_size=65, title_lines=2)
        _rounded(draw, (650, 1160, 1020, 1240), 40, accent)
        _draw_text(draw, (684, 1183), direction.cta, _font(26, True, "ko"), _contrast_text(accent), "ko", True)
        _footer(draw, company=direction.concept_name, direction=direction)

    elif direction.layout_family == "problem_solution":
        left = source = image.crop((0, 0, 540, HEIGHT)).convert("L").convert("RGBA")
        right = image.crop((540, 0, WIDTH, HEIGHT))
        image = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
        image.alpha_composite(left, (0, 0))
        image.alpha_composite(right, (540, 0))
        shade = Image.new("RGBA", (WIDTH, HEIGHT), (4, 12, 22, 105))
        image = Image.alpha_composite(image, shade)
        draw = ImageDraw.Draw(image, "RGBA")
        draw.line((540, 0, 540, HEIGHT), fill=accent, width=8)
        _rounded(draw, (58, 70, 420, 130), 30, (5, 18, 31, 215))
        _draw_text(draw, (85, 87), company, _font(24, True, "ko"), accent, "ko", True)
        _rounded(draw, (50, 760, 1030, 1110), 16, (4, 13, 24, 224))
        _text_block(draw, direction=direction, x=86, y=805, width=900, title_size=68, title_lines=2)
        _rounded(draw, (645, 1150, 1022, 1235), 42, accent)
        _draw_text(draw, (678, 1175), direction.cta, _font(27, True, "ko"), _contrast_text(accent), "ko", True)
        _footer(draw, company=direction.concept_name, direction=direction)

    elif direction.layout_family == "bold_offer":
        shade = Image.new("RGBA", (WIDTH, HEIGHT), (4, 9, 15, 125))
        image = Image.alpha_composite(image, shade)
        draw = ImageDraw.Draw(image, "RGBA")
        _rounded(draw, (52, 52, 360, 112), 12, (5, 13, 22, 205), accent, 2)
        _draw_text(draw, (78, 68), company, _font(24, True, "ko"), accent, "ko", True)
        _rounded(draw, (50, 470, 1030, 870), 8, (5, 12, 18, 222))
        _text_block(draw, direction=direction, x=88, y=520, width=900, title_size=82, title_lines=3)
        _proof_chips(draw, proof_items, x=88, y=930, max_width=900)
        _rounded(draw, (616, 1130, 1022, 1224), 47, accent)
        _draw_text(draw, (656, 1158), direction.cta, _font(29, True, "ko"), _contrast_text(accent), "ko", True)
        _footer(draw, company=company, direction=direction)

    else:
        shade = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        shade_draw = ImageDraw.Draw(shade, "RGBA")
        for x in range(WIDTH):
            alpha = int(225 * max(0, 1 - x / 820))
            shade_draw.line((x, 0, x, HEIGHT), fill=(3, 12, 24, alpha))
        image = Image.alpha_composite(image, shade)
        draw = ImageDraw.Draw(image, "RGBA")
        _rounded(draw, (58, 58, 390, 120), 31, (3, 18, 37, 190), accent, 2)
        _draw_text(draw, (88, 75), company, _font(25, True, "ko"), accent, "ko", True)
        _text_block(draw, direction=direction, x=62, y=210, width=610, title_size=72)
        _proof_previews(draw, proof_items, x=62, y=930, max_width=610)
        _rounded(draw, (58, 1110, 660, 1204), 47, accent)
        _draw_text(draw, (94, 1138), direction.cta, _font(30, True, "ko"), _contrast_text(accent), "ko", True)
        _footer(draw, company=company, direction=direction)

    draw = ImageDraw.Draw(image, "RGBA")
    if footer_detail:
        detail = _compact_copy(footer_detail, 42)
        font = _font(20, True, "ko")
        bounds = draw.textbbox((0, 0), detail, font=font)
        text_width = bounds[2] - bounds[0]
        left = WIDTH - 70 - text_width
        _rounded(draw, (left - 12, 1271, WIDTH - 48, 1323), 12, (5, 15, 27, 205))
        _draw_text(draw, (left, 1283), detail, font,
                   (245, 249, 252, 255), "ko", True)
    if logo_path and Path(logo_path).exists():
        with Image.open(logo_path) as source:
            logo = source.convert("RGBA")
            logo.thumbnail((150, 72), Image.Resampling.LANCZOS)
        plate = Image.new("RGBA", (logo.width + 20, logo.height + 14), (255, 255, 255, 225))
        plate.alpha_composite(logo, (10, 7))
        image.alpha_composite(plate, (WIDTH - plate.width - 48, 1190))

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(target, "PNG", optimize=True)
    return target


def render_blog_cover(*, background_path: str | Path, direction: ArtDirection,
                      company: str, output_path: str | Path) -> Path:
    """Render a readable 1200x630 blog hero without AI-generated lettering."""
    with Image.open(background_path) as source:
        image = _cover(source.convert("RGBA"), (1200, 630))
    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(shade, "RGBA")
    for x in range(1200):
        shade_draw.line((x, 0, x, 630), fill=(4, 12, 23, int(225 * max(0, 1 - x / 860))))
    image = Image.alpha_composite(image, shade)
    draw = ImageDraw.Draw(image, "RGBA")
    accent = ImageColor.getrgb(direction.palette[1]) + (255,)
    _draw_text(draw, (58, 48), company, _font(23, True, "ko"), accent, "ko", True)
    font = _font(55, True, "ko")
    y = 150
    for line in _wrap(draw, direction.headline, font, 650, 3, "ko", True):
        _draw_text(draw, (58, y), line, font, (250, 252, 255, 255), "ko", True)
        y += 72
    draw.rounded_rectangle((58, y + 12, 158, y + 22), radius=5, fill=accent)
    y += 58
    body = _compact_copy(direction.supporting_copy, 54)
    for line in _wrap(draw, body, _font(25, False, "ko"), 650, 2, "ko"):
        _draw_text(draw, (58, y), line, _font(25, False, "ko"), (218, 228, 239, 255), "ko")
        y += 38
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(target, "PNG", optimize=True)
    return target
