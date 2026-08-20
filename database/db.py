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

def init_db():
    conn = _connect()
    cursor = conn.cursor()
    id_column = "BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

    # 대시보드에서도 사용하는 브랜드 프로필 테이블을 항상 보장합니다.
    # 새 서버/새 SQLite DB에서도 /dashboard가 먼저 열려도 오류가 나지 않습니다.
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

    brand_columns = _table_columns(cursor, "brand_profiles")

    brand_migrations = {
        "image_style": "TEXT DEFAULT '고급스러운 실사'",
        "sns_platform": "TEXT DEFAULT '인스타그램'",
        "blog_length": "TEXT DEFAULT '2000자'",
        "ads_count": "INTEGER DEFAULT 5",
        "created_at": "TIMESTAMP",
        "user_id": "INTEGER",
    }

    for column_name, column_type in brand_migrations.items():
        if column_name not in brand_columns:
            cursor.execute(
                f"""
                ALTER TABLE brand_profiles
                ADD COLUMN {column_name} {column_type}
                """
            )

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_brand_profiles_user_id
        ON brand_profiles (user_id)
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS history (
            id {id_column},
            business TEXT,
            company TEXT,
            style TEXT,
            result TEXT,
            image_url TEXT
        )
    """)


    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS payments (
            id {id_column},
            user_id INTEGER NOT NULL,
            order_id TEXT NOT NULL UNIQUE,
            payment_key TEXT,
            product_code TEXT NOT NULL,
            amount INTEGER NOT NULL,
            credits INTEGER NOT NULL,
            status TEXT NOT NULL,
            provider TEXT NOT NULL DEFAULT 'TEST',
            created_at TEXT NOT NULL,
            paid_at TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_user_id
        ON payments (user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_status
        ON payments (status)
    """)

    # 기존 DB를 깨뜨리지 않고 필요한 컬럼만 자동 추가
    columns = _table_columns(cursor, "history")

    migrations = {
        "image_url": "TEXT",
        "content_type": "TEXT DEFAULT 'general'",
        "package_id": "TEXT",
        "brand_profile_id": "INTEGER",
        "created_at": "TEXT",
        "version": "INTEGER DEFAULT 1",
        "is_current": "INTEGER DEFAULT 1",
        "user_id": "INTEGER"
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

    cursor.execute("""
        UPDATE history
        SET version = 1
        WHERE version IS NULL
           OR version < 1
    """)

    cursor.execute("""
        UPDATE history
        SET is_current = 1
        WHERE is_current IS NULL
    """)

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
    brand_profile_id=None,
    user_id=None
):
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    insert_sql = """
        INSERT INTO history (
            business,
            company,
            style,
            result,
            image_url,
            content_type,
            package_id,
            brand_profile_id,
            created_at,
            user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    if USE_POSTGRES:
        insert_sql += " RETURNING id"

    cursor.execute(insert_sql, (
        business,
        company,
        style,
        result,
        image_url,
        content_type,
        package_id,
        brand_profile_id,
        created_at,
        user_id
    ))

    conn.commit()

    if USE_POSTGRES:
        history_id = cursor.fetchone()[0]
    else:
        history_id = cursor.lastrowid

    conn.close()

    return history_id


def get_history(user_id):
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
            image_url,
            COALESCE(content_type, 'general')
        FROM history
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        user_id,
    ))

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_brand_history(
    brand_profile_id,
    user_id,
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
            WHERE (
                    brand_profile_id = ?
                    OR (
                        brand_profile_id IS NULL
                        AND company = ?
                    )
                  )
              AND user_id = ?
              AND COALESCE(is_current, 1) = 1
            ORDER BY
                created_at DESC,
                id DESC
        """, (
            brand_profile_id,
            company,
            user_id
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
              AND user_id = ?
              AND COALESCE(is_current, 1) = 1
            ORDER BY
                created_at DESC,
                id DESC
        """, (
            brand_profile_id,
            user_id,
        ))

    rows = cursor.fetchall()

    conn.close()

    return rows


def delete_history_by_id(history_id, user_id):
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM history WHERE id = ? AND user_id = ?",
        (history_id, user_id)
    )

    conn.commit()
    conn.close()


def get_package_history(
    package_id,
    brand_profile_id=None,
    current_only=True,
    user_id=None
):
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    filters = [
        "package_id = ?"
    ]

    params = [
        package_id
    ]

    if brand_profile_id is not None:
        filters.append(
            "brand_profile_id = ?"
        )
        params.append(
            brand_profile_id
        )

    if current_only:
        filters.append(
            "COALESCE(is_current, 1) = 1"
        )

    if user_id is not None:
        filters.append(
            "user_id = ?"
        )
        params.append(
            user_id
        )

    where_clause = " AND ".join(
        filters
    )

    cursor.execute(
        f"""
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
            created_at,
            COALESCE(version, 1) AS version,
            COALESCE(is_current, 1) AS is_current
        FROM history
        WHERE {where_clause}
        ORDER BY
            CASE content_type
                WHEN 'ads' THEN 1
                WHEN 'blog' THEN 2
                WHEN 'sns' THEN 3
                ELSE 4
            END,
            version DESC,
            id DESC
        """,
        tuple(params)
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


def save_history_version(
    business,
    company,
    style,
    result,
    image_url,
    content_type,
    package_id,
    brand_profile_id,
    user_id
):
    """
    기존 콘텐츠를 삭제하지 않고 새 버전으로 저장합니다.
    같은 package_id + content_type에서 가장 최신 버전만 is_current=1입니다.
    """
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    insert_sql = """
        SELECT COALESCE(MAX(version), 0)
        FROM history
        WHERE package_id = ?
          AND content_type = ?
          AND brand_profile_id = ?
          AND user_id = ?
    """
    if USE_POSTGRES:
        insert_sql += " RETURNING id"

    cursor.execute(insert_sql, (
        package_id,
        content_type,
        brand_profile_id,
        user_id
    ))

    next_version = (
        cursor.fetchone()[0]
        + 1
    )

    cursor.execute("""
        UPDATE history
        SET is_current = 0
        WHERE package_id = ?
          AND content_type = ?
          AND brand_profile_id = ?
          AND user_id = ?
          AND COALESCE(is_current, 1) = 1
    """, (
        package_id,
        content_type,
        brand_profile_id,
        user_id
    ))

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
            created_at,
            version,
            is_current,
            user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (
        business,
        company,
        style,
        result,
        image_url,
        content_type,
        package_id,
        brand_profile_id,
        created_at,
        next_version,
        user_id
    ))

    if USE_POSTGRES:
        history_id = cursor.fetchone()[0]
    else:
        history_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return history_id, next_version



def delete_package_history(
    package_id,
    brand_profile_id=None,
    user_id=None
):
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    filters = [
        "package_id = ?"
    ]
    params = [
        package_id
    ]

    if brand_profile_id is not None:
        filters.append(
            "brand_profile_id = ?"
        )
        params.append(
            brand_profile_id
        )

    if user_id is not None:
        filters.append(
            "user_id = ?"
        )
        params.append(
            user_id
        )

    where_clause = " AND ".join(
        filters
    )

    cursor.execute(
        f"""
        DELETE FROM history
        WHERE {where_clause}
        """,
        tuple(params)
    )

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted_count


def restore_history_version(
    history_id,
    package_id,
    brand_profile_id,
    content_type,
    user_id
):
    """
    특정 과거 버전을 현재 버전으로 다시 지정합니다.
    데이터는 삭제하지 않고 is_current 값만 전환합니다.
    """
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM history
        WHERE id = ?
          AND package_id = ?
          AND brand_profile_id = ?
          AND content_type = ?
          AND user_id = ?
    """, (
        history_id,
        package_id,
        brand_profile_id,
        content_type,
        user_id
    ))

    target = cursor.fetchone()

    if not target:
        conn.close()
        return False

    cursor.execute("""
        UPDATE history
        SET is_current = 0
        WHERE package_id = ?
          AND brand_profile_id = ?
          AND content_type = ?
          AND user_id = ?
    """, (
        package_id,
        brand_profile_id,
        content_type,
        user_id
    ))

    cursor.execute("""
        UPDATE history
        SET is_current = 1
        WHERE id = ?
          AND user_id = ?
    """, (
        history_id,
        user_id,
    ))

    conn.commit()
    conn.close()

    return True



