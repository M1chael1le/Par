"""Streaks, read counts and concept mastery."""
from datetime import date, timedelta

from par import db
from par.config import MASTERY_PER_CORRECT


def today():
    return date.today().isoformat()


def stats(user_id):
    """Returns dict(streak, articles_read, read_today)."""
    reads = db.get_reads(user_id)
    days = {date.fromisoformat(r["read_date"]) for r in reads}
    current = date.today()
    read_today = current in days
    if not read_today:
        current -= timedelta(days=1)  # streak survives until the end of today
    streak = 0
    while current in days:
        streak += 1
        current -= timedelta(days=1)
    return {"streak": streak, "articles_read": len(reads), "read_today": read_today}


def answer_question(user_id, article_id, q_idx, chosen, correct, concepts):
    """Records an answer; first-attempt correct answers raise mastery."""
    first_attempt = db.record_answer(user_id, article_id, q_idx, chosen, correct)
    if first_attempt and correct:
        for concept in concepts:
            db.add_mastery(user_id, concept, MASTERY_PER_CORRECT)


def finish_article(user_id, article_id, takeaway=None, feedback=None):
    db.complete_read(user_id, article_id, today(), takeaway, feedback)


def concept_report(user_id):
    """[(concept, score, [articles])] for concepts the user has met, best first."""
    mastery = db.get_mastery(user_id)
    article_concepts = db.all_article_concepts()
    taught = {}
    for r in db.get_reads(user_id):
        for c in article_concepts.get(r["article_id"], []):
            taught.setdefault(c, []).append(r)
    met = set(mastery) | set(taught)
    report = [(c, mastery.get(c, 0), taught.get(c, [])) for c in met]
    return sorted(report, key=lambda x: (-x[1], x[0]))
