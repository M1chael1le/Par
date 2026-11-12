from datetime import datetime
from html import escape

import streamlit as st

from par import ai, db, news, processing, progress, styles

ROMAN = ["I", "II", "III"]


def _state(article_id):
    """Per-article reader state: how many sections are revealed."""
    readers = st.session_state.setdefault("reader_state", {})
    return readers.setdefault(article_id, {"step": 1})


def _byline(article):
    parts = ["Sample article" if article["id"].startswith("sample/") else "The Guardian"]
    if article.get("published"):
        try:
            d = datetime.fromisoformat(article["published"].replace("Z", "+00:00"))
            parts.append(f"{d:%B} {d.day}, {d.year}")
        except ValueError:
            pass
    return " · ".join(parts)


def _header(article, study):
    styles.html(
        f'<div class="reader-head"><div class="kicker">{styles.kicker_for(article)}</div>'
        f'<h1>{escape(article["title"])}</h1>'
        f'<div class="byline">{escape(_byline(article))}'
        + (f' · <a href="{escape(article["url"], quote=True)}" target="_blank">Full article ↗</a>'
           if article.get("url") else "")
        + f'</div>{styles.image_tag(article.get("thumbnail"), "Today")}</div>'
    )
    if study.get("overview"):
        styles.html(f'<div class="overview"><div class="label">In one sentence · AI overview</div>'
                    f'<p>{escape(study["overview"])}</p></div>')
    if study.get("concepts"):
        tags = "".join(f'<span class="concept-tag">{escape(c)}</span>' for c in study["concepts"])
        styles.html(f'<div style="margin-bottom:.4rem">{tags}</div>')


def _section(idx, paragraphs):
    styles.html(
        f'<div class="sec-head"><span class="num">{ROMAN[idx]}.</span><span class="line"></span>'
        f'<span class="of">Section {idx + 1} of 3</span></div>'
    )
    body = "".join(f"<p>{escape(p)}</p>" for p in paragraphs)
    styles.html(f'<div class="article-body">{body}</div>')


def _question(article_id, q_idx, q, answers, concepts, user_id, number, total):
    styles.html(f'<div class="quiz-label">Check your understanding · {number} of {total}</div>'
                f'<div class="quiz-q">{escape(q["question"])}</div>')
    prior = answers.get(q_idx)
    choice = st.radio(
        q["question"], list(range(len(q["options"]))),
        format_func=lambda i: q["options"][i],
        index=prior["chosen"] if prior else None,
        key=f"q_{article_id}_{q_idx}",
        disabled=prior is not None,
        label_visibility="collapsed",
    )
    if prior:
        correct_text = escape(q["options"][q["answer_index"]])
        if prior["correct"]:
            styles.html(f'<div class="verdict"><b>Correct.</b> {escape(q["explanation"])}</div>')
        else:
            styles.html(f'<div class="verdict wrong"><b>Not quite.</b> The answer is '
                        f'<i>{correct_text}</i>. {escape(q["explanation"])}</div>')
    elif st.button("Check answer", key=f"check_{article_id}_{q_idx}", disabled=choice is None):
        progress.answer_question(user_id, article_id, q_idx, choice,
                                 choice == q["answer_index"], concepts)
        st.rerun()


