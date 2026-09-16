import re

import streamlit as st

import db

ROLES = ["Public", "Researcher", "Official"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def current_user():
    return st.session_state.get("user")


def is_logged_in():
    return current_user() is not None


def current_role():
    user = current_user()
    return user["role"] if user else "Public"


def has_role(*allowed_roles):
    return current_role() in allowed_roles


def logout():
    st.session_state["user"] = None


def login_form():
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Enter both username and password.")
                return

            user = db.verify_user(username.strip(), password)
            if user:
                st.session_state["user"] = {
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                }
                st.success(f"Welcome, {user['full_name']} ({user['role']}).")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with st.expander("Demo accounts for reviewers"):
        st.markdown(
            "- **Official** — username `official_demo`, password `Demo@1234`\n"
            "- **Researcher** — username `researcher_demo`, password `Demo@1234`\n\n"
            "Both are created automatically on first run. You can also sign up your own "
            "account from the Sign Up tab."
        )


def signup_form():
    with st.form("signup_form"):
        full_name = st.text_input("Full name")
        username = st.text_input("Choose a username")
        email = st.text_input("Email")
        role = st.selectbox("Account type", ["Researcher", "Official"])
        password = st.text_input("Choose a password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create account", use_container_width=True)

        if submitted:
            errors = []
            if not full_name.strip():
                errors.append("Full name is required.")
            if not username.strip() or " " in username.strip():
                errors.append("Username is required and cannot contain spaces.")
            if email and not EMAIL_RE.match(email.strip()):
                errors.append("Email address doesn't look valid.")
            if len(password) < 8:
                errors.append("Password must be at least 8 characters.")
            if password != confirm:
                errors.append("Passwords do not match.")

            if errors:
                for e in errors:
                    st.error(e)
                return

            ok, message = db.create_user(username.strip(), full_name.strip(), email.strip(), role, password)
            if ok:
                st.success(f"{message} You can now log in from the Log In tab.")
            else:
                st.error(message)


def auth_gate():
    st.title("🌏 BhoomiNiti AI — Sign in")
    st.caption(
        "Log in to access Researcher/Official tools such as the Policy Simulation Lab and "
        "Innovation Portal submissions, or continue as a public guest with read-only access."
    )

    tab_login, tab_signup, tab_guest = st.tabs(["Log In", "Sign Up", "Continue as Guest"])

    with tab_login:
        login_form()

    with tab_signup:
        signup_form()

    with tab_guest:
        st.write(
            "Guests can view the Dashboard, GIS Intelligence, Research Hub, AI Intelligence, "
            "Analytics, and the public Innovation Portal listing. Logging in unlocks the Policy "
            "Lab, Reports, and submitting to the Innovation Portal."
        )
        if st.button("Continue as Guest", use_container_width=True):
            st.session_state["user"] = None
            st.session_state["guest_mode"] = True
            st.rerun()

    return is_logged_in()


def require_role(*allowed_roles):
    if not has_role(*allowed_roles):
        st.warning(
            f"This section requires one of these roles: {', '.join(allowed_roles)}. "
            "Please log in with an appropriate account from the sidebar."
        )
        st.stop()
