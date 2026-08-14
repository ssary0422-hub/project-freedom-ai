import os
import sqlite3
from pathlib import Path
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None
    DictCursor = None

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "project.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)


class _PostgresCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        # 기존 SQLite 쿼리의 ? placeholder를 PostgreSQL 형식으로 변환
        sql = sql.replace("?", "%s")
        # SQLite 전용 트랜잭션 문법을 PostgreSQL용으로 변환
        if sql.strip().upper() == "BEGIN IMMEDIATE":
            sql = "BEGIN"
        self._cursor.execute(sql, params)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class _PostgresConnection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _PostgresCursor(self._conn.cursor(cursor_factory=DictCursor))

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()


def _connect():
    if USE_POSTGRES:
        if psycopg2 is None:
            raise RuntimeError(
                "DATABASE_URL이 설정되어 있지만 psycopg2가 설치되지 않았습니다."
            )
        return _PostgresConnection(psycopg2.connect(DATABASE_URL))

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_users_table():
    conn = _connect()
    cursor = conn.cursor()

    id_column = "BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {id_column},
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            plan TEXT NOT NULL DEFAULT 'FREE',
            is_admin INTEGER NOT NULL DEFAULT 0,
            trial_eligible INTEGER NOT NULL DEFAULT 0,
            trial_reason TEXT NOT NULL DEFAULT ''
        )
    """)

    # 기존 SQLite DB에 누락된 컬럼이 있으면 보강합니다.
    # PostgreSQL 신규 테이블은 위 CREATE TABLE에서 모든 컬럼을 생성합니다.
    if not USE_POSTGRES:
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

        if "plan" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN plan TEXT NOT NULL DEFAULT 'FREE'")
        if "is_admin" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        if "trial_eligible" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_eligible INTEGER NOT NULL DEFAULT 0")
        if "trial_reason" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_reason TEXT NOT NULL DEFAULT ''")

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS package_usage (
            id {id_column},
            user_id INTEGER NOT NULL,
            used_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ai_credit_usage (
            id {id_column},
            user_id INTEGER NOT NULL,
            usage_type TEXT NOT NULL,
            credits INTEGER NOT NULL,
            used_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_credit_wallet (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ai_credit_transactions (
            id {id_column},
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            kind TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS free_trial_claims (
            id {id_column},
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            ip_hash TEXT,
            device_hash TEXT,
            granted INTEGER NOT NULL DEFAULT 0,
            reason TEXT NOT NULL DEFAULT '',
            claimed_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_free_trial_ip_hash
        ON free_trial_claims (ip_hash)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_free_trial_device_hash
        ON free_trial_claims (device_hash)
    """)

    cursor.execute("""
        INSERT INTO system_settings (setting_key, setting_value)
        VALUES ('ai_enabled', '1')
        ON CONFLICT(setting_key) DO NOTHING
    """)

    conn.commit()
    conn.close()

def create_user(email, username, password, trial_eligible=False, trial_reason=''):
    init_users_table()

    email = (email or "").strip().lower()
    username = (username or "").strip()

    password_hash = generate_password_hash(
        password
    )

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = _connect()
    cursor = conn.cursor()

    try:
        insert_sql = """
            INSERT INTO users (
                email,
                username,
                password_hash,
                created_at,
                trial_eligible,
                trial_reason
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """
        if USE_POSTGRES:
            insert_sql += " RETURNING id"

        cursor.execute(insert_sql, (
            email,
            username,
            password_hash,
            created_at,
            1 if trial_eligible else 0,
            str(trial_reason or ""),
        ))

        if USE_POSTGRES:
            user_id = cursor.fetchone()["id"]
        else:
            user_id = cursor.lastrowid

        conn.commit()
        return user_id

    except (sqlite3.IntegrityError, psycopg2.IntegrityError if psycopg2 else sqlite3.IntegrityError):
        conn.rollback()
        return None

    finally:
        conn.close()


def get_user_by_email(email):
    init_users_table()

    email = (email or "").strip().lower()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            email,
            username,
            password_hash,
            created_at,
            plan,
            is_admin,
            trial_eligible,
            trial_reason
        FROM users
        WHERE email = ?
    """, (
        email,
    ))

    row = cursor.fetchone()
    conn.close()

    return row


def get_user_by_id(user_id):
    init_users_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            email,
            username,
            created_at,
            plan,
            is_admin,
            trial_eligible,
            trial_reason
        FROM users
        WHERE id = ?
    """, (
        user_id,
    ))

    row = cursor.fetchone()
    conn.close()

    return row


def verify_user(email, password):
    user = get_user_by_email(
        email
    )

    if not user:
        return None

    if not check_password_hash(
        user["password_hash"],
        password
    ):
        return None

    return user



