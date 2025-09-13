import streamlit as st
import time
import base64
import json
import hashlib
from PIL import Image

# =================================================================================================
# HELPER FUNCTIONS
# =================================================================================================
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users_data):
    with open("users.json", "w") as f:
        json.dump(users_data, f, indent=4)

# =================================================================================================
# PAGE CONFIGURATION & SESSION STATE
# =================================================================================================
st.set_page_config(page_title="Welcome to AI Study Buddy!", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# =================================================================================================
# LOGIN / SPLASH SCREEN VIEW
# =================================================================================================
if not st.session_state.logged_in:
    
    bg_image_base64 = get_base64_of_bin_file("bg.gif")
    
    # --- Custom CSS for the splash/login screen ---
    st.markdown(f"""
    <style>
        [data-testid="stSidebar"], header, footer {{ visibility: hidden; }}
        .stApp {{
            background-image: linear-gradient(rgba(0, 4, 40, 0.7), rgba(0, 4, 40, 0.7)), url("data:image/jpeg;base64,{bg_image_base64 if bg_image_base64 else ''}");
            background-size: cover; background-position: center;
        }}
        .main .block-container {{ padding-top: 5vh; }}
        h1 {{ color: white; text-shadow: 2px 2px 4px #000000; }}
        .stTabs [data-baseweb="tab-list"] {{ justify-content: center; }}
    </style>
    """, unsafe_allow_html=True)

    # --- Layout with Agent and Login/Sign-up tabs ---
    col_agent, col_auth = st.columns([1, 2])

    with col_agent:
        agent_image_base64 = get_base64_of_bin_file("AiAgent.png")
        if agent_image_base64:
            st.markdown(f'<div style="text-align: center; padding-top: 50px;"><img src="data:image/png;base64,{agent_image_base64}" alt="waving agent" width="300"></div>', unsafe_allow_html=True)
        else:
            st.warning("`AiAgent.png` not found.")

    with col_auth:
        st.title("Welcome to your AI Study Buddy! 🚀")
        st.write("Please log in or sign up to continue.")
        
        login_tab, signup_tab = st.tabs(["🔒 Login", "✍️ Sign Up"])

        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    users = load_users()
                    if username in users and users[username]['password_hash'] == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Incorrect username or password.")

        with signup_tab:
            with st.form("signup_form"):
                new_username = st.text_input("Choose a Username")
                new_password = st.text_input("Choose a Password", type="password")
                mobile_number = st.text_input("Mobile Number (for notifications)", placeholder="+91 1234567890")
                if st.form_submit_button("Sign Up"):
                    users = load_users()
                    if new_username in users:
                        st.error("Username already exists.")
                    elif not all([new_username, new_password, mobile_number]):
                        st.warning("Please fill in all fields.")
                    else:
                        users[new_username] = {'password_hash': hash_password(new_password), 'mobile_number': mobile_number}
                        save_users(users)
                        st.session_state.logged_in = True
                        st.session_state.username = new_username
                        st.success("Account created! You are now logged in.")
                        time.sleep(1)
                        st.rerun()

# =================================================================================================
# MAIN APP VIEW (Shows AFTER the user is logged in)
# =================================================================================================
else:
    st.sidebar.success(f"Welcome, {st.session_state.username}!")
    st.title("🎉 Welcome to your AI Study Buddy!")
    st.info("You're all set! Please choose a tool from the sidebar on the left to get started.", icon="👈")