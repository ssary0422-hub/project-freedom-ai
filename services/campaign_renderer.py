"""Render structurally distinct campaign concepts with exact brand copy."""

from __future__ import annotations

import colorsys
from dataclasses import replace
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageStat

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


def _draw_fitted_cta(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
                      text: str, max_size: int, fill: tuple[int, int, int, int]) -> None:
    """Center a CTA and shrink it until it stays inside its button."""
    left, top, right, bottom = box
    font = _font(max_size, True, "ko")
    while draw.textlength(text or "", font=font) > (right - left - 44) and font.size > 16:
        font = _font(font.size - 2, True, "ko")
    width = draw.textlength(text or "", font=font)
    bbox = draw.textbbox((0, 0), text or "", font=font)
    height = bbox[3] - bbox[1]
    x = left + ((right - left) - width) / 2
    y = top + ((bottom - top) - height) / 2 - bbox[1]
    _draw_text(draw, (x, y), text or "", font, fill, "ko", True)


def _background(path: str | Path) -> Image.Image:
    with Image.open(path) as source:
        return _safe_cover(source.convert("RGBA"), (WIDTH, HEIGHT), focal_y=.42)


def _safe_cover(source: Image.Image, size: tuple[int, int], *, focal_y: float = .42) -> Image.Image:
    """Cover a panel while keeping the visually important upper-middle area in frame."""
    source = source.convert("RGBA")
    target_w, target_h = size
    scale = max(target_w / source.width, target_h / source.height)
    resized = source.resize((round(source.width * scale), round(source.height * scale)),
                            Image.Resampling.LANCZOS)
    left = max(0, (resized.width - target_w) // 2)
    available_y = max(0, resized.height - target_h)
    top = round(available_y * max(0.0, min(1.0, focal_y)))
    return resized.crop((left, top, left + target_w, top + target_h))


def _normalized_logo(logo_path: str | Path) -> Image.Image:
    """Remove oversized uniform margins while preserving the exact visible mark."""
    with Image.open(logo_path) as source:
        logo = source.convert("RGBA")
    logo.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    pixels = logo.load()
    corners = (pixels[0, 0], pixels[logo.width - 1, 0], pixels[0, logo.height - 1],
               pixels[logo.width - 1, logo.height - 1])
    background = tuple(round(sum(color[channel] for color in corners) / 4) for channel in range(3))
    mask = Image.new("L", logo.size, 0)
    mask_pixels = mask.load()
    for y in range(logo.height):
        for x in range(logo.width):
            red, green, blue, alpha = pixels[x, y]
            distance = max(abs(red - background[0]), abs(green - background[1]), abs(blue - background[2]))
            if alpha > 20 and distance > 18:
                mask_pixels[x, y] = min(alpha, max(0, round((distance - 18) * 255 / 18)))
    content_box = mask.getbbox()
    if content_box and content_box != (0, 0, logo.width, logo.height):
        logo.putalpha(mask)
        left, top, right, bottom = content_box
        pad = max(4, round(max(right - left, bottom - top) * .04))
        logo = logo.crop((max(0, left - pad), max(0, top - pad),
                          min(logo.width, right + pad), min(logo.height, bottom + pad)))
    return logo


def _average_color(image: Image.Image, *, ignore_transparent: bool = False) -> tuple[int, int, int]:
    sample = image.convert("RGBA")
    sample.thumbnail((96, 96), Image.Resampling.LANCZOS)
    colors = []
    for red, green, blue, alpha in sample.getdata():
        if ignore_transparent and alpha < 80:
            continue
        spread = max(red, green, blue) - min(red, green, blue)
        colors.extend([(red, green, blue)] * (1 + spread // 24))
    if not colors:
        return (216, 185, 120)
    return tuple(round(sum(color[channel] for color in colors) / len(colors)) for channel in range(3))


def _brand_aware_direction(direction: ArtDirection, background_path: str | Path,
                           logo_path: str | Path | None) -> ArtDirection:
    """Harmonize model art direction with the real uploaded brand and scene."""
    with Image.open(background_path) as source:
        scene_rgb = _average_color(source)
    brand_rgb = ImageColor.getrgb(direction.palette[1])
    if logo_path and Path(logo_path).exists():
        brand_rgb = _average_color(_normalized_logo(logo_path), ignore_transparent=True)
    scene_h, scene_l, scene_s = colorsys.rgb_to_hls(*(value / 255 for value in scene_rgb))
    brand_h, brand_l, brand_s = colorsys.rgb_to_hls(*(value / 255 for value in brand_rgb))
    if brand_s < .16:
        brand_h, brand_s = scene_h, .46
    accent = colorsys.hls_to_rgb(brand_h, min(.82, max(.68, brand_l)), min(.68, max(.38, brand_s)))
    base = colorsys.hls_to_rgb(scene_h, .10, min(.44, max(.22, scene_s)))
    ivory = colorsys.hls_to_rgb(brand_h, .94, .28)
    to_hex = lambda color: "#" + "".join(f"{round(value * 255):02x}" for value in color)
    return replace(direction, palette=(to_hex(base), to_hex(accent), to_hex(ivory)))


def _place_brand_logo(image: Image.Image, logo_path: str | Path | None, *,
                      max_size: tuple[int, int], margin: int,
                      candidates: tuple[tuple[int, int], ...]) -> bool:
    """Place the exact uploaded logo on the calmest available brand-safe area."""
    if not logo_path or not Path(logo_path).exists():
        return False
    logo = _normalized_logo(logo_path)
    alpha_box = logo.getchannel("A").getbbox()
    if not alpha_box:
        return False
    logo = logo.crop(alpha_box)
    logo.thumbnail(max_size, Image.Resampling.LANCZOS)

    pad_x, pad_y = max(14, logo.width // 12), max(10, logo.height // 8)
    plate_size = (logo.width + pad_x * 2, logo.height + pad_y * 2)
    width, height = image.size
    valid = []
    for x, y in candidates:
        x = min(max(margin, x if x >= 0 else width - plate_size[0] + x), width - plate_size[0] - margin)
        y = min(max(margin, y if y >= 0 else height - plate_size[1] + y), height - plate_size[1] - margin)
        crop = image.crop((x, y, x + plate_size[0], y + plate_size[1])).convert("L")
        stat = ImageStat.Stat(crop)
        # Low variation and low edge energy indicate genuine negative space. Edge energy
        # keeps a logo off faces, hands, furniture and other high-detail subjects that
        # can look deceptively calm when averaged into a dark crop.
        edge = crop.filter(ImageFilter.FIND_EDGES)
        edge_mean = ImageStat.Stat(edge).mean[0]
        score = stat.var[0] + edge_mean * 6 + (x < width / 2) * 3
        valid.append((score, x, y))
    if not valid:
        return False
    _, x, y = min(valid)

    shadow = Image.new("RGBA", (plate_size[0] + 18, plate_size[1] + 18), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (9, 9, plate_size[0] + 9, plate_size[1] + 9), radius=18, fill=(0, 0, 0, 58)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    image.alpha_composite(shadow, (x - 9, y - 5))
    # Do not add a white card around the uploaded mark. The source logo's own
    # colors and transparent silhouette are the brand asset; a forced plate
    # makes every business look like it has a sticker border.
    plate = Image.new("RGBA", plate_size, (0, 0, 0, 0))
    plate.alpha_composite(logo, (pad_x, pad_y))
    image.alpha_composite(plate, (x, y))
    return True


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
    """Render the planned copy/photo relationship without a shared badge/button shell."""
    from services.campaign_layout import render_composition
    return render_composition(background_path=background_path, direction=direction,
                              company=company, output_path=output_path, proof_items=proof_items,
                              logo_path=logo_path, footer_detail=footer_detail)


def render_blog_cover(*, background_path: str | Path, direction: ArtDirection,
                      company: str, output_path: str | Path,
                      logo_path: str | Path | None = None) -> Path:
    """Render a readable 1200x630 blog hero without AI-generated lettering."""
    direction = _brand_aware_direction(direction, background_path, logo_path)
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
    _place_brand_logo(
        image, logo_path, max_size=(280, 130), margin=34,
        candidates=((34, -260), (-34, -260), (34, 34), (-34, 34), (-34, -124)),
    )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(target, "PNG", optimize=True)
    return target
