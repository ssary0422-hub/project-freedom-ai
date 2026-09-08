"""Content-led campaign composition; geometry is shared with regression checks."""
from pathlib import Path
from dataclasses import replace
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageStat, ImageOps
from services.finished_promo_card import _font, _draw_text

SIZE = (1080, 1350)


def _side(value):
    value = str(value).lower().replace('-', '_').replace(' ', '_')
    horizontal = 'right' if 'right' in value or '오른' in value else 'left'
    vertical = 'bottom' if 'bottom' in value or '하단' in value else 'top'
    return horizontal, vertical


def _quietness(image, box):
    patch = image.crop(box).convert('L').resize((96, 96))
    return ImageStat.Stat(patch).stddev[0] + ImageStat.Stat(patch.filter(ImageFilter.FIND_EDGES)).mean[0] * 2


def plan_composition(direction, image):
    """Return disjoint photo/copy regions, or an explicitly checked photo overlay.

    Quiet-area detection is a pixel heuristic, not face or object recognition.
    Busy photos use a separate copy panel rather than an opaque block over the subject.
    """
    family = direction.layout_family
    side, vertical = _side(direction.headline_position)
    subject_side, _ = _side(direction.subject_position)
    if direction.headline_position in ('auto', ''):
        side = 'left' if subject_side == 'right' else 'right'
    align = 'right' if side == 'right' else 'left'
    plan = dict(family=family, align=align, overlay=False, title_size=82)
    if family == 'full_bleed_photo':
        candidates = [((64, 198, 650, 662), 'left', 'top'), ((430, 198, 1016, 662), 'right', 'top'),
                      ((64, 658, 650, 1122), 'left', 'bottom'), ((430, 658, 1016, 1122), 'right', 'bottom')]
        ranked = [( _quietness(image, box) + (0 if horizontal == side else 14)
                    + (0 if v == vertical else 8) + (24 if horizontal == subject_side else 0), box, horizontal)
                  for box, horizontal, v in candidates]
        score, box, horizontal = min(ranked)
        if score < 75:
            plan.update(photo=(0, 0, 1080, 1350), copy=box, overlay=True, align=horizontal, title_size=78)
        else:
            plan.update(photo=(0, 480, 1080, 1188), copy=(72, 195, 1008, 448), title_size=76)
    elif family == 'product_closeup':
        plan.update(photo=(40, 485, 1040, 1190), copy=(72, 195, 1008, 449), title_size=88)
        if vertical == 'bottom':
            plan.update(photo=(40, 185, 1040, 855), copy=(72, 900, 1008, 1180))
    elif family == 'split_scene':
        plan.update(photo=(466, 185, 1080, 1190), copy=(64, 230, 424, 1110), title_size=70)
        if side == 'right':
            plan.update(photo=(0, 185, 614, 1190), copy=(658, 230, 1016, 1110))
    elif family == 'editorial_type':
        plan.update(photo=(170, 660, 1008, 1180), copy=(72, 198, 1008, 620), title_size=112)
    elif family == 'bold_offer':
        plan.update(photo=(560, 714, 1008, 1178), copy=(72, 210, 1008, 665), title_size=122, color_field=True)
    elif family == 'photo_collage':
        plan.update(photo=(72, 538, 728, 1184), detail=(752, 754, 1008, 1010),
                    copy=(72, 190, 1008, 494), title_size=84)
    elif family == 'testimonial':
        # Never synthesize quotes, ratings or testimonials from ordinary brand copy.
        plan.update(photo=(720, 198, 1008, 598), copy=(72, 650, 1008, 1160), title_size=92)
    elif family == 'problem_solution':
        plan.update(photo=(72, 198, 540, 916), copy=(586, 350, 1008, 1160), title_size=76)
    elif family == 'location_first':
        plan.update(photo=(0, 185, 1080, 888), copy=(72, 924, 1008, 1186), title_size=72)
    elif family == 'step_by_step':
        plan.update(photo=(760, 198, 1008, 1175), copy=(72, 270, 706, 1115), title_size=88)
    else:
        raise ValueError(f'Unsupported campaign layout: {family}')
    return plan


def _ink(color):
    def linear(value):
        value /= 255
        return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
    luminance = sum(weight * linear(value) for weight, value in zip((.2126, .7152, .0722), color[:3]))
    return '#ffffff' if luminance < .179 else '#17191b'


def _lines(draw, text, font, width):
    result = []
    for paragraph in str(text or '').split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if draw.textlength(candidate, font=font) <= width:
                line = candidate
                continue
            if line:
                result.append(line)
                line = ''
            # Keep Korean words intact; split only a single overlong token.
            for char in word:
                if line and draw.textlength(line + char, font=font) > width:
                    result.append(line)
                    line = ''
                line += char
        if line.strip():
            result.append(line.strip())
    return result


