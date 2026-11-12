"""Get an article's study layer: cache -> sample data -> Claude -> plain fallback."""
from par import ai, db
from par.sample_data import SAMPLES_BY_ID


def get_study_layer(article):
    """Returns (study, notice).

    study = dict(overview, breaks, questions, concepts). notice is a user-facing
    message when the AI layer is unavailable (study then has no quiz or concepts).
    """
    cached = db.get_article_ai(article["id"])
    if cached:
        return cached, None

    if article["id"] in SAMPLES_BY_ID:
        study = SAMPLES_BY_ID[article["id"]]["ai"]
        db.save_article(article)  # so reading history can show its title
        db.save_article_ai(article["id"], study)
        return study, None

    fallback = {
        "overview": None,
        "breaks": ai.even_breaks(len(article["paragraphs"])),
        "questions": [],
        "concepts": [],
    }
    if not ai.has_ai_key():
        return fallback, "Quizzes and overviews need an ANTHROPIC_API_KEY. You can still read the article below."

    try:
        study = ai.analyze_article(article["title"], article["paragraphs"])
    except ai.AIError as e:
        return fallback, f"Couldn't prepare the quiz ({e}). You can still read the article below."

    db.save_article_ai(article["id"], study)
    return study, None


def split_sections(paragraphs, breaks):
    a, b = breaks
    return [paragraphs[:a], paragraphs[a:b], paragraphs[b:]]
