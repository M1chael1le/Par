"""Guardian Open Platform client with SQLite caching and sample-article fallback."""
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser

import requests

from par import db
from par.config import FEED_TTL_MINUTES, GUARDIAN_SECTIONS, GUARDIAN_URL, TOPICS, get_secret
from par.sample_data import SAMPLE_ARTICLES, SAMPLES_BY_ID

MIN_PARAGRAPHS = 6


class _ParagraphParser(HTMLParser):
    """Collects the text of top-level <p> tags, skipping figures, asides and embeds."""

    SKIP = {"figure", "aside", "figcaption", "script", "style"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paragraphs = []
        self._buf = None
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag == "p" and self._skip_depth == 0:
            self._buf = []
        elif tag == "br" and self._buf is not None:
            self._buf.append(" ")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "p" and self._buf is not None:
            text = " ".join("".join(self._buf).split())
            if text:
                self.paragraphs.append(text)
            self._buf = None

    def handle_data(self, data):
        if self._buf is not None and self._skip_depth == 0:
            self._buf.append(data)


def html_to_paragraphs(body_html):
    parser = _ParagraphParser()
    parser.feed(body_html or "")
    return parser.paragraphs


def has_guardian_key():
    return bool(get_secret("GUARDIAN_API_KEY"))


def _samples(topic=None):
    if topic:
        matched = [a for a in SAMPLE_ARTICLES if topic in a["topics"]]
        return matched or SAMPLE_ARTICLES
    return SAMPLE_ARTICLES


def _fetch_guardian(api_key, topic=None):
    params = {
        "section": GUARDIAN_SECTIONS,
        "tag": "type/article",
        "show-fields": "body,thumbnail,trailText",
        "order-by": "newest",
        "page-size": 15,
        "api-key": api_key,
    }
    if topic:
        params["q"] = TOPICS[topic]
    resp = requests.get(GUARDIAN_URL, params=params, timeout=10)
    resp.raise_for_status()
    results = resp.json()["response"]["results"]

    articles = []
    for r in results:
        fields = r.get("fields", {})
        paragraphs = html_to_paragraphs(fields.get("body", ""))
        if len(paragraphs) < MIN_PARAGRAPHS:
            continue  # skip briefs, galleries and other non-reading pieces
        articles.append({
            "id": r["id"],
            "title": r["webTitle"],
            "url": r["webUrl"],
            "thumbnail": fields.get("thumbnail"),
            "trail": unescape(" ".join(html_to_paragraphs(f"<p>{fields.get('trailText', '')}</p>"))),
            "published": r.get("webPublicationDate"),
            "paragraphs": paragraphs,
        })
    return articles


def get_feed(topic=None):
    """Returns (articles, notice). notice is None or a user-facing message string."""
    if not has_guardian_key():
        return _samples(topic), (
            "Showing bundled sample articles. Add a GUARDIAN_API_KEY to read today's real finance news."
        )

    key = f"topic:{topic}" if topic else "top"
    cached = db.get_feed(key)
    if cached:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(cached["fetched_at"])
        if age < timedelta(minutes=FEED_TTL_MINUTES):
            articles = [a for a in (db.get_article(i) for i in cached["article_ids"]) if a]
            if articles:
                return articles, None

    try:
        articles = _fetch_guardian(get_secret("GUARDIAN_API_KEY"), topic)
    except (requests.RequestException, KeyError, ValueError) as e:
        stale = [a for a in (db.get_article(i) for i in (cached or {}).get("article_ids", [])) if a]
        reason = _describe_error(e)
        if stale:
            return stale, f"Couldn't refresh from the Guardian ({reason}). Showing earlier stories."
        return _samples(topic), f"Couldn't reach the Guardian ({reason}). Showing sample articles instead."

    if not articles:
        return _samples(topic), "The Guardian returned no stories for this topic right now. Showing sample articles."

    for a in articles:
        db.save_article(a)
    db.save_feed(key, [a["id"] for a in articles])
    return articles, None


def get_article(article_id):
    if article_id in SAMPLES_BY_ID:
        return SAMPLES_BY_ID[article_id]
    return db.get_article(article_id)


def _describe_error(e):
    if isinstance(e, requests.HTTPError) and e.response is not None:
        if e.response.status_code in (401, 403):
            return "the API key was rejected"
        if e.response.status_code == 429:
            return "rate limit reached"
        return f"HTTP {e.response.status_code}"
    if isinstance(e, requests.Timeout):
        return "request timed out"
    if isinstance(e, requests.ConnectionError):
        return "no network connection"
    return "unexpected response"
