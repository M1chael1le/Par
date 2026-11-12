from html import escape

import streamlit as st

from par import progress, styles
from par.config import CONCEPTS, mastery_level


def render(go):
    user = st.session_state.user
    report = progress.concept_report(user["id"])

    styles.html('<div class="section-label">Concepts</div>')
    styles.html('<p class="muted" style="text-align:center">Every story teaches a few recurring ideas. '
                'Correct first-try answers build your mastery.</p>')

    if not report:
        styles.html('<p style="text-align:center;margin-top:1.5rem">'
                    'You haven\'t met any concepts yet. Read your first story to begin.</p>')
        if st.button("Go to today's stories →", type="primary", width="stretch"):
            go("today")
    else:
        for concept, score, articles in report:
            n = len(articles)
            taught = (f"Taught by {n} article{'s' if n != 1 else ''}:" if n
                      else "Practised in quizzes. Finish the article to log it here.")
            styles.html(
                f'<div class="concept-row"><div class="top"><span class="name">{escape(concept)}</span>'
                f'<span class="level">{mastery_level(score)} · {score}/100</span></div>'
                f'<div class="bar"><span style="width:{score}%"></span></div>'
                f'<div class="taught">{taught}</div></div>'
            )
            for a in articles:
                if st.button(a["title"] or "Untitled article", key=f"c_{concept}_{a['article_id']}",
                             type="tertiary"):
                    go("reader", article_id=a["article_id"])

    met = {c for c, _, _ in report}
    remaining = [c for c in CONCEPTS if c not in met]
    if remaining:
        styles.html('<div class="section-label" style="margin-top:2rem">Still to Discover</div>')
        styles.html('<p class="muted" style="text-align:center;line-height:1.9">'
                    + " · ".join(escape(c) for c in remaining) + "</p>")
