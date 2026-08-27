import secrets
from datetime import datetime, timedelta, timezone
from database.users import USE_POSTGRES, _connect, init_users_table


KST = timezone(timedelta(hours=9))
DAILY_REWARD_CREDITS = 5


def _now_utc():
    return datetime.now(timezone.utc)


def _kst_date(value=None):
    return (value or _now_utc()).astimezone(KST).date().isoformat()


def init_sungeum_walk_tables():
    init_users_table()
    conn = _connect()
    cursor = conn.cursor()
    id_column = "BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sungeum_walk_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            submitted_at TEXT,
            score INTEGER
        )
    """)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS sungeum_walk_scores (
            id {id_column},
            play_date TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            achieved_at TEXT NOT NULL,
            UNIQUE(play_date, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sungeum_walk_rewards (
            play_date TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            credits INTEGER NOT NULL,
            awarded_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sungeum_walk_scores_daily
        ON sungeum_walk_scores (play_date, score DESC, achieved_at ASC)
    """)
    conn.commit()
    conn.close()


def _award_unsettled_days():
    """Award each completed KST day once, atomically with the wallet update."""
    init_sungeum_walk_tables()
    today = _kst_date()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")
    cursor.execute("""
        SELECT DISTINCT s.play_date
        FROM sungeum_walk_scores s
        LEFT JOIN sungeum_walk_rewards r ON r.play_date = s.play_date
        WHERE s.play_date < ? AND r.play_date IS NULL
        ORDER BY s.play_date ASC
    """, (today,))
    dates = [row[0] for row in cursor.fetchall()]
    now = _now_utc().isoformat()
    for play_date in dates:
        cursor.execute("""
            SELECT user_id, score
            FROM sungeum_walk_scores
            WHERE play_date = ?
            ORDER BY score DESC, achieved_at ASC
            LIMIT 1
        """, (play_date,))
        winner = cursor.fetchone()
        if not winner:
            continue
        user_id, score = int(winner[0]), int(winner[1])
        cursor.execute("""
            INSERT INTO sungeum_walk_rewards
                (play_date, user_id, score, credits, awarded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (play_date, user_id, score, DAILY_REWARD_CREDITS, now))
        cursor.execute("""
            INSERT INTO ai_credit_wallet (user_id, balance, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                balance = ai_credit_wallet.balance + excluded.balance,
                updated_at = excluded.updated_at
        """, (user_id, DAILY_REWARD_CREDITS, now))
        cursor.execute("""
            INSERT INTO ai_credit_transactions
                (user_id, amount, kind, note, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            DAILY_REWARD_CREDITS,
            "SUNGEUM_WALK_DAILY_WINNER",
            f"순금이 산책시키기 {play_date} 일일 1등 ({score}개)",
            now,
        ))
    conn.commit()
    conn.close()


def start_game(user_id):
    _award_unsettled_days()
    if not user_id:
        return None
    token = secrets.token_urlsafe(32)
    conn = _connect()
    cursor = conn.cursor()
    cutoff = (_now_utc() - timedelta(days=2)).isoformat()
    cursor.execute("DELETE FROM sungeum_walk_sessions WHERE started_at < ?", (cutoff,))
    cursor.execute("""
        INSERT INTO sungeum_walk_sessions (token, user_id, started_at)
        VALUES (?, ?, ?)
    """, (token, int(user_id), _now_utc().isoformat()))
    conn.commit()
    conn.close()
    return token


def submit_score(user_id, token, score):
    _award_unsettled_days()
    score = int(score)
    if score < 0 or score > 250:
        raise ValueError("invalid_score")
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")
    cursor.execute("""
        SELECT started_at, submitted_at
        FROM sungeum_walk_sessions
        WHERE token = ? AND user_id = ?
    """, (str(token or ""), int(user_id)))
    game = cursor.fetchone()
    if not game or game[1]:
        conn.rollback()
        conn.close()
        raise ValueError("invalid_session")
    started_at = datetime.fromisoformat(game[0])
    now_utc = _now_utc()
    elapsed = max(0.0, (now_utc - started_at).total_seconds())
    max_reasonable_score = int(elapsed / 0.35) + 3
    if elapsed < 1.0 or elapsed > 1800 or score > max_reasonable_score:
        conn.rollback()
        conn.close()
        raise ValueError("invalid_play")
    now_text = now_utc.isoformat()
    cursor.execute("""
        UPDATE sungeum_walk_sessions
        SET submitted_at = ?, score = ?
        WHERE token = ?
    """, (now_text, score, token))
    play_date = _kst_date(now_utc)
    cursor.execute("""
        INSERT INTO sungeum_walk_scores
            (play_date, user_id, score, achieved_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(play_date, user_id) DO UPDATE SET
            score = excluded.score,
            achieved_at = excluded.achieved_at
        WHERE excluded.score > sungeum_walk_scores.score
    """, (play_date, int(user_id), score, now_text))
    conn.commit()
    conn.close()
    return leaderboard(user_id)


def _masked_name(name):
    name = (name or "플레이어").strip()
    if len(name) <= 1:
        return name + "*"
    return name[0] + "*" * min(3, len(name) - 1)


def leaderboard(user_id=None, limit=5):
    _award_unsettled_days()
    play_date = _kst_date()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.user_id, s.score, s.achieved_at, u.username
        FROM sungeum_walk_scores s
        JOIN users u ON u.id = s.user_id
        WHERE s.play_date = ?
        ORDER BY s.score DESC, s.achieved_at ASC
        LIMIT ?
    """, (play_date, int(limit)))
    rows = cursor.fetchall()
    ranking = [
        {"rank": index + 1, "name": _masked_name(row[3]), "score": int(row[1])}
        for index, row in enumerate(rows)
    ]
    my_best = 0
    my_rank = None
    if user_id:
        cursor.execute("""
            SELECT score, achieved_at FROM sungeum_walk_scores
            WHERE play_date = ? AND user_id = ?
        """, (play_date, int(user_id)))
        mine = cursor.fetchone()
        if mine:
            my_best = int(mine[0])
            cursor.execute("""
                SELECT COUNT(*) + 1
                FROM sungeum_walk_scores
                WHERE play_date = ? AND (
                    score > ? OR (score = ? AND achieved_at < ?)
                )
            """, (play_date, my_best, my_best, mine[1]))
            my_rank = int(cursor.fetchone()[0])
    conn.close()
    return {
        "date": play_date,
        "reward": DAILY_REWARD_CREDITS,
        "ranking": ranking,
        "my_best": my_best,
        "my_rank": my_rank,
    }