def fit_copy(draw, direction, box, title_size):
    width, height = box[2] - box[0], box[3] - box[1]
    for size in range(title_size, 27, -2):
        body_size = max(24, min(32, size // 2))
        title_font, body_font = _font(size, True, 'ko'), _font(body_size, False, 'ko')
        try:
            body_font.set_variation_by_name('Regular')
        except (AttributeError, OSError, ValueError):
            pass
        title = _lines(draw, direction.headline, title_font, width)
        body = _lines(draw, direction.supporting_copy, body_font, width)
        needed = len(title) * (size + 16) + (28 if body else 0) + len(body) * (body_size + 14)
        if needed <= height:
            return title, body, title_font, body_font
    raise ValueError('Campaign copy does not fit; shorten the brief instead of clipping text')


def _draw_lines(draw, lines, font, box, y, fill, align, bold=False):
    for line in lines:
        width = draw.textlength(line, font=font)
        x = box[2] - width if align == 'right' else (box[0]+box[2]-width)/2 if align == 'center' else box[0]
        top = draw.textbbox((0, 0), line, font=font)[1]
        _draw_text(draw, (x, y - top), line, font, fill, 'ko', bold)
        y += font.size + (16 if bold else 14)
    return y


def render_composition(*, background_path, direction, company, output_path,
                       logo_path=None, footer_detail='', proof_items=()):
    if proof_items:
        direction = replace(direction, supporting_copy='\n'.join(filter(None,(direction.supporting_copy,*proof_items))))
    with Image.open(background_path) as source:
        source = source.convert('RGB')
        full = ImageOps.fit(source, SIZE, method=Image.Resampling.LANCZOS)
    plan = plan_composition(direction, full)
    base = ImageColor.getrgb(direction.palette[0])
    paper = ImageColor.getrgb(direction.palette[2])
    accent = ImageColor.getrgb(direction.palette[1])
    surface = base if plan.get('color_field') else paper
    image = full.copy() if plan['overlay'] else Image.new('RGB', SIZE, surface)
    if not plan['overlay']:
        x1, y1, x2, y2 = plan['photo']
        subject_side, subject_vertical = _side(direction.subject_position)
        focal_x = .82 if subject_side == 'right' else .18
        focal_y = .85 if subject_vertical == 'bottom' else .42
        photo = ImageOps.fit(source, (x2-x1, y2-y1), method=Image.Resampling.LANCZOS,
                             centering=(focal_x,focal_y))
        image.paste(photo, (x1,y1))
        if plan.get('detail'):
            box = plan['detail']
            crop = source.crop((source.width//4, source.height//4, source.width*3//4, source.height*3//4))
            image.paste(ImageOps.fit(crop, (box[2]-box[0],box[3]-box[1])), box[:2])
    box = plan['copy']
    if plan['overlay']:
        # Quiet regions already have low variation. Choose contrasting ink;
        # never put a dark rectangle over an otherwise usable photograph.
        fill = _ink(ImageStat.Stat(image.crop(box)).mean)
    else:
        fill = _ink(surface)
    draw = ImageDraw.Draw(image)
    title, body, title_font, body_font = fit_copy(draw, direction, box, plan['title_size'])
    y = _draw_lines(draw,title,title_font,box,box[1],fill,plan['align'],True)
    _draw_lines(draw,body,body_font,box,y+28,fill,plan['align'])
    # A reserved, low-noise brand line. Exact logos never cover copy or subjects.
    brand_style = getattr(direction,'brand_style','text')
    if logo_path and Path(logo_path).is_file():
        from services.campaign_renderer import _normalized_logo
        logo = _normalized_logo(logo_path)
        logo.thumbnail((280,90),Image.Resampling.LANCZOS)
        image.paste(logo,(72,60),logo)
    elif brand_style != 'none':
        label_color = _ink(ImageStat.Stat(image.crop((64,50,700,150))).mean)
        brand_font = _font(26,True,'ko')
        brand_lines = _lines(draw,company,brand_font,936)
        if len(brand_lines)>2:
            raise ValueError('Brand name too long for reserved area')
        _draw_lines(draw,brand_lines,brand_font,(72,58,1008,160),58,label_color,'left',True)
    style = getattr(direction,'cta_style','auto')
    if style == 'auto':
        style = 'text' if direction.message_angle == 'offer_action' else 'none'
    if footer_detail:
        style = 'none'
    if direction.cta and style != 'none':
        color = _ink(ImageStat.Stat(image.crop((64,1220,1008,1310))).mean)
        font = _font(26,True,'ko')
        cta_lines = _lines(draw,direction.cta,font,880)
        if len(cta_lines)>2:
            raise ValueError('CTA too long for reserved area')
        if style == 'button':
            draw.rectangle((64,1210,1016,1320),fill=accent)
            color = _ink(accent)
        _draw_lines(draw,cta_lines,font,(88,1232,968,1320),1232,color,'left',True)
    if footer_detail:
        # Contact details take the reserved footer; never collide with an action.
        font = _font(22,False,'ko')
        rows = _lines(draw,footer_detail,font,936)
        if len(rows)>2:
            raise ValueError('Contact detail too long')
        _draw_lines(draw,rows,font,(72,1230,1008,1330),1230,_ink(surface),'left')
    target = Path(output_path)
    target.parent.mkdir(parents=True,exist_ok=True)
    image.save(target,'PNG',optimize=True)
    return target
