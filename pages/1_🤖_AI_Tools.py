import streamlit as st
import datetime
import json
import time
import base64
import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.generativeai as genai
from PIL import Image
import pandas as pd
import plotly.express as px

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

def create_priority_chart(priority_level, plan, theme_colors):
    tasks = [t for t in plan if t['priority'] == priority_level]
    if not tasks: return None
    completed = len([t for t in tasks if t['done']])
    not_completed = len(tasks) - completed
    df = pd.DataFrame({'Status': ['Completed', 'Not Completed'], 'Count': [completed, not_completed]})
    
    fig = px.pie(df, values='Count', names='Status', title=f'{priority_level} Priority Tasks',
                 color_discrete_map={'Completed':'#4CAF50', 'Not Completed':'#F44336'})
    fig.update_traces(textposition='inside', textinfo='percent+label', hole=.3)
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      font_color=theme_colors["text"]) # Use theme text color
    return fig

def get_user_chat_dir(username):
    user_chat_dir = os.path.join("chats", username)
    if not os.path.exists(user_chat_dir):
        os.makedirs(user_chat_dir)
    return user_chat_dir

def save_chat_history(username, chat_history, filename):
    user_chat_dir = get_user_chat_dir(username)
    with open(os.path.join(user_chat_dir, filename), "w") as f:
        json.dump(chat_history, f, indent=4)

