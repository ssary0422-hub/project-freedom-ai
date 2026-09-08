from app import app
from database import db


def test_dashboard_opens_without_retired_brand_tables(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'dashboard.db')
    monkeypatch.setattr(db, 'USE_POSTGRES', False)
    client = app.test_client()
    with client.session_transaction() as session:
        session.update(user_id=991, language='ko')
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert '아직 저장된 작업이 없어요.' in response.get_data(as_text=True)
    connection = db._connect()
    try:
        assert not connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='brand_profiles'").fetchall()
    finally:
        connection.close()


def test_dashboard_only_lists_current_work_owned_by_user(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'dashboard.db')
    monkeypatch.setattr(db, 'USE_POSTGRES', False)
    for number in range(8):
        db.save_history('cafe', f'My work {number}', 'warm', 'body', user_id=991, content_type='sns')
    db.save_history('cafe', 'Other account secret', 'warm', 'body', user_id=992)
    old_id = db.save_history('cafe', 'Outdated version', 'warm', 'body', user_id=991)
    connection = db._connect()
    try:
        connection.execute('UPDATE history SET is_current=0 WHERE id=?', (old_id,))
        connection.commit()
    finally:
        connection.close()
    summary = db.get_dashboard_data(991)
    assert summary['content_count'] == 8
    assert [item['company'] for item in summary['recent_contents']] == [f'My work {n}' for n in range(7, 1, -1)]
    client = app.test_client()
    with client.session_transaction() as session:
        session.update(user_id=991, language='ko')
    response = client.get('/dashboard')
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'My work 7' in html
    assert 'Other account secret' not in html
    assert 'Outdated version' not in html
    assert '/history#history-result-' in html
    assert 'href="/profiles' not in html


def test_dashboard_requires_login():
    response = app.test_client().get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
