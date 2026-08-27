import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import database.users as users
from database.sungeum_walk import leaderboard, start_game, submit_score


class SungeumWalkRewardTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(users, "DB_PATH", Path(self.temp_dir.name) / "walk.db")
        self.db_patch.start()
        self.user_one = users.create_user("one@example.com", "첫번째", "password123")
        self.user_two = users.create_user("two@example.com", "두번째", "password123")

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def _play(self, user_id, score, start_time, finish_time):
        with patch("database.sungeum_walk._now_utc", return_value=start_time):
            token = start_game(user_id)
        with patch("database.sungeum_walk._now_utc", return_value=finish_time):
            return submit_score(user_id, token, score)

    def test_higher_score_leads_and_personal_best_does_not_go_backwards(self):
        start = datetime(2026, 8, 27, 1, 0, 0, tzinfo=timezone.utc)
        result = self._play(self.user_one, 8, start, datetime(2026, 8, 27, 1, 0, 10, tzinfo=timezone.utc))
        self.assertEqual(result["my_rank"], 1)
        self.assertEqual(result["my_best"], 8)
        result = self._play(self.user_one, 3, start, datetime(2026, 8, 27, 1, 0, 10, tzinfo=timezone.utc))
        self.assertEqual(result["my_best"], 8)

    def test_tie_is_won_by_first_achievement(self):
        first_start = datetime(2026, 8, 27, 2, 0, 0, tzinfo=timezone.utc)
        second_start = datetime(2026, 8, 27, 2, 1, 0, tzinfo=timezone.utc)
        self._play(self.user_one, 5, first_start, datetime(2026, 8, 27, 2, 0, 8, tzinfo=timezone.utc))
        result = self._play(self.user_two, 5, second_start, datetime(2026, 8, 27, 2, 1, 8, tzinfo=timezone.utc))
        self.assertEqual(result["ranking"][0]["name"], "첫**")
        self.assertEqual(result["my_rank"], 2)

    def test_completed_day_awards_five_credits_once(self):
        start = datetime(2026, 8, 26, 2, 0, 0, tzinfo=timezone.utc)
        self._play(self.user_one, 7, start, datetime(2026, 8, 26, 2, 0, 10, tzinfo=timezone.utc))
        with patch("database.sungeum_walk._now_utc", return_value=datetime(2026, 8, 27, 2, 0, 0, tzinfo=timezone.utc)):
            leaderboard(self.user_one)
            leaderboard(self.user_one)
        self.assertEqual(users.get_bonus_credit_balance(self.user_one), 5)
        transactions = users.get_credit_transactions(self.user_one)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]["kind"], "SUNGEUM_WALK_DAILY_WINNER")

    def test_impossible_score_is_rejected(self):
        start = datetime(2026, 8, 27, 3, 0, 0, tzinfo=timezone.utc)
        with patch("database.sungeum_walk._now_utc", return_value=start):
            token = start_game(self.user_one)
        with patch("database.sungeum_walk._now_utc", return_value=datetime(2026, 8, 27, 3, 0, 2, tzinfo=timezone.utc)):
            with self.assertRaisesRegex(ValueError, "invalid_play"):
                submit_score(self.user_one, token, 100)


if __name__ == "__main__":
    unittest.main()
