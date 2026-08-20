import unittest
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app import app


READY = {
    "can_generate": True,
    "plan": "TEST",
    "used": 0,
    "limit": 100,
    "remaining": 100,
    "percent": 0,
}


class ContentFlowTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = 999999
            session["user_name"] = "Tester"
            session["user_email"] = "tester@example.com"
            session["language"] = "ko"

    def _common_patches(self, module, maker_name, result):
        return [
            patch(f"routes.{module}.get_ai_enabled", return_value=True),
            patch(f"routes.{module}.get_plan_status", return_value=READY),
            patch(f"routes.{module}.get_profiles", return_value=[]),
            patch(f"routes.{module}.{maker_name}", return_value=result),
            patch(f"routes.{module}.save_history", return_value=1),
            patch(f"routes.{module}.record_ai_credit_usage"),
        ]

    def _run_with(self, patches, callback):
        started = [item.start() for item in patches]
        self.addCleanup(lambda: [item.stop() for item in reversed(patches)])
        return callback(started)

    def test_ads_text_generation(self):
        patches = self._common_patches("ads", "make_ads", "ADS_RESULT_OK") + [
            patch("routes.ads.create_word"),
            patch("routes.ads.create_pdf"),
        ]
        response = self._run_with(patches, lambda _: self.client.post(
            "/ads-generator",
            data={"business": "카페", "company": "오늘의커피", "style": "따뜻함"},
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ADS_RESULT_OK", response.data)

    def test_ads_image_failure_keeps_retry_available_after_refresh(self):
        patches = self._common_patches("ads", "make_ads", "ADS_TEXT_SURVIVES") + [
            patch("routes.ads.make_image", side_effect=RuntimeError("provider down")),
            patch("routes.ads.create_word"),
            patch("routes.ads.create_pdf"),
            patch("routes.ads.get_history_item", return_value=(
                1, "massage", "Seven Days", "premium", "ADS_TEXT_SURVIVES", "", "ads"
            )),
        ]
        def run(_):
            first = self.client.post("/ads-generator", data={
                "business": "massage", "company": "Seven Days", "style": "premium",
                "with_image": "on", "image_style": "AI 추천",
            })
            refreshed = self.client.get("/ads-generator")
            return first, refreshed
        first, refreshed = self._run_with(patches, run)
        self.assertIn("이미지 생성 다시 시도".encode(), first.data)
        self.assertIn("이미지 생성 다시 시도".encode(), refreshed.data)

    @patch("routes.ads.make_image", side_effect=[
        RuntimeError("moderation_blocked safety_violations sexual"),
        "static/generated/safe.png",
    ])
    def test_ads_safety_block_uses_family_friendly_fallback(self, make_image_mock):
        path = __import__("routes.ads", fromlist=["_generate_ad_image"])._generate_ad_image(
            "massage", "Seven Days", "premium", "AI 추천"
        )
        self.assertEqual(path, "static/generated/safe.png")
        self.assertEqual(make_image_mock.call_count, 2)
        self.assertIn("No people", make_image_mock.call_args_list[1].args[0])

    def test_blog_text_generation_with_photo_guidance(self):
        patches = self._common_patches("blog", "make_blog", "BLOG_RESULT_OK") + [
            patch("routes.blog.save_files", return_value=[(1, "menu.jpg")]),
            patch("routes.blog.create_blog_word"),
            patch("routes.blog.create_blog_pdf"),
        ]
        response = self._run_with(patches, lambda _: self.client.post(
            "/blog",
            data={
                "business": "카페", "company": "오늘의커피", "topic": "신메뉴",
                "tone": "친근함", "length": "1000자",
            },
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BLOG_RESULT_OK", response.data)

    @patch("routes.blog.get_profiles", return_value=[])
    @patch("routes.blog.save_files", return_value=[(77, "store.jpg")])
    @patch("routes.blog.get_history_item", return_value=(
        12, "카페", "오늘의커피", "따뜻함", "BLOG_FINAL_OK", "", "blog"
    ))
    def test_blog_finalize_adds_photos_without_new_ai_call(self, *_):
        response = self.client.post(
            "/blog/finalize",
            data={
                "history_id": "12",
                "blog_photos": (io.BytesIO(b"fake-image"), "store.jpg"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BLOG_FINAL_OK", response.data)
        self.assertIn(b"blogFinalPreview", response.data)

    def test_sns_text_generation(self):
        patches = self._common_patches("sns", "make_sns", "SNS_RESULT_OK") + [
            patch("routes.sns.create_sns_word"),
            patch("routes.sns.create_sns_pdf"),
        ]
        response = self._run_with(patches, lambda _: self.client.post(
            "/sns",
            data={
                "business": "카페", "company": "오늘의커피", "style": "활기참",
                "platform": "Instagram",
            },
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SNS_RESULT_OK", response.data)

    def test_sns_image_failure_keeps_text_and_offers_image_only_retry(self):
        patches = self._common_patches("sns", "make_sns", "SNS_TEXT_SURVIVES") + [
            patch("routes.sns.make_image", side_effect=RuntimeError("image provider down")),
            patch("routes.sns.create_sns_word"),
            patch("routes.sns.create_sns_pdf"),
        ]
        response = self._run_with(patches, lambda _: self.client.post(
            "/sns",
            data={
                "business": "카페", "company": "테스트카페",
                "style": "따뜻한 신메뉴 홍보", "platform": "Instagram",
                "with_image": "on", "image_style": "AI 추천",
            },
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SNS_TEXT_SURVIVES", response.data)
        self.assertIn("이미지만 다시 생성".encode(), response.data)

    @patch("routes.sns.get_profiles", return_value=[])
    @patch("routes.sns.record_ai_credit_usage")
    @patch("routes.sns.create_sns_pdf")
    @patch("routes.sns.create_sns_word")
    @patch("routes.sns.update_history_image", return_value=True)
    @patch("routes.sns.make_image", return_value="static/generated/retry.png")
    @patch("routes.sns.get_history_item", return_value=(
        77, "카페", "테스트카페", "따뜻한 홍보", "SNS_RETRY_RESULT", "", "sns"
    ))
    @patch("routes.sns.get_plan_status", return_value=READY)
    def test_sns_image_only_retry_attaches_image_and_charges_two(self, *mocks):
        response = self.client.post(
            "/sns/retry-image",
            data={"history_id": "77", "platform": "Instagram", "image_style": "AI 추천"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SNS_RETRY_RESULT", response.data)
        self.assertIn(b"/static/generated/retry.png", response.data)
        record_usage = mocks[6]
        record_usage.assert_called_once_with(999999, "SNS_IMAGE_RETRY", 2)

    def test_poster_page_is_generic_and_randomized(self):
        response = self.client.get("/poster")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'value="Project Freedom AI"', response.data)
        js = self.client.get("/static/poster-maker.js")
        self.assertIn(b"rotateExamples", js.data)
        self.assertIn(b"rawLines", js.data)
        self.assertIn(b"makeOneClick", js.data)
        self.assertIn("순금이가 포스터 완성".encode(), response.data)
        self.assertIn("보통 1~2분 정도 걸려요".encode(), response.data)
        self.assertIn("원하는 분만 직접 설정하기".encode(), response.data)
        js.close()

    def test_all_post_forms_show_loading_overlay(self):
        source = Path("templates/generator_base.html").read_text(encoding="utf-8")
        self.assertIn('querySelectorAll("form[method=\'POST\']")', source)
        self.assertIn("⏳ 이미지 생성 중", source)

    def test_sungeum_assistant_has_visible_click_guidance(self):
        source = Path("templates/_sungeum_assistant.html").read_text(encoding="utf-8")
        self.assertIn("순금이에게 물어보기", source)

    def test_generated_media_has_direct_image_download(self):
        source = Path("templates/generator_base.html").read_text(encoding="utf-8")
        self.assertIn('class="btn btn-outline-primary image-download-btn"', source)
        self.assertIn("download=\"{{ active_tab or 'content' }}-image.png\"", source)

    @patch("routes.poster.record_ai_credit_usage")
    @patch("routes.poster.get_plan_status", return_value=READY)
    @patch("routes.poster.generate_text", return_value=(
        "제목1|혜택1|이벤트1|문의1\n제목2|혜택2|이벤트2|문의2\n제목3|혜택3|이벤트3|문의3"
    ))
    def test_poster_ai_copy_returns_three_choices(self, *_):
        response = self.client.post(
            "/poster/suggest",
            json={"business": "오늘의커피", "purpose": "여름 행사"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["sets"]), 3)

    @patch("routes.poster.record_ai_credit_usage")
    @patch("routes.poster.get_plan_status", return_value=READY)
    @patch("routes.poster.generate_text", return_value=(
        "파타야 터미널21 근처 마사지 찾는 분|가까운 위치에서 가성비 좋고 전문적인 마사지로 여행 중 피로를 편하게 풀어보세요|파타야 터미널21 인근 가성비좋고 전문적인 마사지샵|상담 및 예약 문의 01031255836"
    ))
    def test_poster_ai_copy_compacts_overflow_and_formats_phone(self, *_):
        response = self.client.post(
            "/poster/suggest",
            json={"business": "7day's massage", "purpose": "마사지 예약 01031255836"},
        )
        self.assertEqual(response.status_code, 200)
        result = response.get_json()["sets"][0]
        self.assertLessEqual(len(result[0]), 22)
        self.assertLessEqual(len(result[1]), 42)
        self.assertLessEqual(len(result[2]), 18)
        self.assertEqual(result[3], "예약 문의 010-3125-5836")

    def test_all_main_pages_render(self):
        with patch("routes.ads.get_profiles", return_value=[]), \
             patch("routes.blog.get_profiles", return_value=[]), \
             patch("routes.sns.get_profiles", return_value=[]), \
             patch("routes.brand_library.media_for_user", return_value=[]):
            for path in ("/ads-generator", "/blog", "/sns", "/poster", "/brand-library"):
                with self.subTest(path=path):
                    self.assertEqual(self.client.get(path).status_code, 200)

    def test_main_forms_use_simple_request_first_design(self):
        with patch("routes.ads.get_profiles", return_value=[]), \
             patch("routes.blog.get_profiles", return_value=[]), \
             patch("routes.sns.get_profiles", return_value=[]):
            expected = {
                "/ads-generator": "무엇을 홍보하고 싶나요?",
                "/sns": "어떤 내용을 올리고 싶나요?",
                "/blog": "어떤 글을 만들고 싶나요?",
                "/poster": "무엇을 홍보하고 싶나요?",
            }
            for path, phrase in expected.items():
                with self.subTest(path=path):
                    html = self.client.get(path).get_data(as_text=True)
                    self.assertIn(phrase, html)
                    self.assertIn("AI가 업종에 맞게 추천", html)

    def test_customer_navigation_focuses_on_four_creation_tools(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["user_name"] = "테스트"
            session["is_admin"] = False
        html = self.client.get("/").get_data(as_text=True)
        for path in ("/ads-generator", "/sns", "/blog", "/poster"):
            self.assertIn(f'href="{path}"', html)

        with patch("routes.ads.get_profiles", return_value=[]):
            page = self.client.get("/ads-generator").get_data(as_text=True)
            navbar = page.split("</nav>", 1)[0]
        for hidden_path in ("/dashboard", "/ai-office", "/brand-library", "/profiles"):
            self.assertNotIn(f'href="{hidden_path}"', navbar)

    def test_word_and_pdf_exports_for_all_content_types(self):
        from documents import pdf, word

        with TemporaryDirectory() as directory:
            root = Path(directory)
            output_paths = {
                "WORD_PATH": root / "advertisement.docx",
                "BLOG_WORD_PATH": root / "blog.docx",
                "SNS_WORD_PATH": root / "sns.docx",
                "PDF_PATH": root / "advertisement.pdf",
                "BLOG_PDF_PATH": root / "blog.pdf",
                "SNS_PDF_PATH": root / "sns.pdf",
            }
            with patch.object(word, "WORD_PATH", str(output_paths["WORD_PATH"])), \
                 patch.object(word, "BLOG_WORD_PATH", str(output_paths["BLOG_WORD_PATH"])), \
                 patch.object(word, "SNS_WORD_PATH", str(output_paths["SNS_WORD_PATH"])), \
                 patch.object(pdf, "PDF_PATH", str(output_paths["PDF_PATH"])), \
                 patch.object(pdf, "BLOG_PDF_PATH", str(output_paths["BLOG_PDF_PATH"])), \
                 patch.object(pdf, "SNS_PDF_PATH", str(output_paths["SNS_PDF_PATH"])):
                word.create_word("광고 결과")
                word.create_blog_word("블로그 결과")
                word.create_sns_word("SNS 결과")
                pdf.create_pdf("광고 결과")
                pdf.create_blog_pdf("블로그 결과")
                pdf.create_sns_pdf("SNS 결과")

            for name, path in output_paths.items():
                with self.subTest(name=name):
                    self.assertTrue(path.exists())
                    self.assertGreater(path.stat().st_size, 100)
                    expected = b"%PDF" if name.endswith("PDF_PATH") else b"PK"
                    self.assertEqual(path.read_bytes()[:len(expected)], expected)


if __name__ == "__main__":
    unittest.main()
