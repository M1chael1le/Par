"""SQLite storage: users, cached articles/AI output, and reading progress."""
import json
import sqlite3
import threading
from datetime import datetime, timezone

import streamlit as st

from par.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    pw_hash     TEXT NOT NULL,
    topics      TEXT NOT NULL DEFAULT '[]',
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS articles (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    url         TEXT,
    thumbnail   TEXT,
    trail       TEXT,
    paragraphs  TEXT NOT NULL,
    published   TEXT,
    fetched_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feeds (
    key         TEXT PRIMARY KEY,
    article_ids TEXT NOT NULL,
    fetched_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS article_ai (
    article_id  TEXT PRIMARY KEY,
    overview    TEXT NOT NULL,
    breaks      TEXT NOT NULL,
    questions   TEXT NOT NULL,
    concepts    TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reads (
    user_id      INTEGER NOT NULL,
    article_id   TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    read_date    TEXT NOT NULL,
    takeaway     TEXT,
    feedback     TEXT,
    PRIMARY KEY (user_id, article_id)
);
CREATE TABLE IF NOT EXISTS answers (
    user_id     INTEGER NOT NULL,
    article_id  TEXT NOT NULL,
    q_idx       INTEGER NOT NULL,
    chosen      INTEGER NOT NULL,
    correct     INTEGER NOT NULL,
    answered_at TEXT NOT NULL,
    PRIMARY KEY (user_id, article_id, q_idx)
);
CREATE TABLE IF NOT EXISTS concept_mastery (
    user_id     INTEGER NOT NULL,
    concept     TEXT NOT NULL,
    score       INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (user_id, concept)
);
"""

_lock = threading.Lock()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@st.cache_resource
def _connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def query(sql, params=()):
    with _lock:
        return [dict(r) for r in _connection().execute(sql, params).fetchall()]


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    with _lock:
        conn = _connection()
        cur = conn.execute(sql, params)
        conn.commit()
        return cur


# ---------- users ----------

def create_user(username, pw_hash):
    execute(
        "INSERT INTO users (username, pw_hash, created_at) VALUES (?, ?, ?)",
        (username, pw_hash, now_iso()),
    )
    return get_user(username)


def get_user(username):
    user = query_one("SELECT * FROM users WHERE username = ?", (username,))
    if user:
        user["topics"] = json.loads(user["topics"])
    return user


def set_topics(user_id, topics):
    execute("UPDATE users SET topics = ? WHERE id = ?", (json.dumps(topics), user_id))


# ---------- article cache ----------

def save_article(a):
    execute(
        """INSERT OR REPLACE INTO articles
           (id, title, url, thumbnail, trail, paragraphs, published, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (a["id"], a["title"], a.get("url"), a.get("thumbnail"), a.get("trail"),
         json.dumps(a["paragraphs"]), a.get("published"), now_iso()),
    )


def get_article(article_id):
    row = query_one("SELECT * FROM articles WHERE id = ?", (article_id,))
    if row:
        row["paragraphs"] = json.loads(row["paragraphs"])
    return row


def save_feed(key, article_ids):
    execute(
        "INSERT OR REPLACE INTO feeds (key, article_ids, fetched_at) VALUES (?, ?, ?)",
        (key, json.dumps(article_ids), now_iso()),
    )


def get_feed(key):
    row = query_one("SELECT * FROM feeds WHERE key = ?", (key,))
    if row:
        row["article_ids"] = json.loads(row["article_ids"])
    return row


def save_article_ai(article_id, ai):
    execute(
        """INSERT OR REPLACE INTO article_ai
           (article_id, overview, breaks, questions, concepts, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (article_id, ai["overview"], json.dumps(ai["breaks"]),
         json.dumps(ai["questions"]), json.dumps(ai["concepts"]), now_iso()),
    )


def get_article_ai(article_id):
    row = query_one("SELECT * FROM article_ai WHERE article_id = ?", (article_id,))
    if row:
        for field in ("breaks", "questions", "concepts"):
            row[field] = json.loads(row[field])
    return row


def all_article_concepts():
    """{article_id: [concepts]} for every processed article."""
    rows = query("SELECT article_id, concepts FROM article_ai")
    return {r["article_id"]: json.loads(r["concepts"]) for r in rows}


# ---------- progress ----------

def get_answers(user_id, article_id):
    rows = query(
        "SELECT q_idx, chosen, correct FROM answers WHERE user_id = ? AND article_id = ?",
        (user_id, article_id),
    )
    return {r["q_idx"]: r for r in rows}


def record_answer(user_id, article_id, q_idx, chosen, correct):
    """Returns True if this was the first attempt (and therefore counts)."""
    cur = execute(
        """INSERT OR IGNORE INTO answers
           (user_id, article_id, q_idx, chosen, correct, answered_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, article_id, q_idx, chosen, int(correct), now_iso()),
    )
    return cur.rowcount == 1


def add_mastery(user_id, concept, points):
    execute(
        """INSERT INTO concept_mastery (user_id, concept, score, updated_at)
           VALUES (?, ?, MIN(?, 100), ?)
           ON CONFLICT(user_id, concept)
           DO UPDATE SET score = MIN(score + excluded.score, 100), updated_at = excluded.updated_at""",
        (user_id, concept, points, now_iso()),
    )


def get_mastery(user_id):
    rows = query("SELECT concept, score FROM concept_mastery WHERE user_id = ?", (user_id,))
    return {r["concept"]: r["score"] for r in rows}


def complete_read(user_id, article_id, read_date, takeaway=None, feedback=None):
    execute(
        """INSERT INTO reads (user_id, article_id, completed_at, read_date, takeaway, feedback)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_id, article_id)
           DO UPDATE SET takeaway = COALESCE(excluded.takeaway, takeaway),
                         feedback = COALESCE(excluded.feedback, feedback)""",
        (user_id, article_id, now_iso(), read_date, takeaway, feedback),
    )


def get_read(user_id, article_id):
    return query_one(
        "SELECT * FROM reads WHERE user_id = ? AND article_id = ?", (user_id, article_id)
    )


def get_reads(user_id):
    return query(
        """SELECT r.article_id, r.read_date, r.completed_at, a.title
           FROM reads r LEFT JOIN articles a ON a.id = r.article_id
           WHERE r.user_id = ? ORDER BY r.completed_at DESC""",
        (user_id,),
    )
