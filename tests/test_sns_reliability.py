import json
from dataclasses import asdict
from unittest.mock import Mock
from PIL import Image
from app import app
from routes import sns
from tests.test_content_flows import TEST_DIRECTION, READY


def setup_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(sns, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(sns, 'get_ai_enabled', lambda: True)
    monkeypatch.setattr(sns, 'get_plan_status', lambda *a, **k: READY)
    monkeypatch.setattr(sns, 'get_recent_sns_copy', lambda *a: ['맥도날드: 한 입의 즐거움'])
    monkeypatch.setattr(sns, 'make_sns', lambda *a, **k: '점심 고민은 여기까지. 새 콘셉트입니다.')
    for name in ('create_sns_word', 'create_sns_pdf'):
        monkeypatch.setattr(sns, name, Mock())
    save, usage = Mock(return_value=107), Mock()
    monkeypatch.setattr(sns, 'save_history', save)
    monkeypatch.setattr(sns, 'record_ai_credit_usage', usage)
    monkeypatch.setattr(sns, 'create_art_directions', lambda **k: [TEST_DIRECTION])
    monkeypatch.setattr(sns, 'analyze_image_json', lambda *a: {'score': 98, 'approved': True, 'blockers': []})
    background = tmp_path / 'photo.png'
    Image.new('RGB', (1024, 1024), '#faf4e8').save(background)
    monkeypatch.setattr(sns, 'make_image', Mock(return_value=str(background)))
    client = app.test_client()
    with client.session_transaction() as session:
        session.update(user_id=999999, language='ko')
    data = dict(business='버거', company='롯데리아', style='점심 메뉴 고민', platform='인스타그램',
                with_image='on', image_output_mode='finished_card',
                selected_art_direction=json.dumps(asdict(TEST_DIRECTION)))
    return client, data, save, usage


def test_real_composition_runs_through_sns_route(tmp_path, monkeypatch):
    client, data, save, usage = setup_flow(tmp_path, monkeypatch)
    response = client.post('/sns', data=data)
    assert response.status_code == 200
    assert '/static/generated/finished-sns-' in response.get_data(as_text=True)
    paths = list((tmp_path / 'static/generated').glob('finished-sns-*.png'))
    assert len(paths) == 1
    with Image.open(paths[0]) as output:
        assert output.size == (1080, 1350)
    assert save.call_args.args[4].startswith('/static/generated/')
    usage.assert_called_once_with(999999, 'SNS_IMAGE', 3)


def test_failed_image_does_not_charge_or_fake_a_finished_card(tmp_path, monkeypatch):
    client, data, save, usage = setup_flow(tmp_path, monkeypatch)
    monkeypatch.setattr(sns, 'make_image', Mock(side_effect=RuntimeError('private provider data')))
    fallback = Mock()
    monkeypatch.setattr(sns, 'create_finished_promo_card', fallback)
    response = client.post('/sns', data=data)
    html = response.get_data(as_text=True)
    assert '이미지만 다시 생성' in html
    assert '<div class="sungeum-quality-stamp"' not in html
    assert 'private provider data' not in html
    assert save.call_args.args[4] == ''
    fallback.assert_not_called()
    usage.assert_called_once_with(999999, 'SNS_TEXT', 1)
    diagnostic = client.get('/sns/image-status').json
    assert diagnostic['chain'][0]['type'] == 'RuntimeError'
    assert 'private provider data' not in json.dumps(diagnostic)


def test_failed_retry_preserves_previous_result_and_is_free(tmp_path, monkeypatch):
    client, data, save, usage = setup_flow(tmp_path, monkeypatch)
    monkeypatch.setattr(sns, 'get_history_item', lambda *a: (107, '버거', '롯데리아', '점심', '기존 글', '/old.png', 'sns'))
    update = Mock()
    monkeypatch.setattr(sns, 'update_history_image', update)
    monkeypatch.setattr(sns, 'make_image', Mock(side_effect=RuntimeError('provider down')))
    response = client.post('/sns/retry-image', data={'history_id': 107})
    assert '크레딧은 차감하지 않았습니다' in response.get_data(as_text=True)
    update.assert_not_called()
    usage.assert_not_called()


def test_retry_renders_selected_copy_without_regenerating_caption(tmp_path, monkeypatch):
    client, data, save, usage = setup_flow(tmp_path, monkeypatch)
    monkeypatch.setattr(sns, 'get_history_item', lambda *a: (107, '버거', '롯데리아', '점심', '보존할 기존 글', '', 'sns'))
    update, planner, writer = Mock(return_value=True), Mock(side_effect=AssertionError('Selected direction exists')), Mock()
    monkeypatch.setattr(sns, 'update_history_image', update)
    monkeypatch.setattr(sns, 'create_art_directions', planner)
    monkeypatch.setattr(sns, 'make_sns', writer)
    response = client.post('/sns/retry-image', data={'history_id': 107, 'selected_art_direction': data['selected_art_direction']})
    assert '보존할 기존 글' in response.get_data(as_text=True)
    update.assert_called_once()
    assert update.call_args.args[2].startswith('/static/generated/finished-sns-')
    writer.assert_not_called()
    usage.assert_called_once_with(999999, 'SNS_IMAGE_RETRY', 2)


def test_sns_copy_uses_recent_openings_and_avoids_production_language(monkeypatch):
    from ai import sns as copy
    generate = Mock(return_value='점심 고민 끝.')
    monkeypatch.setattr(copy, 'generate_with_quality_check', generate)
    copy.make_sns('버거', '롯데리아', '점심 선택', 'Instagram', recent_copy=['맥도날드: 한 입의 즐거움'])
    prompt = generate.call_args.args[1]
    assert '맥도날드: 한 입의 즐거움' in prompt
    assert 'not just the brand name' in prompt
    assert 'not customer-facing copy' in prompt


def test_korean_headline_does_not_leave_word_ending_on_its_own_line():
    from PIL import ImageDraw
    from services.campaign_layout import _lines
    from services.finished_promo_card import _font
    draw = ImageDraw.Draw(Image.new('RGB', (1080, 1350)))
    font = _font(112, True, 'ko')
    lines = _lines(draw, '고민 길면, 점심 늦는다.', font, 936)
    assert '다.' not in lines
    assert any('늦는다.' in line for line in lines)
    assert all(draw.textlength(line, font=font) <= 936 for line in lines)


def test_retried_history_image_is_not_cached_as_immutable(monkeypatch):
    from routes import history
    monkeypatch.setattr(history, 'get_history_image', lambda *a: (b'updated-image', 'image/png'))
    client = app.test_client()
    with client.session_transaction() as session:
        session['user_id'] = 999999
    response = client.get('/history/image/107')
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'private, no-store'
    assert response.data == b'updated-image'
