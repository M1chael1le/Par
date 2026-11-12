import streamlit as st

from par import db, styles
from par.config import MAX_TOPICS, TOPICS


def render(go):
    user = st.session_state.user
    first_time = not user["topics"]

    styles.html('<div class="section-label">Your Beats</div>')
    styles.html(f'<p style="text-align:center">Pick up to {MAX_TOPICS} topics. '
                'They become tabs on your front page.</p>')

    picked = st.pills(
        "Topics", list(TOPICS), selection_mode="multi", default=user["topics"],
        label_visibility="collapsed", key="topic_pills",
    )

    if len(picked) > MAX_TOPICS:
        st.warning(f"Choose at most {MAX_TOPICS} topics. You've picked {len(picked)}.")
    label = "Start reading" if first_time else "Save topics"
    if st.button(label, type="primary", width="stretch",
                 disabled=not picked or len(picked) > MAX_TOPICS):
        db.set_topics(user["id"], picked)
        go("today")
