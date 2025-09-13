import streamlit as st
import google.generativeai as genai
import time

# =================================================================================================
# THEME SELECTOR CODE - PASTE THIS AT THE TOP OF EACH PAGE SCRIPT
# =================================================================================================
def apply_theme(theme_name):
    """
    Applies a theme by injecting custom CSS into the Streamlit app.
    """
    css = ""
    # --- Spiderman Theme ---
    if theme_name == "Spiderman":
        css = """
        .stApp {
            /* This is a new, different URL for the online photo */
            background-image: url("https://i.pinimg.com/originals/c8/15/33/c815332f813a303dd5347f631122a16d.png");
            background-color: #a30000;
            background-size: contain; /* 'contain' works well for character images */
            background-position: 95% 100%; /* Position to the bottom right */
            background-repeat: no-repeat;
            background-attachment: fixed;
            color: white;
        }
        .main .block-container {
            background-color: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 2rem;
        }
        .st-emotion-cache-16txtl3 {
            background-color: rgba(0, 86, 179, 0.7);
        }
        .stButton>button {
            background-color: #0056b3;
            color: white;
        }
        """
    # --- Barbie Theme ---
    elif theme_name == "Barbie":
        css = """
        .stApp {
            background-color: #f9d9ea; /* Light Pink */
            color: #5b0d38; /* Dark Pink text */
        }
        .st-emotion-cache-16txtl3 {
            background-color: #fce4ec; /* Lighter Pink for sidebar */
        }
        .stButton>button {
            background-color: #e91e63; /* Hot Pink */
            color: white;
        }
        """
    # --- Football Theme ---
    elif theme_name == "Football":
        css = """
        .stApp {
            background-image: url("https://www.transparenttextures.com/patterns/diagmonds.png");
            background-color: #006400; /* Dark Green */
            color: white;
        }
        .st-emotion-cache-16txtl3 {
            background-color: #2e8b57; /* Sea Green */
        }
        .stButton>button {
            background-color: #ffffff;
            color: #006400;
        }
        """
    # --- Normal Dark Theme ---
    elif theme_name == "Normal Dark":
        css = """
        .stApp {
            background-color: #0e1117;
            color: white;
        }
        .st-emotion-cache-16txtl3 {
            background-color: #1c1c1c;
        }
        .stButton>button {
            background-color: #4a90e2;
            color: white;
        }
        """
    # --- Colorful Theme ---
    elif theme_name == "Colorful":
        css = """
        .stApp {
            background-image: linear-gradient(to right top, #d16ba5, #c777b9, #ba83ca, #aa8fd8, #9a9ae1, #8aa7ec, #79b3f4, #69bff8, #52cffe, #41dfff, #46eefa, #5ffbf1);
            color: #000000;
        }
        .st-emotion-cache-16txtl3 {
            background-color: rgba(255, 255, 255, 0.7);
        }
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
        }
        """
    
    # Inject the CSS into the app
    if css:
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


# --- Theme Selector in Sidebar ---
theme_list = ["Spiderman", "Barbie", "Football", "Normal Dark", "Colorful", "Default Light"]
selected_theme = st.sidebar.selectbox("Choose a theme", theme_list, key="theme_selector")

# Apply the theme if it's not the default
if selected_theme != "Default Light":
    apply_theme(selected_theme)

# =================================================================================================
# END OF THEME SELECTOR CODE
# =================================================================================================

# Your original page code (st.title, chatbot logic, etc.) starts here...
# --- CONFIGURATION ---
# (Your Gemini configuration code remains here)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error("Failed to configure the Gemini API. Please make sure your API key is set correctly in st.secrets.")
    st.stop()


# --- PAGE SETUP ---
st.set_page_config(page_title="Friendly Study Companion", page_icon="🌱")


# --- NEW: CREATIVE HEADER ---
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/3653/3653195.png", width=100) # A simple, friendly icon
with col2:
    st.title("Your Friendly Study Companion")
    st.write("A safe space to talk about study stress and well-being.")

st.divider()


# --- CHATBOT PERSONA AND INITIALIZATION ---
SYSTEM_PROMPT = """
You are a friendly, empathetic, and supportive AI companion for students. Your name is 'Pebble'.
Your purpose is to be a safe space for students to talk about their study-related stress, anxieties, and mental health challenges.
- Listen carefully and validate their feelings.
- Offer gentle, constructive advice and coping strategies (like the Pomodoro Technique, mindfulness exercises, or breaking down large tasks).
- Always be encouraging and positive.
- NEVER claim to be a real therapist or a replacement for professional help.
- If the user's problem seems serious or they mention severe distress, you MUST include the following disclaimer in your response: 
'I'm here to listen, but I'm an AI. If you're feeling overwhelmed, please consider talking to a trusted adult or a mental health professional. You are not alone.'
"""

# Initialize chat history
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[]) # Start with an empty history


# --- CHAT INTERFACE ---
# Display previous messages
# Display previous messages
# Display previous messages
for message in st.session_state.chat_session.history[1:]:
    # FIX: Check if the message is a dictionary or a Gemini object
    if isinstance(message, dict):
        role = message['role']
        text = message['parts'][0]
    else: # It's a Gemini Content object
        role = message.role
        text = message.parts[0].text

    # Set avatar and display the message
    avatar_icon = "🌱" if role == 'model' else "😊"
    with st.chat_message(name=role, avatar=avatar_icon):
        st.markdown(text)

# Welcome message with typing animation
if len(st.session_state.chat_session.history) == 0:
    # Add the system prompt to the history without displaying it
    st.session_state.chat_session.history.append({'role': 'user', 'parts': [SYSTEM_PROMPT]})
    
    welcome_message = "Hello! I'm Pebble, your friendly study companion. What's on your mind today? I'm here to listen."
    with st.chat_message(name="model", avatar="🌱"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in welcome_message.split():
            full_response += chunk + " "
            time.sleep(0.1)  # Control typing speed
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    
    # Add the welcome message to the history
    st.session_state.chat_session.history.append({'role': 'model', 'parts': [welcome_message]})


# Get user input
if user_prompt := st.chat_input("Share your thoughts here..."):
    # Add user's message to the chat display
    with st.chat_message("user", avatar="😊"):
        st.markdown(user_prompt)

    # Send the message to the Gemini model and get a response
    with st.spinner("Pebble is thinking..."):
        try:
            response = st.session_state.chat_session.send_message(user_prompt)
            # Display the AI's response
            with st.chat_message("model", avatar="🌱"):
                st.markdown(response.text)
        except Exception as e:
            st.error(f"An error occurred: {e}")