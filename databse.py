"""
Simple SQLite persistence layer for the Job Hunter app.

Tables:
- users:    login accounts (email + salted/hashed password)
- resumes:  uploaded resumes, tied to a user
- analyses: saved AI job-match results, tied to a resume
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "job_hunter.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist. Safe to call every app start."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            resume_text TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (resume_id) REFERENCES resumes (id)
        )
    """)

    # "kind" distinguishes fit-score analyses from improvement suggestions
    # and cover letters. Added via ALTER so existing databases created
    # before this feature still work without deleting job_hunter.db.
    try:
        cur.execute("ALTER TABLE analyses ADD COLUMN kind TEXT NOT NULL DEFAULT 'fit_analysis'")
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.commit()
    conn.close()


# ---------------------------------------------------------------- auth ----


def hash_password(password, salt=None):
    """Salt + SHA-256 hash a password. Generates a new salt if none given."""
    if salt is None:
        salt = os.urandom(16).hex()
    pw_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return pw_hash, salt


def create_user(email, password):
    email = email.strip().lower()
    conn = get_connection()
    cur = conn.cursor()
    pw_hash, salt = hash_password(password)
    try:
        cur.execute(
            "INSERT INTO users (email, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
            (email, pw_hash, salt, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "That email is already registered."
    finally:
        conn.close()


def verify_user(email, password):
    """Returns the user row (as a dict) if credentials are valid, else None."""
    email = email.strip().lower()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    pw_hash, _ = hash_password(password, row["salt"])
    if pw_hash == row["password_hash"]:
        return dict(row)
    return None


# ------------------------------------------------------------- resumes ----


def save_resume(user_id, filename, resume_text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO resumes (user_id, filename, resume_text, uploaded_at) VALUES (?, ?, ?, ?)",
        (user_id, filename, resume_text, datetime.utcnow().isoformat()),
    )
    conn.commit()
    resume_id = cur.lastrowid
    conn.close()
    return resume_id


def get_user_resumes(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_resume(resume_id, user_id):
    """
    Delete a resume and its analyses, scoped to user_id so one user can't
    delete another's data by guessing an id. Returns True if a row was
    actually deleted.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM analyses WHERE resume_id = ?", (resume_id,))
    cur.execute("DELETE FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ------------------------------------------------------------ analyses ----


def save_analysis(resume_id, job_title, result, kind="fit_analysis"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO analyses (resume_id, job_title, result, created_at, kind) VALUES (?, ?, ?, ?, ?)",
        (resume_id, job_title, result, datetime.utcnow().isoformat(), kind),
    )
    conn.commit()
    conn.close()


def get_analyses_for_resume(resume_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM analyses WHERE resume_id = ? ORDER BY created_at DESC",
        (resume_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_analyses_for_user(user_id):
    """
    All analyses across every resume this user owns, newest first. Used
    for the dashboard (score history chart, summary stats) rather than
    the per-resume history view.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT analyses.*, resumes.filename AS resume_filename
        FROM analyses
        JOIN resumes ON analyses.resume_id = resumes.id
        WHERE resumes.user_id = ?
        ORDER BY analyses.created_at DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]