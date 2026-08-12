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
            created_at
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
            created_at
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
