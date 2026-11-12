import streamlit as st

from par import auth, styles


def render(go):
    styles.masthead()
    styles.html('<p class="muted" style="text-align:center;margin:.6rem 0 1.2rem">'
                'Read one real finance story a day. Get quizzed. Watch your understanding compound.</p>')

    sign_in, sign_up = st.tabs(["Sign in", "Create account"])

    with sign_in:
        with st.form("signin"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
        if submitted:
            user, error = auth.sign_in(username, password)
            if error:
                st.error(error)
            else:
                go("today" if user["topics"] else "onboarding", user=user)

    with sign_up:
        with st.form("signup"):
            username = st.text_input("Choose a username")
            password = st.text_input("Choose a password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary", width="stretch")
        if submitted:
            if password != confirm:
                st.error("Passwords don't match.")
            else:
                user, error = auth.sign_up(username, password)
                if error:
                    st.error(error)
                else:
                    go("onboarding", user=user)
