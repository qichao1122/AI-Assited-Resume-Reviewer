import os
import sqlite3
import tempfile

import pytest

import databse as db


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    """Point db.DB_PATH at a fresh temp file for every test so tests don't
    touch or depend on the real job_hunter.db."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db()
    yield
    os.remove(path)


def test_create_user_success():
    ok, msg = db.create_user("alice@example.com", "hunter22")
    assert ok is True
    assert "created" in msg.lower()


def test_create_user_duplicate_email_fails():
    db.create_user("alice@example.com", "hunter22")
    ok, msg = db.create_user("alice@example.com", "different")
    assert ok is False
    assert "already registered" in msg.lower()


def test_verify_user_correct_password():
    db.create_user("alice@example.com", "hunter22")
    user = db.verify_user("alice@example.com", "hunter22")
    assert user is not None
    assert user["email"] == "alice@example.com"


def test_verify_user_wrong_password_returns_none():
    db.create_user("alice@example.com", "hunter22")
    assert db.verify_user("alice@example.com", "wrongpass") is None


def test_verify_user_unknown_email_returns_none():
    assert db.verify_user("nobody@example.com", "anything") is None


def test_save_and_get_resume():
    db.create_user("alice@example.com", "hunter22")
    user = db.verify_user("alice@example.com", "hunter22")

    resume_id = db.save_resume(user["id"], "resume.pdf", "Some resume text")
    resumes = db.get_user_resumes(user["id"])

    assert len(resumes) == 1
    assert resumes[0]["id"] == resume_id
    assert resumes[0]["filename"] == "resume.pdf"


def test_save_and_get_analysis():
    db.create_user("alice@example.com", "hunter22")
    user = db.verify_user("alice@example.com", "hunter22")
    resume_id = db.save_resume(user["id"], "resume.pdf", "Some resume text")

    db.save_analysis(resume_id, "Pharmacy Technician", "Score: 65")
    analyses = db.get_analyses_for_resume(resume_id)

    assert len(analyses) == 1
    assert analyses[0]["job_title"] == "Pharmacy Technician"
    assert analyses[0]["result"] == "Score: 65"
    assert analyses[0]["kind"] == "fit_analysis"  # default when not specified


def test_save_analysis_with_explicit_kind():
    db.create_user("alice@example.com", "hunter22")
    user = db.verify_user("alice@example.com", "hunter22")
    resume_id = db.save_resume(user["id"], "resume.pdf", "Some resume text")

    db.save_analysis(resume_id, "Pharmacy Technician", "Dear Hiring Manager...", kind="cover_letter")
    db.save_analysis(resume_id, "Pharmacy Technician", "Add more detail...", kind="improvement_suggestions")

    analyses = db.get_analyses_for_resume(resume_id)
    kinds = {a["kind"] for a in analyses}

    assert kinds == {"cover_letter", "improvement_suggestions"}


def test_init_db_migrates_existing_database_without_kind_column():
    """
    Simulates a database created before the 'kind' column existed, to
    confirm init_db() adds it via ALTER TABLE without losing existing data.
    """
    conn = sqlite3.connect(db.DB_PATH)
    cur = conn.cursor()
    # Drop and recreate analyses table in the old (pre-'kind') shape
    cur.execute("DROP TABLE analyses")
    cur.execute("""
        CREATE TABLE analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute(
        "INSERT INTO analyses (resume_id, job_title, result, created_at) VALUES (?, ?, ?, ?)",
        (1, "Old Job", "Score: 50", "2020-01-01T00:00:00"),
    )
    conn.commit()
    conn.close()

    db.init_db()  # should migrate in place, not wipe existing rows

    analyses = db.get_analyses_for_resume(1)
    assert len(analyses) == 1
    assert analyses[0]["result"] == "Score: 50"
    assert analyses[0]["kind"] == "fit_analysis"  # default applied to pre-existing row


def test_delete_resume_removes_resume_and_its_analyses():
    db.create_user("alice@example.com", "hunter22")
    user = db.verify_user("alice@example.com", "hunter22")
    resume_id = db.save_resume(user["id"], "resume.pdf", "Some resume text")
    db.save_analysis(resume_id, "Job A", "Score: 80")

    deleted = db.delete_resume(resume_id, user["id"])

    assert deleted is True
    assert db.get_user_resumes(user["id"]) == []
    assert db.get_analyses_for_resume(resume_id) == []


def test_delete_resume_returns_false_for_nonexistent_resume():
    db.create_user("alice@example.com", "hunter22")
    user = db.verify_user("alice@example.com", "hunter22")

    deleted = db.delete_resume(9999, user["id"])

    assert deleted is False


def test_delete_resume_blocks_cross_user_deletion():
    db.create_user("alice@example.com", "hunter22")
    alice = db.verify_user("alice@example.com", "hunter22")
    resume_id = db.save_resume(alice["id"], "resume.pdf", "Some resume text")

    db.create_user("bob@example.com", "hunter22")
    bob = db.verify_user("bob@example.com", "hunter22")

    deleted = db.delete_resume(resume_id, bob["id"])

    assert deleted is False
    assert len(db.get_user_resumes(alice["id"])) == 1  # Alice's resume untouched


def test_get_all_analyses_for_user_spans_multiple_resumes():
    db.create_user("alice@example.com", "hunter22")
    user = db.verify_user("alice@example.com", "hunter22")
    rid1 = db.save_resume(user["id"], "r1.pdf", "text one")
    rid2 = db.save_resume(user["id"], "r2.pdf", "text two")
    db.save_analysis(rid1, "Job A", "Score: 80")
    db.save_analysis(rid2, "Job B", "Score: 60")

    all_analyses = db.get_all_analyses_for_user(user["id"])

    assert len(all_analyses) == 2
    filenames = {a["resume_filename"] for a in all_analyses}
    assert filenames == {"r1.pdf", "r2.pdf"}


def test_get_all_analyses_for_user_excludes_other_users():
    db.create_user("alice@example.com", "hunter22")
    alice = db.verify_user("alice@example.com", "hunter22")
    rid = db.save_resume(alice["id"], "r1.pdf", "text")
    db.save_analysis(rid, "Job A", "Score: 80")

    db.create_user("bob@example.com", "hunter22")
    bob = db.verify_user("bob@example.com", "hunter22")

    assert db.get_all_analyses_for_user(bob["id"]) == []