def has_claimed_free_trial_by_ip(ip_hash):
    init_users_table()

    if not ip_hash:
        return False

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM free_trial_claims
        WHERE ip_hash = ? AND granted = 1
        LIMIT 1
        """,
        (ip_hash,)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None


def has_claimed_free_trial_by_device(device_hash):
    init_users_table()

    if not device_hash:
        return False

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM free_trial_claims
        WHERE device_hash = ? AND granted = 1
        LIMIT 1
        """,
        (device_hash,)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None


def record_free_trial_claim(
    user_id,
    email,
    ip_hash="",
    device_hash="",
    granted=False,
    reason=""
):
    init_users_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO free_trial_claims (
            user_id,
            email,
            ip_hash,
            device_hash,
            granted,
            reason,
            claimed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            (email or "").strip().lower(),
            ip_hash or "",
            device_hash or "",
            1 if granted else 0,
            str(reason or ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    )

    conn.commit()
    conn.close()


def get_free_trial_status(user_id):
    user = get_user_by_id(user_id)

    if not user:
        return {
            "eligible": False,
            "reason": "user_not_found",
        }

    return {
        "eligible": bool(user["trial_eligible"]),
        "reason": user["trial_reason"] or "",
    }

CREDIT_LIMITS = {"FREE": 6, "PRO": 100}
CREDIT_COSTS = {"ADS_TEXT": 1, "ADS_IMAGE": 3, "BLOG_TEXT": 1, "BLOG_IMAGE": 3, "SNS_TEXT": 1, "SNS_IMAGE": 3, "PACKAGE_TEXT": 3, "PACKAGE_IMAGE": 7}


def get_monthly_package_usage(user_id):
    init_users_table()
    month_key = datetime.now().strftime("%Y-%m")
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM package_usage
        WHERE user_id = ? AND substr(used_at, 1, 7) = ?
    """, (user_id, month_key))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_monthly_credit_usage(user_id):
    init_users_table()
    month_key = datetime.now().strftime("%Y-%m")
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(credits), 0)
        FROM ai_credit_usage
        WHERE user_id = ? AND substr(used_at, 1, 7) = ?
    """, (user_id, month_key))
    used = int(cursor.fetchone()[0] or 0)
    conn.close()
    return used



def get_bonus_credit_balance(user_id):
    """구매/관리자 지급 등 월이 바뀌어도 유지되는 추가 크레딧."""
    init_users_table()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT balance FROM ai_credit_wallet WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return int(row["balance"] if row else 0)


