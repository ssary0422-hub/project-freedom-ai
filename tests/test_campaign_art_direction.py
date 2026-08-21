import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.campaign_art_direction import create_art_directions, direction_from_payload


def three_concepts():
    return json.dumps([
        {
            "concept_name": "현장 몰입",
            "campaign_angle": "실제 공간에서 바로 느끼는 편안함",
            "layout_family": "full_bleed_photo",
            "message_angle": "customer_outcome",
            "photo_strategy": "uploaded_photo_full_bleed",
            "subject_position": "right",
            "headline_position": "upper_left",
            "mood": "warm",
            "headline": "오늘의 피로를 내려놓으세요",
            "supporting_copy": "실제 공간의 분위기를 먼저 보여줍니다",
            "cta": "위치 확인하기",
            "palette": ["#14211f", "#e5b879", "#fffaf1"],
            "avoid": ["information card"],
        },
        {
            "concept_name": "가까운 해결",
            "campaign_angle": "이동 동선 안에서 쉬는 선택",
            "layout_family": "split_scene",
            "message_angle": "local_convenience",
            "photo_strategy": "uploaded_photo_split",
            "subject_position": "left",
            "headline_position": "right",
            "mood": "clear",
            "headline": "가까운 곳에서 잠시 쉬어가세요",
            "supporting_copy": "위치와 실제 공간을 나누어 보여줍니다",
            "cta": "길 찾기",
            "palette": ["#f4efe8", "#1d6b62", "#132321"],
            "avoid": ["top-right circle"],
        },
        {
            "concept_name": "지금 행동",
            "campaign_angle": "복잡한 설명 없이 문의로 연결",
            "layout_family": "bold_offer",
            "message_angle": "offer_action",
            "photo_strategy": "uploaded_photo_cutout",
            "subject_position": "center",
            "headline_position": "top",
            "mood": "energetic",
            "headline": "필요할 때 바로 문의하세요",
            "supporting_copy": "행동 문구를 가장 크게 보여줍니다",
            "cta": "문의하기",
            "palette": ["#f0ff65", "#161616", "#ffffff"],
            "avoid": ["navy template"],
        },
    ], ensure_ascii=False)


class CampaignArtDirectionTests(unittest.TestCase):
    def test_creates_three_structurally_distinct_concepts(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
            "services.campaign_art_direction.HISTORY_PATH", Path(tmp) / "history.json"
        ):
            directions = create_art_directions(
                business="마사지",
                company="7day's massage",
                request="터미널21 근처에서 여행객의 피로를 풀어주는 마사지",
                media="sns",
                photo_count=2,
                generator=lambda _: three_concepts(),
            )
            self.assertEqual(len({item.layout_family for item in directions}), 3)
            self.assertEqual(len({item.message_angle for item in directions}), 3)
            self.assertEqual(len({item.photo_strategy for item in directions}), 3)

    def test_rejects_color_variants_of_one_template(self):
        payload = json.loads(three_concepts())
        for item in payload:
            item["layout_family"] = "full_bleed_photo"
        with tempfile.TemporaryDirectory() as tmp, patch(
            "services.campaign_art_direction.HISTORY_PATH", Path(tmp) / "history.json"
        ):
            with self.assertRaisesRegex(ValueError, "different layouts"):
                create_art_directions(
                    business="카페", company="테스트", request="신메뉴", media="ads",
                    generator=lambda _: json.dumps(payload, ensure_ascii=False),
                )

    def test_media_contract_rejects_unknown_output(self):
        with self.assertRaisesRegex(ValueError, "Unsupported media"):
            create_art_directions(
                business="카페", company="테스트", request="신메뉴", media="video",
                generator=lambda _: three_concepts(),
            )

    def test_selected_browser_direction_is_validated(self):
        payload = json.loads(three_concepts())[0]
        direction = direction_from_payload(payload)
        self.assertEqual(direction.layout_family, "full_bleed_photo")
        payload["layout_family"] = "browser_injected_layout"
        with self.assertRaisesRegex(ValueError, "Unknown layout"):
            direction_from_payload(payload)


if __name__ == "__main__":
    unittest.main()
