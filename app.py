"""Par: a daily finance-news reading habit for college students."""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Par · Daily Finance Reader", page_icon="📰", layout="centered")

from par import db, progress, styles  # noqa: E402  (set_page_config must run first)
from views import concepts, login, onboarding, reader, today  # noqa: E402

styles.inject_css()

PAGES = {
    "login": login.render,
    "onboarding": onboarding.render,
    "today": today.render,
    "reader": reader.render,
    "concepts": concepts.render,
}


def go(page, **state):
    st.session_state.page = page
    st.session_state.update(state)
    st.session_state.scroll_top = True
    st.rerun()


def scroll_to_top():
    """Streamlit keeps the scroll position across reruns; reset it on page changes."""
    if st.session_state.pop("scroll_top", False):
        script = ("<script>const m = window.parent.document.querySelector('[data-testid=\"stMain\"]')"
                  " || window.parent.document.querySelector('section.main'); if (m) m.scrollTo(0, 0);"
                  " window.parent.scrollTo(0, 0);</script>")
        if hasattr(st, "iframe"):
            st.iframe(script, height=1)
        else:  # older Streamlit without st.iframe
            components.html(script, height=0)


def nav():
    """Top navigation shown on signed-in pages."""
    cols = st.container(key="nav").columns([1, 1, 1, 1.15], gap="small")
    current = st.session_state.page
    items = [("today", "Today"), ("concepts", "Concepts"), ("onboarding", "Topics")]
    for col, (page, label) in zip(cols, items):
        if col.button(label, key=f"nav_{page}", type="primary" if current == page else "secondary",
                      width="stretch"):
            go(page)
    if cols[3].button("Sign out", key="nav_signout", width="stretch"):
        st.session_state.clear()
        st.rerun()


def main():
    st.session_state.setdefault("page", "login")
    st.session_state.setdefault("user", None)

    user = st.session_state.user
    if user is None:
        st.session_state.page = "login"
    else:
        user = db.get_user(user["username"])  # refresh topics
        if user is None:
            st.session_state.clear()
            st.rerun()
        st.session_state.user = user
        if not user["topics"]:
            st.session_state.page = "onboarding"

    if user is not None and st.session_state.page != "reader":
        styles.masthead(progress.stats(user["id"]))
        nav()
    PAGES[st.session_state.page](go)
    scroll_to_top()


main()