def _takeaway(article, study, user_id, answers, n_questions):
    styles.html('<div class="section-label">In Your Own Words</div>')
    read = db.get_read(user_id, article["id"])

    if read and read.get("takeaway"):
        styles.html(f'<p class="muted">Your takeaway</p><div class="feedback-box"><i>'
                    f'{escape(read["takeaway"])}</i></div>')
        if read.get("feedback"):
            styles.html(f'<p class="muted">Feedback</p><div class="feedback-box">'
                        f'{escape(read["feedback"])}</div>')
    elif not read:
        styles.html('<p>In 2–3 sentences, what happened and why does it matter? '
                    'Writing it down is how it sticks.</p>')
        with st.form(f"takeaway_{article['id']}"):
            text = st.text_area("Your takeaway", height=120, label_visibility="collapsed",
                                placeholder="The main point of this story is…")
            submitted = st.form_submit_button("Submit for feedback", type="primary", width="stretch")
        if submitted:
            if len(text.split()) < 8:
                st.error("Write at least a couple of sentences (8+ words).")
            else:
                feedback = None
                if ai.has_ai_key():
                    with st.spinner("Reading your takeaway…"):
                        try:
                            feedback = ai.takeaway_feedback(article["title"], article["paragraphs"], text)
                        except ai.AIError as e:
                            st.session_state["takeaway_notice"] = f"Couldn't get feedback ({e}). Your takeaway was saved."
                else:
                    st.session_state["takeaway_notice"] = ("Takeaway saved. AI feedback needs an "
                                                           "ANTHROPIC_API_KEY.")
                progress.finish_article(user_id, article["id"], text.strip(), feedback)
                st.rerun()
        if st.button("Skip and mark as read", type="tertiary"):
            progress.finish_article(user_id, article["id"])
            st.rerun()
        return

    notice = st.session_state.pop("takeaway_notice", None)
    if notice:
        st.info(notice)
    _completion(user_id, study, answers, n_questions)


def _completion(user_id, study, answers, n_questions):
    stats = progress.stats(user_id)
    score = sum(1 for a in answers.values() if a["correct"])
    n_read = stats["articles_read"]
    lines = [f"<b>Article complete.</b> {stats['streak']}-day streak · "
             f"{n_read} article{'s' if n_read != 1 else ''} read."]
    if n_questions:
        lines.append(f"You answered {score} of {n_questions} correctly on the first try.")
    if study.get("concepts"):
        mastery = db.get_mastery(user_id)
        lines.append("Concepts: " + ", ".join(
            f"{escape(c)} ({mastery.get(c, 0)}/100)" for c in study["concepts"]))
    styles.html(f'<div class="verdict">{"<br>".join(lines)}</div>')


def render(go):
    user = st.session_state.user
    article_id = st.session_state.get("article_id")
    article = news.get_article(article_id) if article_id else None

    if st.button("← Back to Today", type="tertiary"):
        go("today")
    if not article:
        st.error("That article isn't available anymore. Head back to Today for fresh stories.")
        return

    with st.spinner("Setting the type: preparing sections and questions…"):
        study, notice = processing.get_study_layer(article)

    _header(article, study)
    if notice:
        st.info(notice)

    sections = processing.split_sections(article["paragraphs"], study["breaks"])
    questions = study["questions"]
    answers = db.get_answers(user["id"], article_id)
    state = _state(article_id)
    if not questions or db.get_read(user["id"], article_id):
        state["step"] = 3  # nothing to gate on, or a re-read

    for idx in range(state["step"]):
        if sections[idx]:
            _section(idx, sections[idx])
        sec_qs = [(i, q) for i, q in enumerate(questions) if q["section"] == idx]
        for n, (q_idx, q) in enumerate(sec_qs, start=1):
            _question(article_id, q_idx, q, answers, study["concepts"], user["id"], n, len(sec_qs))

        section_done = all(i in answers for i, _ in sec_qs)
        is_frontier = idx == state["step"] - 1
        if is_frontier and not section_done:
            styles.html('<p class="muted" style="text-align:center">Answer to continue reading.</p>')
            return
        if is_frontier and idx < 2:
            if st.button(f"Continue to section {ROMAN[idx + 1]} →", type="primary", width="stretch"):
                state["step"] += 1
                st.rerun()
            return

    _takeaway(article, study, user["id"], answers, len(questions))
    if article.get("url"):
        st.link_button("Read the full article at the Guardian ↗", article["url"], width="stretch")
    if st.button("Back to today's front page", width="stretch"):
        go("today")