def get_history_item(history_id, user_id):
    """
    생성 기록 1개를 다운로드용으로 조회합니다.
    """
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
            image_url,
            COALESCE(content_type, 'general')
        FROM history
        WHERE id = ?
          AND user_id = ?
    """, (
        history_id,
        user_id,
    ))

    row = cursor.fetchone()

    conn.close()

    return row


def update_history_image(history_id, user_id, image_url, content_type="sns"):
    """Attach a regenerated image only to the owning user's matching history item."""
    init_db()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE history
        SET image_url = ?
        WHERE id = ?
          AND user_id = ?
          AND COALESCE(content_type, 'general') = ?
        """,
        (image_url, history_id, user_id, content_type),
    )
    updated = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return updated



def create_test_payment(
    user_id,
    order_id,
    product_code,
    amount,
    credits
):
    """
    TEST 결제 완료 기록을 저장합니다.
    order_id UNIQUE 제약으로 같은 주문의 중복 지급을 방지합니다.
    """
    init_db()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = _connect()
    cursor = conn.cursor()

    try:
        insert_sql = """
            INSERT INTO payments (
                user_id,
                order_id,
                payment_key,
                product_code,
                amount,
                credits,
                status,
                provider,
                created_at,
                paid_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'PAID', 'TEST', ?, ?)
            """
        if USE_POSTGRES:
            insert_sql += " RETURNING id"

        cursor.execute(
            insert_sql,
            (
                user_id,
                order_id,
                f"test_{order_id}",
                product_code,
                int(amount),
                int(credits),
                created_at,
                created_at,
            )
        )

        conn.commit()
        if USE_POSTGRES:
            payment_id = cursor.fetchone()[0]
        else:
            payment_id = cursor.lastrowid
        return {
            "ok": True,
            "payment_id": payment_id,
        }

    except (sqlite3.IntegrityError, psycopg2.IntegrityError if psycopg2 else sqlite3.IntegrityError):
        return {
            "ok": False,
            "reason": "duplicate_order",
        }

    finally:
        conn.close()


def get_user_payments(user_id, limit=30):
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            order_id,
            product_code,
            amount,
            credits,
            status,
            provider,
            created_at,
            paid_at
        FROM payments
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            int(limit),
        )
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_payment_by_order_id(order_id):
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            order_id,
            product_code,
            amount,
            credits,
            status,
            provider,
            created_at,
            paid_at
        FROM payments
        WHERE order_id = ?
        LIMIT 1
        """,
        (order_id,)
    )

    row = cursor.fetchone()
    conn.close()
    return row

