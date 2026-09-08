"""Run app regression checks without touching the workspace database."""
import importlib
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DATABASE_URL'] = ''
os.environ['ADMIN_EMAIL'] = ''
with tempfile.TemporaryDirectory(prefix='pfa-studio-tests-') as temporary:
    for name in ('database.db', 'database.users', 'database.profiles'):
        module = importlib.import_module(name)
        module.DB_PATH = Path(temporary) / 'test.db'
        module.USE_POSTGRES = False
    import pytest
    result = pytest.main(['-q', '--tb=short', 'tests/test_landing_showcase.py', 'tests/test_content_flows.py',
                          'tests/test_running_form.py', 'tests/test_running_coach.py',
                          'tests/test_speaking_coach.py', 'tests/test_i18n_integrity.py',
                          'tests/test_request_security.py', 'tests/test_campaign_composition.py',
                          'tests/test_campaign_renderer.py', 'tests/test_campaign_art_direction.py',
                          'tests/test_campaign_budget.py', 'tests/test_campaign_quality.py',
                          'tests/test_image_prompts.py'])
    sys.exit(result)
