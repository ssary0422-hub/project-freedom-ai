import sqlite3
from pathlib import Path
from datetime import datetime

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "project.db"


def _connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_users_table():
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # 기존 users 테이블에도 안전하게 요금제 컬럼 추가
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}

    if "plan" not in columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN plan TEXT NOT NULL DEFAULT 'FREE'"
        )

    if "is_admin" not in columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS package_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_credit_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            usage_type TEXT NOT NULL,
            credits INTEGER NOT NULL,
            used_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO system_settings (
            setting_key,
            setting_value
        )
        VALUES ('ai_enabled', '1')
    """)

    conn.commit()
    conn.close()


def create_user(email, username, password):
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
        cursor.execute("""
            INSERT INTO users (
                email,
                username,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            email,
            username,
            password_hash,
            created_at,
        ))

        user_id = cursor.lastrowid
        conn.commit()

        return user_id

    except sqlite3.IntegrityError:
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
            is_admin
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
            is_admin
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


CREDIT_LIMITS = {"FREE": 6, "PRO": 100}
CREDIT_COSTS = {"ADS": 2, "BLOG": 2, "SNS": 2, "PACKAGE": 6}


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


def get_plan_status(user_id, required_credits=1):
    user = get_user_by_id(user_id)
    plan = (user["plan"] if user and user["plan"] else "FREE").upper()
    if plan not in CREDIT_LIMITS:
        plan = "FREE"
    used = get_monthly_credit_usage(user_id)
    limit = CREDIT_LIMITS[plan]
    remaining = max(0, limit - used)
    required = max(0, int(required_credits or 0))
    return {
        "plan": plan,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "can_generate": remaining >= required,
        "percent": min(100, int((used / limit) * 100)) if limit else 0,
        "required": required,
    }


def record_ai_credit_usage(user_id, usage_type, credits=None):
    init_users_table()
    usage_type = (usage_type or "OTHER").strip().upper()
    if credits is None:
        credits = CREDIT_COSTS.get(usage_type, 1)
    credits = int(credits)
    if credits <= 0:
        return
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ai_credit_usage (user_id, usage_type, credits, used_at)
        VALUES (?, ?, ?, ?)
    """, (
        user_id, usage_type, credits,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()



def record_package_usage(user_id):
    init_users_table()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO package_usage (user_id, used_at) VALUES (?, ?)",
        (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    record_ai_credit_usage(user_id, "PACKAGE", CREDIT_COSTS["PACKAGE"])


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
