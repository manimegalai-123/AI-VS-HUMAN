import streamlit as st
import time
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase setup
if not firebase_admin._apps:
    cred = credentials.Certificate("finalround1.json")  # Replace with your Firebase credentials
    firebase_admin.initialize_app(cred)
db = firestore.client()

# List of current affairs questions
questions = [
    ("India hosted the G20 Summit in 2023.", "Elon Musk acquired Twitter in 2022.", "NASA landed a man on Mars in 2023."),
    ("The FIFA World Cup 2022 was won by Argentina.", "The UK left the European Union in 2021.", "ChatGPT was launched in 2020."),
    ("India's Chandrayaan-3 successfully landed on the Moon.", "Bitcoin became a legal tender in El Salvador in 2021.", "The Olympics 2024 is hosted by Japan."),
    ("The COVID-19 pandemic was officially declared over by WHO in 2023.", "Apple released the iPhone 15 in 2023.", "Russia became a NATO member in 2022."),
    ("OpenAI introduced GPT-4 in 2023.", "The 2024 US Presidential Election was held in March.", "Paris will host the 2024 Olympics."),
]

fake_statements = [
    "NASA landed a man on Mars in 2023.",
    "The UK left the European Union in 2021.",
    "The Olympics 2024 is hosted by Japan.",
    "Russia became a NATO member in 2022.",
    "The 2024 US Presidential Election was held in March.",
]

# Initialize session state variables
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "time_left" not in st.session_state:
    st.session_state.time_left = 30
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "user_choice" not in st.session_state:
    st.session_state.user_choice = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "name_exists" not in st.session_state:
    st.session_state.name_exists = False

st.title("🎭 Fact or Fiction: Find the Fake Statement!")

# Show leaderboard
if st.sidebar.button("Show Leaderboard"):
    st.sidebar.subheader("🏆 Leaderboard")
    scores_ref = db.collection("leaderboard").order_by("score", direction=firestore.Query.DESCENDING)
    scores = scores_ref.stream()
    for score in scores:
        data = score.to_dict()
        st.sidebar.write(f"{data['name']}: {data['score']}")

# Player name input (before game starts)
if not st.session_state.game_started:
    st.session_state.player_name = st.text_input("Enter your name:")
    
    if st.button("Start Game"):
        if st.session_state.player_name:
            player_ref = db.collection("leaderboard").document(st.session_state.player_name)
            if player_ref.get().exists:
                st.session_state.name_exists = True
                st.warning("This name already exists! Please enter a different name.")
            else:
                st.session_state.game_started = True
                st.session_state.name_exists = False
                st.rerun()
    
    st.stop()

# If game is over, save score and display final score
if st.session_state.game_over:
    st.title("🎉 Game Over!")
    st.subheader(f"{st.session_state.player_name}")
    st.subheader(f"Final Score: {st.session_state.score}/{len(questions)}")
    
    # Save score in Firebase
    player_ref = db.collection("leaderboard").document(st.session_state.player_name)
    player_data = player_ref.get()

    if player_data.exists:
        existing_score = player_data.to_dict().get("score", 0)
        if st.session_state.score > existing_score:
            player_ref.set({
                "name": st.session_state.player_name,
                "score": st.session_state.score
            })
    else:
        player_ref.set({
            "name": st.session_state.player_name,
            "score": st.session_state.score
        })

    st.stop()

# Layout setup
col1, col2 = st.columns([1, 1])

# Left side: Player Info, Score, Timer
with col1:
    st.subheader("Player Info")
    st.write(f"👤 Name: {st.session_state.player_name}")
    st.write(f"🏆 Score: {st.session_state.score}/{len(questions)}")
    timer_placeholder = st.empty()
    st.progress((st.session_state.question_index + 1) / len(questions))

# Right side: Questions
with col2:
    st.subheader(f"Question {st.session_state.question_index + 1} of {len(questions)}")
    question_set = questions[st.session_state.question_index]
    fake_answer = fake_statements[st.session_state.question_index]
    st.session_state.user_choice = st.radio("Which one is fake?", question_set, index=None)

# Timer function
def countdown():
    for i in range(st.session_state.time_left, 0, -1):
        if st.session_state.submitted:
            return
        timer_placeholder.warning(f"⏳ Time Left: {i} seconds")
        time.sleep(1)
        st.session_state.time_left -= 1
        st.rerun()
    if not st.session_state.submitted:
        st.session_state.submitted = True
        next_question()

# Function to go to the next question
def next_question():
    if st.session_state.user_choice == fake_answer:
        st.session_state.score += 1
        st.success("✅ Correct! That was the fake statement.")
    elif st.session_state.user_choice is not None:
        st.error(f"❌ Wrong! The fake statement was: '{fake_answer}'.")

    # Move to next question or end game
    if st.session_state.question_index < len(questions) - 1:
        st.session_state.question_index += 1
        st.session_state.time_left = 30
        st.session_state.user_choice = None
        st.session_state.submitted = False
        st.rerun()
    else:
        st.session_state.game_over = True
        st.rerun()

if st.button("Submit Answer"):
    st.session_state.submitted = True
    next_question()

# Start countdown if answer not submitted
if not st.session_state.submitted:
    countdown()
