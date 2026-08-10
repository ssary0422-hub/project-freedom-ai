import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "project.db"


def _connect():
    return sqlite3.connect(str(DB_PATH))


def init_db():
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT,
            company TEXT,
            style TEXT,
            result TEXT,
            image_url TEXT
        )
    """)

    # 기존 DB를 깨뜨리지 않고 필요한 컬럼만 자동 추가
    cursor.execute("PRAGMA table_info(history)")
    columns = {
        column[1]
        for column in cursor.fetchall()
    }

    migrations = {
        "image_url": "TEXT",
        "content_type": "TEXT DEFAULT 'general'",
        "package_id": "TEXT",
        "brand_profile_id": "INTEGER",
        "created_at": "TEXT"
    }

    for column_name, column_type in migrations.items():
        if column_name not in columns:
            cursor.execute(
                f"""
                ALTER TABLE history
                ADD COLUMN {column_name} {column_type}
                """
            )

    # 기존 데이터 중 생성일이 비어 있으면 현재 시각으로 채움
    cursor.execute("""
        UPDATE history
        SET created_at = ?
        WHERE created_at IS NULL
           OR created_at = ''
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    conn.commit()
    conn.close()


def save_history(
    business,
    company,
    style,
    result,
    image_url="",
    content_type="general",
    package_id=None,
    brand_profile_id=None
):
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
        INSERT INTO history (
            business,
            company,
            style,
            result,
            image_url,
            content_type,
            package_id,
            brand_profile_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        business,
        company,
        style,
        result,
        image_url,
        content_type,
        package_id,
        brand_profile_id,
        created_at
    ))

    conn.commit()

    history_id = cursor.lastrowid

    conn.close()

    return history_id


def get_history():
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            business,
            company,
            style,
            result,
            image_url
        FROM history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_brand_history(
    brand_profile_id,
    company=None
):
    """
    브랜드별 히스토리.

    새 데이터는 brand_profile_id로 정확히 조회합니다.
    이전 데이터는 company 값이 일치하는 광고/SNS 기록을 보조적으로 포함합니다.
    """
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    if company:
        cursor.execute("""
            SELECT
                id,
                business,
                company,
                style,
                result,
                image_url,
                content_type,
                package_id,
                brand_profile_id,
                created_at
            FROM history
            WHERE brand_profile_id = ?
               OR (
                    brand_profile_id IS NULL
                    AND company = ?
               )
            ORDER BY
                created_at DESC,
                id DESC
        """, (
            brand_profile_id,
            company
        ))

    else:
        cursor.execute("""
            SELECT
                id,
                business,
                company,
                style,
                result,
                image_url,
                content_type,
                package_id,
                brand_profile_id,
                created_at
            FROM history
            WHERE brand_profile_id = ?
            ORDER BY
                created_at DESC,
                id DESC
        """, (
            brand_profile_id,
        ))

    rows = cursor.fetchall()

    conn.close()

    return rows


def delete_history_by_id(history_id):
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM history WHERE id = ?",
        (history_id,)
    )

    conn.commit()
    conn.close()
