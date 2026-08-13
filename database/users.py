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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS package_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            used_at TEXT NOT NULL
        )
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
            plan
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
            plan
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


PLAN_LIMITS = {
    "FREE": 3,
    "PRO": 50,
}


def get_monthly_package_usage(user_id):
    init_users_table()
    month_key = datetime.now().strftime("%Y-%m")

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM package_usage
        WHERE user_id = ?
          AND substr(used_at, 1, 7) = ?
        """,
        (user_id, month_key)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_plan_status(user_id):
    user = get_user_by_id(user_id)
    plan = (user["plan"] if user and user["plan"] else "FREE").upper()
    if plan not in PLAN_LIMITS:
        plan = "FREE"

    used = get_monthly_package_usage(user_id)
    limit = PLAN_LIMITS[plan]

    return {
        "plan": plan,
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
        "can_generate": used < limit,
        "percent": min(100, int((used / limit) * 100)) if limit else 0,
    }


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


def set_user_plan(user_id, plan):
    init_users_table()
    plan = (plan or "FREE").upper()
    if plan not in PLAN_LIMITS:
        raise ValueError("plan은 FREE 또는 PRO만 가능합니다.")

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET plan = ? WHERE id = ?",
        (plan, user_id)
    )
    conn.commit()
    conn.close()
