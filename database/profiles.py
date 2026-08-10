import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "project.db"


def init_profiles_table():
    conn = sqlite3.connect(str(DB_PATH))
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_profiles():
    init_profiles_table()

    conn = sqlite3.connect(str(DB_PATH))
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
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_profile(profile_id):
    init_profiles_table()

    conn = sqlite3.connect(str(DB_PATH))
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
    """, (
        profile_id,
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
    ads_count=5
):
    init_profiles_table()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO brand_profiles (
            business,
            company,
            style,
            image_style,
            sns_platform,
            blog_length,
            ads_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        business,
        company,
        style,
        image_style,
        sns_platform,
        blog_length,
        ads_count
    ))

    conn.commit()
    conn.close()


def delete_profile(profile_id):
    init_profiles_table()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM brand_profiles WHERE id = ?",
        (profile_id,)
    )

    conn.commit()
    conn.close()