def get_dashboard_data(user_id):
    """
    로그인 사용자의 대시보드 요약 데이터를 반환합니다.
    브랜드별 최신 생성 이미지를 대표 썸네일로 함께 조회합니다.
    """
    init_db()

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM brand_profiles
        WHERE user_id = ?
    """, (
        user_id,
    ))
    brand_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            bp.id,
            bp.business,
            bp.company,
            bp.style,
            (
                SELECT h.image_url
                FROM history h
                WHERE h.brand_profile_id = bp.id
                  AND h.user_id = bp.user_id
                  AND h.image_url IS NOT NULL
                  AND h.image_url != ''
                  AND COALESCE(h.is_current, 1) = 1
                ORDER BY
                    h.created_at DESC,
                    h.id DESC
                LIMIT 1
            ) AS thumbnail_url
        FROM brand_profiles bp
        WHERE bp.user_id = ?
        ORDER BY bp.id DESC
        LIMIT 3
    """, (
        user_id,
    ))
    recent_brands = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*)
        FROM history
        WHERE user_id = ?
          AND COALESCE(is_current, 1) = 1
    """, (
        user_id,
    ))
    content_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT package_id)
        FROM history
        WHERE user_id = ?
          AND package_id IS NOT NULL
          AND package_id != ''
    """, (
        user_id,
    ))
    package_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            package_id,
            brand_profile_id,
            MAX(company) AS company,
            MAX(business) AS business,
            MAX(created_at) AS created_at,
            COUNT(DISTINCT content_type) AS content_count
        FROM history
        WHERE user_id = ?
          AND package_id IS NOT NULL
          AND package_id != ''
          AND COALESCE(is_current, 1) = 1
        GROUP BY
            package_id,
            brand_profile_id
        ORDER BY
            MAX(created_at) DESC,
            MAX(id) DESC
        LIMIT 5
    """, (
        user_id,
    ))
    recent_packages = cursor.fetchall()

    conn.close()

    return {
        "brand_count": brand_count,
        "package_count": package_count,
        "content_count": content_count,
        "recent_brands": recent_brands,
        "recent_packages": recent_packages,
    }

