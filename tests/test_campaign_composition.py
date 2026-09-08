from dataclasses import replace
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from services.campaign_art_direction import ArtDirection, LAYOUT_FAMILIES
from services.campaign_layout import plan_composition, fit_copy
from services.campaign_renderer import render_campaign_concept
from services.campaign_budget import generate_with_bounded_backgrounds
from ai.image_prompts import build_campaign_background_prompt


def direction(**changes):
    base = ArtDirection('제품', '한 가지 메시지', 'product_closeup', 'brand_story', 'studio',
                        'right', 'top_left', 'soft light', '한 입의 즐거움',
                        '음식 이미지와 짧은 문구의 조합입니다.', '',
                        ('#c41218', '#ffcc00', '#fff8ed'), (), visual_scene='one cheeseburger')
    return replace(base, **changes)


@pytest.mark.parametrize('family', LAYOUT_FAMILIES)
def test_photo_and_text_regions_are_disjoint_and_all_copy_fits(family):
    photo = Image.effect_noise((1080,1350),90).convert('RGB')
    d = direction(layout_family=family)
    p = plan_composition(d, photo)
    assert not p['overlay']  # busy image uses a separate text area
    a,b = p['copy'],p['photo']
    assert a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1]
    for box in (a,b):
        assert 0<=box[0]<box[2]<=1080 and 0<=box[1]<box[3]<=1350
    title,body,_,_=fit_copy(ImageDraw.Draw(photo),d,a,p['title_size'])
    assert ''.join(title).replace(' ','')==d.headline.replace(' ','')
    assert ''.join(body).replace(' ','')==d.supporting_copy.replace(' ','')


def test_position_changes_real_composition():
    photo=Image.new('RGB',(1080,1350),'#bb0011')
    left=plan_composition(direction(layout_family='split_scene'),photo)
    right=plan_composition(direction(layout_family='split_scene',headline_position='top_right'),photo)
    assert left['copy'][2]<right['copy'][0]
    assert left['photo'][0]>right['photo'][0]
    upper=plan_composition(direction(),photo)
    lower=plan_composition(direction(headline_position='bottom_left'),photo)
    assert upper['copy'][3]<upper['photo'][1]
    assert lower['copy'][1]>lower['photo'][3]


def test_background_prompt_never_receives_printable_campaign_copy():
    d=direction(headline='HEADLINE_SENTINEL',supporting_copy='BODY_SENTINEL',cta='CTA_SENTINEL')
    prompt=build_campaign_background_prompt(business='food',direction=d)
    assert 'one cheeseburger' in prompt
    assert all(value not in prompt for value in (d.headline,d.supporting_copy,d.cta))
    assert 'ZERO readable text' in prompt


def test_no_forced_brand_or_button_and_palette_is_preserved(tmp_path):
    source=tmp_path/'photo.png';Image.new('RGB',(800,600),'#779966').save(source)
    d=direction(layout_family='bold_offer',brand_style='none',cta_style='none')
    output=render_campaign_concept(background_path=source,direction=d,company='Brand',output_path=tmp_path/'out.png')
    with Image.open(output) as image:
        assert image.getpixel((75,75))==(196,18,24)
        assert image.getpixel((100,1250))==(196,18,24)


def test_overlong_copy_is_rejected_instead_of_silently_clipped():
    canvas=Image.new('RGB',(1080,1350))
    with pytest.raises(ValueError,match='does not fit'):
        fit_copy(ImageDraw.Draw(canvas),direction(headline='긴문장'*2000),(0,0,300,200),80)


def test_high_score_cannot_override_duplicate_text_blocker(tmp_path):
    with pytest.raises(ValueError):
        generate_with_bounded_backgrounds(directions=[direction()],
            generate_background=lambda _:tmp_path/'source.png',
            render_candidate=lambda *args:tmp_path/'result.png',
            evaluate_candidate=lambda _:dict(score=99,approved=True,blockers=['duplicated text']),
            prefer_generated_on_failure=True)
