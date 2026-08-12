import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "project.db"


def _connect():
    return sqlite3.connect(str(DB_PATH))


def init_profiles_table():
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brand_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT NOT NULL,
            company TEXT NOT NULL,
            style TEXT NOT NULL,
            image_style TEXT DEFAULT '고급스러운 실사',
            sns_platform TEXT DEFAULT '인스타그램',
            blog_length TEXT DEFAULT '2000자',
            ads_count INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER
        )
    """)

    cursor.execute(
        "PRAGMA table_info(brand_profiles)"
    )

    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if "user_id" not in columns:
        cursor.execute("""
            ALTER TABLE brand_profiles
            ADD COLUMN user_id INTEGER
        """)

    conn.commit()
    conn.close()


def get_profiles(user_id):
    init_profiles_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            business,
            company,
            style,
            image_style,
            sns_platform,
            blog_length,
            ads_count
        FROM brand_profiles
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        user_id,
    ))

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_profile(profile_id, user_id):
    init_profiles_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            business,
            company,
            style,
            image_style,
            sns_platform,
            blog_length,
            ads_count
        FROM brand_profiles
        WHERE id = ?
          AND user_id = ?
    """, (
        profile_id,
        user_id,
    ))

    row = cursor.fetchone()
    conn.close()

    return row


def save_profile(
    business,
    company,
    style,
    image_style="고급스러운 실사",
    sns_platform="인스타그램",
    blog_length="2000자",
    ads_count=5,
    user_id=None
):
    init_profiles_table()

    if user_id is None:
        raise ValueError(
            "브랜드 프로필 저장에는 user_id가 필요합니다."
        )

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO brand_profiles (
            business,
            company,
            style,
            image_style,
            sns_platform,
            blog_length,
            ads_count,
            user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        business,
        company,
        style,
        image_style,
        sns_platform,
        blog_length,
        ads_count,
        user_id,
    ))

    profile_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return profile_id


def delete_profile(profile_id, user_id):
    init_profiles_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM brand_profiles
        WHERE id = ?
          AND user_id = ?
    """, (
        profile_id,
        user_id,
    ))

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted_count