def load_chat_history(username, filename):
    user_chat_dir = get_user_chat_dir(username)
    try:
        with open(os.path.join(user_chat_dir, filename), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def delete_chat_history(username, filename):
    user_chat_dir = get_user_chat_dir(username)
    file_path = os.path.join(user_chat_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

# =================================================================================================
# COLOR THEME LOGIC
# =================================================================================================
COLOR_THEMES = {
    "⚪ Light": {"primary": "#000000", "background": "#FFFFFF", "secondary_bg": "#F0F2F6", "text": "#000000"},
    "⚫ Dark": {"primary": "#FFFFFF", "background": "#0E1117", "secondary_bg": "#1C1C1C", "text": "#FFFFFF"},
    "🔴 Red": {"primary": "#FFFFFF", "background": "#7B241C", "secondary_bg": "#A93226", "text": "#FFFFFF"},
    "🔵 Blue": {"primary": "#FFFFFF", "background": "#154360", "secondary_bg": "#1F618D", "text": "#FFFFFF"},
    "🟢 Green": {"primary": "#FFFFFF", "background": "#145A32", "secondary_bg": "#1E8449", "text": "#FFFFFF"},
    "🩷 Pink": {"primary": "#FFFFFF", "background": "#880E4F", "secondary_bg": "#C2185B", "text": "#FFFFFF"},
    "🩵 Light Blue": {"primary": "#000000", "background": "#E1F5FE", "secondary_bg": "#B3E5FC", "text": "#01579B"},
    "💜 Lavender": {"primary": "#FFFFFF", "background": "#4A148C", "secondary_bg": "#6A1B9A", "text": "#FFFFFF"},
    "💛 Yellow": {"primary": "#000000", "background": "#FFFDE7", "secondary_bg": "#FFF9C4", "text": "#F57F17"},
}

def apply_color_theme(theme_colors):
    css = f"""
    <style>
        .stApp {{ background-color: {theme_colors["background"]}; color: {theme_colors["text"]}; }}
        .st-emotion-cache-16txtl3 {{ background-color: {theme_colors["secondary_bg"]}; }}
        .stButton>button, .stDownloadButton>button {{
            background-color: {theme_colors["primary"]}; color: {theme_colors["background"]};
            border: 2px solid {theme_colors["background"]};
        }}
        h1, h2, h3, h4, h5, h6, p, li, label, .st-emotion-cache-16txtl3 {{ color: {theme_colors["text"]} !important; }}
        .st-emotion-cache-16txtl3 h1, .st-emotion-cache-16txtl3 h2, .st-emotion-cache-16txtl3 h3, .st-emotion-cache-16txtl3 p, .st-emotion-cache-16txtl3 b {{ color: {theme_colors["primary"]} !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

if "selected_theme_emoji" not in st.session_state:
    st.session_state.selected_theme_emoji = "⚪ Light"

st.sidebar.write("Choose a theme:")
cols = st.sidebar.columns(5)
col_index = 0
for emoji_and_name, colors in COLOR_THEMES.items():
    with cols[col_index]:
        if st.button(emoji_and_name.split(" ")[0], use_container_width=True, key=f"theme_{emoji_and_name}"):
            st.session_state.selected_theme_emoji = emoji_and_name
            st.rerun()
    col_index = (col_index + 1) % 5

selected_theme_colors = COLOR_THEMES[st.session_state.selected_theme_emoji]
apply_color_theme(selected_theme_colors)
# =================================================================================================

# --- MAIN APP ---
if not st.session_state.get("logged_in", False):
    st.warning("Please log in from the Home page to use the application.")
    st.stop()

username = st.session_state.get("username", "default_user")

# --- API CONFIGURATIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception:
    st.error("Failed to configure Gemini API.")
    st.stop()
try:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    st.sidebar.success("Connected to Google Calendar.")
except FileNotFoundError:
    st.sidebar.error("`credentials.json` not found for Google Calendar.")
except Exception as e:
    st.sidebar.error(f"Google Calendar Error: {e}")

# --- SESSION STATE INITIALIZATION ---
if "plan" not in st.session_state: st.session_state.plan = []
if 'active_chat' not in st.session_state: st.session_state.active_chat = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- Sidebar for Chat History Navigation ---
st.sidebar.title(f"{username}'s Chats")
if st.sidebar.button("➕ New Chat"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.active_chat = f"chat_{timestamp}.json"
    st.session_state.chat_history = []
    save_chat_history(username, [], st.session_state.active_chat)
    st.rerun()

st.sidebar.write("---")
st.sidebar.subheader("Saved Conversations")
try:
    user_chat_dir = get_user_chat_dir(username)
    chat_files = sorted([f for f in os.listdir(user_chat_dir) if f.endswith(".json")], reverse=True)
    for chat_file in chat_files:
        col1, col2 = st.sidebar.columns([0.8, 0.2])
        with col1:
            display_name = chat_file.replace("chat_", "").replace(".json", "").replace("_", " at ")
            if st.button(display_name, key=f"load_{chat_file}", use_container_width=True):
                st.session_state.active_chat = chat_file
                st.session_state.chat_history = load_chat_history(username, chat_file)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{chat_file}", help=f"Delete chat {display_name}"):
                delete_chat_history(username, chat_file)
                if st.session_state.active_chat == chat_file:
                    st.session_state.active_chat = None
                    st.session_state.chat_history = []
                st.rerun()
except Exception as e:
    st.sidebar.error(f"Error loading chat files: {e}")

# --- MAIN PAGE TABS ---
planner_tab, assistant_tab = st.tabs(["🗓️ Study Planner", "🤖 AI Assistant"])

with planner_tab:
    st.header("Plan Your Week")
    with st.form("new_task_form", clear_on_submit=True):
        st.subheader("Add a New Study Task")
        task_date = st.date_input("Date", datetime.date.today())
        subject = st.text_input("Enter Subject")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        start_time = st.time_input("Start Time", datetime.time(9, 0))
        end_time = st.time_input("End Time", datetime.time(10, 0))
        submitted = st.form_submit_button("➕ Add to Plan & Calendar")

    if submitted and subject:
        # (Add task logic here...)
        st.toast(f"Task '{subject}' added!")

    st.subheader("📌 Today's Plan & Priority Breakdown")
    dash_col1, dash_col2 = st.columns([2, 1])
    with dash_col1:
        # (Task list and progress bar logic here...)
        pass
    with dash_col2:
        if st.session_state.plan:
            for priority in ["High", "Medium", "Low"]:
                chart = create_priority_chart(priority, st.session_state.plan, selected_theme_colors)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)

with assistant_tab:
    st.header("Your Doubt-Solving Bestie!")
    if st.session_state.active_chat:
        st.caption(f"Continuing chat: `{st.session_state.active_chat.replace('.json', '')}`")
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["parts"])
        
        if user_prompt := st.chat_input("What can I help you with?"):
            st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
            with st.chat_message("user"): st.markdown(user_prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    chat = model.start_chat(history=st.session_state.chat_history)
                    response = chat.send_message(user_prompt)
                    st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "parts": response.text})
            save_chat_history(username, st.session_state.chat_history, st.session_state.active_chat)
    else:
        st.info("To talk to the AI, start a '➕ New Chat' from the sidebar.")