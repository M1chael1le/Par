from datetime import datetime
from html import escape

import streamlit as st

from par import db, news, styles

TOP_STORIES = 9
TOPIC_STORIES = 8


def _published(article):
    if not article.get("published"):
        return ""
    try:
        d = datetime.fromisoformat(article["published"].replace("Z", "+00:00"))
    except ValueError:
        return ""
    return f"{d:%b} {d.day}"


def _lead(article, read_ids, go):
    badge = ' · <span class="read-badge">Read ✓</span>' if article["id"] in read_ids else ""
    styles.html(
        f'<div class="lead">{styles.image_tag(article.get("thumbnail"), "Lead story")}'
        f'<div class="kicker">Lead story · {styles.kicker_for(article)}{badge}</div>'
        f'<h1>{escape(article["title"])}</h1>'
        f'<div class="trail">{escape(article.get("trail") or "")}</div></div>'
    )
    if st.button("Read the lead story →", key=f"lead_{article['id']}", type="primary", width="stretch"):
        go("reader", article_id=article["id"])


def _story(article, read_ids, key_prefix, go):
    meta = [m for m in (styles.kicker_for(article), _published(article)) if m]
    if article["id"] in read_ids:
        meta.append("Read ✓")
    styles.html(
        f'<div class="story">{styles.image_tag(article.get("thumbnail"), "Finance")}'
        f'<div><div class="kicker">{" · ".join(meta)}</div>'
        f'<h3>{escape(article["title"])}</h3>'
        f'<p class="trail">{escape(article.get("trail") or "")}</p></div></div>'
    )
    if st.button("Read the story →", key=f"{key_prefix}_{article['id']}", type="tertiary"):
        go("reader", article_id=article["id"])
    styles.html("<hr>")


def render(go):
    user = st.session_state.user
    read_ids = {r["article_id"] for r in db.get_reads(user["id"])}

    articles, notice = news.get_feed()
    if notice:
        st.info(notice)
    if not articles:
        st.warning("No stories available right now.")
        return

    _lead(articles[0], read_ids, go)

    tabs = st.tabs(["Top Stories", *user["topics"]])
    with tabs[0]:
        for a in articles[1:TOP_STORIES + 1]:
            _story(a, read_ids, "top", go)

    for tab, topic in zip(tabs[1:], user["topics"]):
        with tab:
            topic_articles, topic_notice = news.get_feed(topic)
            if topic_notice and topic_notice != notice:
                st.info(topic_notice)
            for a in topic_articles[:TOPIC_STORIES]:
                _story(a, read_ids, f"t{topic}", go)
