import sqlite3


DB_PATH = "project.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
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

    # 예전 DB에 image_url이 없는 경우 자동 추가
    cursor.execute("PRAGMA table_info(history)")
    columns = [column[1] for column in cursor.fetchall()]

    if "image_url" not in columns:
        cursor.execute("""
            ALTER TABLE history
            ADD COLUMN image_url TEXT
        """)

    conn.commit()
    conn.close()


def save_history(
    business,
    company,
    style,
    result,
    image_url=""
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO history (
            business,
            company,
            style,
            result,
            image_url
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        business,
        company,
        style,
        result,
        image_url
    ))

    conn.commit()
    conn.close()


def get_history():
    conn = sqlite3.connect(DB_PATH)
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


def delete_history_by_id(history_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM history WHERE id = ?",
        (history_id,)
    )

    conn.commit()
    conn.close()