def add_bonus_credits(user_id, amount, kind="ADMIN_GRANT", note=""):
    """추가 크레딧을 지급합니다. 실제 결제 성공 후에도 이 함수를 호출하면 됩니다."""
    init_users_table()
    amount = int(amount)

    if amount <= 0:
        raise ValueError("지급 크레딧은 1 이상이어야 합니다.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")

    cursor.execute(
        """
        INSERT INTO ai_credit_wallet (user_id, balance, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            balance = ai_credit_wallet.balance + excluded.balance,
            updated_at = excluded.updated_at
        """,
        (user_id, amount, now)
    )

    cursor.execute(
        """
        INSERT INTO ai_credit_transactions (
            user_id, amount, kind, note, created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, amount, str(kind), str(note or ""), now)
    )

    conn.commit()
    conn.close()
    return get_bonus_credit_balance(user_id)


def get_credit_transactions(user_id, limit=30):
    init_users_table()
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, amount, kind, note, created_at
        FROM ai_credit_transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, int(limit))
    )

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_plan_status(user_id, required_credits=1):
    user = get_user_by_id(user_id)
    plan = (user["plan"] if user and user["plan"] else "FREE").upper()

    if plan not in CREDIT_LIMITS:
        plan = "FREE"

    used = get_monthly_credit_usage(user_id)

    if plan == "FREE":
        trial_status = get_free_trial_status(user_id)
        limit = CREDIT_LIMITS[plan] if trial_status["eligible"] else 0
    else:
        limit = CREDIT_LIMITS[plan]

    base_remaining = max(0, limit - used)
    bonus_balance = get_bonus_credit_balance(user_id)
    remaining = base_remaining + bonus_balance
    required = max(0, int(required_credits or 0))

    return {
        "plan": plan,
        "used": used,
        "limit": limit,
        "base_remaining": base_remaining,
        "bonus_balance": bonus_balance,
        "remaining": remaining,
        "can_generate": remaining >= required,
        "percent": min(100, int((min(used, limit) / limit) * 100)) if limit else 0,
        "required": required,
    }

def record_ai_credit_usage(user_id, usage_type, credits=None):
    """
    월 기본 크레딧을 먼저 사용하고, 부족한 부분만 충전 크레딧에서 차감합니다.
    """
    init_users_table()
    usage_type = (usage_type or "OTHER").strip().upper()

    if credits is None:
        credits = CREDIT_COSTS.get(usage_type, 1)

    credits = int(credits)

    if credits <= 0:
        return

    user = get_user_by_id(user_id)
    plan = (user["plan"] if user and user["plan"] else "FREE").upper()

    if plan not in CREDIT_LIMITS:
        plan = "FREE"

    limit = CREDIT_LIMITS[plan]
    month_key = datetime.now().strftime("%Y-%m")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")

    cursor.execute(
        """
        SELECT COALESCE(SUM(credits), 0)
        FROM ai_credit_usage
        WHERE user_id = ?
          AND substr(used_at, 1, 7) = ?
        """,
        (user_id, month_key)
    )
    used_before = int(cursor.fetchone()[0] or 0)
    base_available = max(0, limit - used_before)
    bonus_needed = max(0, credits - base_available)

    cursor.execute(
        "SELECT balance FROM ai_credit_wallet WHERE user_id = ?",
        (user_id,)
    )
    wallet_row = cursor.fetchone()
    wallet_balance = int(wallet_row["balance"] if wallet_row else 0)

    if bonus_needed > wallet_balance:
        conn.rollback()
        conn.close()
        raise ValueError("AI 크레딧이 부족합니다.")

    cursor.execute(
        """
        INSERT INTO ai_credit_usage (
            user_id, usage_type, credits, used_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (user_id, usage_type, credits, now)
    )

    if bonus_needed > 0:
        cursor.execute(
            """
            UPDATE ai_credit_wallet
            SET balance = balance - ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (bonus_needed, now, user_id)
        )

        cursor.execute(
            """
            INSERT INTO ai_credit_transactions (
                user_id, amount, kind, note, created_at
            )
            VALUES (?, ?, 'USAGE', ?, ?)
            """,
            (
                user_id,
                -bonus_needed,
                f"{usage_type} 생성에 충전 크레딧 사용",
                now,
            )
        )

    conn.commit()
    conn.close()

def record_package_usage(user_id, credits=7):
    """패키지 통계 + 실제 크레딧 차감."""
    init_users_table()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO package_usage (user_id, used_at) VALUES (?, ?)",
        (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    record_ai_credit_usage(user_id, "PACKAGE", int(credits))


def set_user_plan(user_id, plan):
    init_users_table()
    plan = (plan or "FREE").upper()
    if plan not in CREDIT_LIMITS:
        raise ValueError("plan은 FREE 또는 PRO만 가능합니다.")

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET plan = ? WHERE id = ?",
        (plan, user_id)
    )
    conn.commit()
    conn.close()


def is_user_admin(user_id):
    user = get_user_by_id(user_id)

    if not user:
        return False

    return bool(user["is_admin"])


def set_user_admin_by_email(email, is_admin=True):
    """
    ADMIN_EMAIL 환경변수와 함께 사용할 수 있는 관리자 지정 helper.
    """
    init_users_table()

    email = (email or "").strip().lower()

    if not email:
        return False

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET is_admin = ?
        WHERE lower(email) = ?
        """,
        (
            1 if is_admin else 0,
            email,
        )
    )

    changed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return changed


def get_ai_enabled():
    init_users_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT setting_value
        FROM system_settings
        WHERE setting_key = 'ai_enabled'
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return True

    return str(row["setting_value"]) == "1"


def set_ai_enabled(enabled):
    init_users_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO system_settings (
            setting_key,
            setting_value
        )
        VALUES ('ai_enabled', ?)
        ON CONFLICT(setting_key)
        DO UPDATE SET setting_value = excluded.setting_value
    """, (
        "1" if enabled else "0",
    ))

    conn.commit()
    conn.close()


def get_admin_stats():
    init_users_table()

    month_key = datetime.now().strftime("%Y-%m")

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE upper(plan) = 'FREE'"
    )
    free_users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE upper(plan) = 'PRO'"
    )
    pro_users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM package_usage
        WHERE substr(used_at, 1, 7) = ?
    """, (
        month_key,
    ))
    monthly_packages = cursor.fetchone()[0]

    conn.close()

    return {
        "total_users": total_users,
        "free_users": free_users,
        "pro_users": pro_users,
        "monthly_packages": monthly_packages,
        "ai_enabled": get_ai_enabled(),
    }


def get_admin_users(limit=50):
    init_users_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            email,
            username,
            plan,
            is_admin,
            created_at
        FROM users
        ORDER BY id DESC
        LIMIT ?
    """, (
        int(limit),
    ))

    rows = cursor.fetchall()
    conn.close()

    return rows
