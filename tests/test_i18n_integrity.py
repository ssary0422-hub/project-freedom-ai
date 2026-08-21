import re
import unittest
from pathlib import Path

from i18n.translations import SUPPORTED_LANGUAGES, TRANSLATIONS, translate


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_KEY = re.compile(r'''\bt\(\s*["']([^"']+)["']''')


class I18nIntegrityTests(unittest.TestCase):
    def test_every_template_translation_key_exists_in_every_language(self):
        used_keys = set()
        for template in (ROOT / "templates").glob("*.html"):
            used_keys.update(TEMPLATE_KEY.findall(template.read_text(encoding="utf-8")))

        for language in SUPPORTED_LANGUAGES:
            missing = sorted(used_keys - TRANSLATIONS[language].keys())
            self.assertEqual(missing, [], f"{language} is missing template keys: {missing}")

    def test_languages_do_not_silently_fall_back_for_korean_keys(self):
        korean_keys = set(TRANSLATIONS["ko"])
        for language in SUPPORTED_LANGUAGES:
            missing = sorted(korean_keys - TRANSLATIONS[language].keys())
            self.assertEqual(missing, [], f"{language} falls back to Korean for: {missing}")

    def test_unknown_keys_remain_visible_for_diagnostics(self):
        self.assertEqual(translate("audit.unknown-key", "en"), "audit.unknown-key")

    def test_new_landing_sections_are_really_localized(self):
        keys = (
            "landing.task.label",
            "landing.approved.title",
            "landing.approved.desc",
            "landing.pricing.poster",
        )
        for language in SUPPORTED_LANGUAGES:
            for key in keys:
                self.assertNotEqual(translate(key, language), key)
                if language != "ko":
                    self.assertNotEqual(translate(key, language), translate(key, "ko"))


if __name__ == "__main__":
    unittest.main()
