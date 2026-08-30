
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "fileorganizer.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            rule_matched TEXT,
            organized_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS file_tags (
            file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (file_id, tag_id)
        )
    """)
    conn.commit()
    conn.close()


def record_file(path: str, filename: str, rule_matched: str | None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO files (path, filename, rule_matched, organized_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            filename=excluded.filename,
            rule_matched=excluded.rule_matched,
            organized_at=excluded.organized_at
    """, (path, filename, rule_matched, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()


def update_file_path(old_path: str, new_path: str, new_filename: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE files SET path=?, filename=? WHERE path=?",
                (new_path, new_filename, old_path))
    conn.commit()
    conn.close()


def add_tag(file_path: str, tag_name: str):
    tag_name = tag_name.strip().lower()
    if not tag_name:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM files WHERE path=?", (file_path,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    file_id = row[0]
    cur.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
    cur.execute("SELECT id FROM tags WHERE name=?", (tag_name,))
    tag_id = cur.fetchone()[0]
    cur.execute("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                (file_id, tag_id))
    conn.commit()
    conn.close()


def remove_tag(file_path: str, tag_name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM file_tags WHERE file_id = (SELECT id FROM files WHERE path=?)
        AND tag_id = (SELECT id FROM tags WHERE name=?)
    """, (file_path, tag_name.strip().lower()))
    conn.commit()
    conn.close()


def get_all_files(search_tag: str | None = None):
    conn = get_conn()
    cur = conn.cursor()
    if search_tag:
        cur.execute("""
            SELECT f.id, f.path, f.filename, f.rule_matched, f.organized_at
            FROM files f
            JOIN file_tags ft ON ft.file_id = f.id
            JOIN tags t ON t.id = ft.tag_id
            WHERE t.name = ?
            ORDER BY f.organized_at DESC
        """, (search_tag.strip().lower(),))
    else:
        cur.execute("""
            SELECT id, path, filename, rule_matched, organized_at
            FROM files ORDER BY organized_at DESC
        """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_tags_for_file(file_path: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.name FROM tags t
        JOIN file_tags ft ON ft.tag_id = t.id
        JOIN files f ON f.id = ft.file_id
        WHERE f.path = ?
        ORDER BY t.name
    """, (file_path,))
    tags = [r[0] for r in cur.fetchall()]
    conn.close()
    return tags


def get_all_tags():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM tags ORDER BY name")
    tags = [r[0] for r in cur.fetchall()]
    conn.close()
    return tags


def delete_file_record(file_path: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM files WHERE path=?", (file_path,))
    conn.commit()
    conn.close()
