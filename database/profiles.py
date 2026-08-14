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




def _table_columns(cursor, table_name):
    if USE_POSTGRES:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = ?
            """,
            (table_name,),
        )
        return {row[0] for row in cursor.fetchall()}

    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}

def init_profiles_table():
    conn = _connect()
    cursor = conn.cursor()
    id_column = "BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS brand_profiles (
            id {id_column},
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

    columns = _table_columns(cursor, "brand_profiles")

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

    insert_sql = """
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
    """
    if USE_POSTGRES:
        insert_sql += " RETURNING id"

    cursor.execute(insert_sql, (
        business,
        company,
        style,
        image_style,
        sns_platform,
        blog_length,
        ads_count,
        user_id,
    ))

    if USE_POSTGRES:
        profile_id = cursor.fetchone()[0]
    else:
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


def count_profiles(user_id):
    init_profiles_table()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM brand_profiles
        WHERE user_id = ?
    """, (
        user_id,
    ))

    count = cursor.fetchone()[0]
    conn.close()

    return count
