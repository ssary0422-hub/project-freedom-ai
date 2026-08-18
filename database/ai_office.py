import json
from datetime import datetime

from database.db import USE_POSTGRES, _connect


def init_ai_office_table():
    conn = _connect()
    cursor = conn.cursor()
    id_column = "BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ai_office_tasks (
            id {id_column},
            user_id INTEGER NOT NULL,
            objective TEXT NOT NULL,
            context TEXT,
            departments TEXT NOT NULL,
            executive_summary TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'REVIEW',
            created_at TEXT NOT NULL,
            approved_at TEXT
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ai_office_tasks_user_id
        ON ai_office_tasks (user_id)
    """)
    conn.commit()
    conn.close()


def save_ai_office_task(user_id, objective, context, result):
    init_ai_office_table()
    conn = _connect()
    cursor = conn.cursor()
    sql = """
        INSERT INTO ai_office_tasks (
            user_id, objective, context, departments,
            executive_summary, status, created_at
        ) VALUES (?, ?, ?, ?, ?, 'REVIEW', ?)
    """
    if USE_POSTGRES:
        sql += " RETURNING id"
    cursor.execute(sql, (
        user_id,
        objective,
        context,
        json.dumps(result["departments"], ensure_ascii=False),
        result["executive_summary"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))
    task_id = cursor.fetchone()[0] if USE_POSTGRES else cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def list_ai_office_tasks(user_id, limit=20):
    init_ai_office_table()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, objective, context, departments, executive_summary,
               status, created_at, approved_at
        FROM ai_office_tasks
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, int(limit)))
    tasks = []
    for row in cursor.fetchall():
        tasks.append({
            "id": row[0],
            "objective": row[1],
            "context": row[2] or "",
            "departments": json.loads(row[3]),
            "executive_summary": row[4],
            "status": row[5],
            "created_at": row[6],
            "approved_at": row[7],
        })
    conn.close()
    return tasks


def approve_ai_office_task(task_id, user_id):
    init_ai_office_table()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ai_office_tasks
        SET status = 'APPROVED', approved_at = ?
        WHERE id = ? AND user_id = ? AND status = 'REVIEW'
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        task_id,
        user_id,
    ))
    changed = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return changed
