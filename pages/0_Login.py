import streamlit as st
from db_utils import authenticate_user, register_user, logout, db_available
from utils import page_config, show_top_logo

st.set_page_config(page_title="Kayfa — Login", page_icon="🔐", layout="centered")
show_top_logo()

st.title("🔐 Kayfa Student Analytics")
st.markdown("##### Sign in or create an account")

if not db_available():
    st.info(
        "⚠️ **MongoDB Atlas unreachable** — using local file storage instead. "
        "Login/register will work, snapshots save to `.local_db/`.\n\n"
        "To connect MongoDB, whitelist this machine's IP in your "
        "[Atlas Network Access](https://cloud.mongodb.com) settings."
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("Login")
    with st.form("login_form"):
        l_user = st.text_input("Username", key="login_user")
        l_pass = st.text_input("Password", type="password", key="login_pass")
        if st.form_submit_button("Login", use_container_width=True):
            ok, msg = authenticate_user(l_user, l_pass)
            if ok:
                st.session_state["authenticated"] = True
                st.session_state["username"] = l_user
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

with col2:
    st.subheader("Register")
    with st.form("register_form"):
        r_user = st.text_input("Username", key="reg_user")
        r_pass = st.text_input("Password", type="password", key="reg_pass")
        r_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        if st.form_submit_button("Register", use_container_width=True):
            if r_pass != r_confirm:
                st.error("Passwords do not match")
            elif len(r_pass) < 4:
                st.error("Password must be at least 4 characters")
            else:
                ok, msg = register_user(r_user, r_pass)
                if ok:
                    st.success(msg)
                    st.info("You can now log in.")
                else:
                    st.error(msg)

st.divider()
st.markdown("#### About")
st.caption(
    "Kayfa Student Analytics provides dashboards for attendance, engagement, "
    "academic performance, group integrity, curriculum weak spots, and student risk profiling. "
    "Register to save analysis results and track changes over time."
)

if "authenticated" in st.session_state and st.session_state["authenticated"]:
    st.success(f"✅ Logged in as **{st.session_state['username']}**")
    if st.button("Logout", use_container_width=True):
        logout()
