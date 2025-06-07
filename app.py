import streamlit as st
from textblob import TextBlob

# Dummy functions for translation & sentiment - replace with actual implementations
def translate_text(text, lang="en"):
    # placeholder: pretend translation is the same text
    return text

def sentiment_analysis(text):
    # Basic sentiment polarity from TextBlob (range -1 to 1)
    return TextBlob(text).sentiment.polarity

def evaluate_answers(answers):
    # Score based on how many questions answered (simple)
    total = 0
    answered = 0
    for tech in answers:
        qas = answers[tech]
        total += len(qas)
        answered += sum(1 for qa in qas if qa.get("answer","").strip())
    return (answered / total) * 100 if total > 0 else 0

def grade_candidate(score):
    if score > 90: return "A+ (Excellent)"
    if score > 75: return "A (Very Good)"
    if score > 50: return "B (Good)"
    if score > 30: return "C (Average)"
    return "D (Needs Improvement)"

def recommend_jobs_and_upskill(score, techs):
    # Dummy recommendation logic
    if score > 85:
        return "Senior Developer", "Advanced Algorithms, System Design"
    elif score > 60:
        return "Mid-Level Developer", "Data Structures, Coding Practice"
    else:
        return "Junior Developer", "Basic Programming Skills"

# Initialize session state defaults
if "step" not in st.session_state:
    st.session_state.step = 1
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = {}
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "translated_answers" not in st.session_state:
    st.session_state.translated_answers = {}
if "sentiment_scores" not in st.session_state:
    st.session_state.sentiment_scores = {}
if "score" not in st.session_state:
    st.session_state.score = 0
if "grade" not in st.session_state:
    st.session_state.grade = ""
if "job_recommendation" not in st.session_state:
    st.session_state.job_recommendation = ""
if "upskill_recommendation" not in st.session_state:
    st.session_state.upskill_recommendation = ""

def reset_all():
    st.session_state.step = 1
    st.session_state.candidate_info = {}
    st.session_state.answers = {}
    st.session_state.translated_answers = {}
    st.session_state.sentiment_scores = {}
    st.session_state.score = 0
    st.session_state.grade = ""
    st.session_state.job_recommendation = ""
    st.session_state.upskill_recommendation = ""

# --- Page config ---
st.set_page_config(
    page_title="AI Hiring Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- CSS styles for a fresh modern card UI ---
st.markdown("""
<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
      Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
    background-color: #f5f7fa;
    color: #20232a;
    margin: 0;
    padding: 0;
}
h1, h2, h3, h4 {
    font-weight: 700;
    color: #222;
}
.step-nav {
    display: flex;
    justify-content: center;
    margin-bottom: 30px;
    gap: 2rem;
}
.step-nav button {
    background-color: #ddd;
    border: none;
    border-radius: 25px;
    padding: 12px 25px;
    font-weight: 600;
    font-size: 18px;
    cursor: pointer;
    color: #555;
    transition: background-color 0.3s ease, color 0.3s ease;
    box-shadow: 0 2px 6px rgb(0 0 0 / 0.1);
}
.step-nav button.active {
    background: linear-gradient(135deg, #4f93ff, #2a6fff);
    color: white;
    box-shadow: 0 4px 12px rgb(46 102 255 / 0.5);
}
.step-card {
    background: white;
    padding: 2rem 2.5rem;
    border-radius: 14px;
    box-shadow: 0 10px 20px rgb(0 0 0 / 0.07);
    margin-bottom: 3rem;
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
}
.input-label {
    font-weight: 600;
    font-size: 16px;
    margin-bottom: 6px;
    display: block;
    color: #444;
}
input[type=text], input[type=email], input[type=tel], select, textarea {
    width: 100%;
    padding: 12px 14px;
    font-size: 16px;
    border: 1.8px solid #ccc;
    border-radius: 10px;
    margin-bottom: 20px;
    transition: border-color 0.3s ease;
}
input[type=text]:focus, input[type=email]:focus, input[type=tel]:focus, select:focus, textarea:focus {
    outline: none;
    border-color: #4f93ff;
    box-shadow: 0 0 6px #4f93ffaa;
}
button.primary-btn {
    background: #4f93ff;
    color: white;
    border: none;
    font-weight: 700;
    padding: 14px 30px;
    border-radius: 30px;
    font-size: 20px;
    cursor: pointer;
    transition: background 0.3s ease;
    box-shadow: 0 6px 14px rgb(79 147 255 / 0.6);
    margin-top: 10px;
}
button.primary-btn:hover {
    background: #2a6fff;
    box-shadow: 0 8px 18px rgb(42 111 255 / 0.8);
}
.answer-block {
    background: #f0f4ff;
    border-radius: 12px;
    padding: 15px 20px;
    margin-bottom: 15px;
    box-shadow: inset 0 0 4px #9abaff;
}
.sentiment-emoji {
    font-size: 22px;
    vertical-align: middle;
    margin-right: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- Horizontal step navigation ---
def step_button(step_num, label):
    active_class = "active" if st.session_state.step == step_num else ""
    return f'<button class="{active_class}" onclick="window.location.href=\'#{step_num}\'">{label}</button>'

st.markdown(
    f"""
    <div class="step-nav" role="navigation" aria-label="Steps Navigation">
        <button class="{'active' if st.session_state.step==1 else ''}" onclick="window.location.href='#1'">📝 Candidate Info</button>
        <button class="{'active' if st.session_state.step==2 else ''}" onclick="window.location.href='#2'">❓ Interview</button>
        <button class="{'active' if st.session_state.step==3 else ''}" onclick="window.location.href='#3'">📊 Summary</button>
    </div>
    """,
    unsafe_allow_html=True,
)

# JS to allow button clicks to update Streamlit state is tricky without advanced tricks
# So add simple buttons below for step navigation:
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📝 Go to Step 1 - Candidate Info"):
        st.session_state.step = 1
with col2:
    if st.button("❓ Go to Step 2 - Interview"):
        st.session_state.step = 2
with col3:
    if st.button("📊 Go to Step 3 - Summary"):
        st.session_state.step = 3

# --- Step 1: Candidate Info ---
if st.session_state.step == 1:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.title("📝 Candidate Information")

    with st.form("candidate_info_form", clear_on_submit=False):
        cols = st.columns([1,1])
        with cols[0]:
            full_name = st.text_input("Full Name", value=st.session_state.candidate_info.get("Full Name", ""))
            email = st.text_input("Email Address", value=st.session_state.candidate_info.get("Email", ""))
            phone = st.text_input("Phone Number", value=st.session_state.candidate_info.get("Phone", ""))
        with cols[1]:
            experience = st.number_input("Years of Experience", min_value=0, max_value=50,
                                         value=st.session_state.candidate_info.get("Years of Experience", 0))
            position = st.text_input("Position Applying For", value=st.session_state.candidate_info.get("Desired Position", ""))
            location = st.text_input("Current Location", value=st.session_state.candidate_info.get("Current Location", ""))
        tech_stack = st.text_input("Technical Stack (comma separated)", value=st.session_state.candidate_info.get("Tech Stack", ""))

        submitted = st.form_submit_button("Save & Proceed to Interview")
        if submitted:
            # Save info to session state
            st.session_state.candidate_info = {
                "Full Name": full_name.strip(),
                "Email": email.strip(),
                "Phone": phone.strip(),
                "Years of Experience": experience,
                "Desired Position": position.strip(),
                "Current Location": location.strip(),
                "Tech Stack": tech_stack.strip(),
            }
            st.success("Candidate info saved. Proceed to Step 2.")
            st.session_state.step = 2
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- Step 2: Interview Questions ---
elif st.session_state.step == 2:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.title("❓ Technical Interview Questions")

    # For demo, dummy tech stacks and questions
    techs = [t.strip() for t in st.session_state.candidate_info.get("Tech Stack", "").split(",") if t.strip()]
    if not techs:
        st.warning("Please add your Technical Stack in Step 1 to load interview questions.")
        if st.button("Go Back to Step 1"):
            st.session_state.step = 1
            st.experimental_rerun()
    else:
        if "answers" not in st.session_state or not st.session_state.answers:
            # Initialize answers dict with 3 dummy questions per tech
            st.session_state.answers = {
                tech: [
                    {"question": f"What is {tech} and why is it important?", "answer": ""},
                    {"question": f"Explain a key challenge you faced with {tech}.", "answer": ""},
                    {"question": f"How do you optimize performance in {tech}?", "answer": ""},
                ] for tech in techs
            }

        with st.form("interview_form"):
            for tech in techs:
                st.markdown(f"### 🛠️ {tech} Questions")
                for i, qa in enumerate(st.session_state.answers[tech]):
                    answer = st.text_area(f"Q{i+1}. {qa['question']}", value=qa.get("answer",""), key=f"{tech}_q{i}")
                    st.session_state.answers[tech][i]["answer"] = answer

            if st.form_submit_button("Submit Answers and Evaluate"):
                # Translate & sentiment
                translated = {}
                sentiments = {}
                for tech in st.session_state.answers:
                    translated[tech] = []
                    sentiments[tech] = []
                    for qa in st.session_state.answers[tech]:
                        text = qa.get("answer", "").strip()
                        if text:
                            t_text = translate_text(text, "en")
                        else:
                            t_text = ""
                        translated[tech].append(t_text)
                        sentiments[tech].append(sentiment_analysis(t_text))
                st.session_state.translated_answers = translated
                st.session_state.sentiment_scores = sentiments

                score = evaluate_answers(st.session_state.answers)
                st.session_state.score = round(score, 2)
                st.session_state.grade = grade_candidate(score)

                job, upskill = recommend_jobs_and_upskill(score, techs)
                st.session_state.job_recommendation = job
                st.session_state.upskill_recommendation = upskill

                st.success("✅ Answers evaluated. Proceeding to summary...")
                st.session_state.step = 3
                st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Step 3: Summary & Recommendations ---
elif st.session_state.step == 3:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.title("📊 Evaluation Summary")

    info = st.session_state.candidate_info
    st.subheader("👤 Candidate Details")
    st.markdown(f"""
    - **Name:** {info.get('Full Name', '')}
    - **Email:** {info.get('Email', '')}
    - **Phone:** {info.get('Phone', '')}
    - **Experience:** {info.get('Years of Experience', '')} years
    - **Position Applied:** {info.get('Desired Position', '')}
    - **Location:** {info.get('Current Location', '')}
    - **Tech Stack:** {info.get('Tech Stack', '')}
    """)

    st.subheader("🏆 Interview Score & Grade")
    st.markdown(f"<h2 style='color:#2a6fff;'>{st.session_state.score}% — {st.session_state.grade}</h2>", unsafe_allow_html=True)

    st.subheader("💼 Job Recommendation")
    st.info(f"**Suggested Role:** {st.session_state.job_recommendation}")
    st.info(f"**Upskill Recommendations:** {st.session_state.upskill_recommendation}")

    st.subheader("📝 Detailed Answers & Sentiment Analysis")

    for tech, qas in st.session_state.answers.items():
        with st.expander(f"{tech} ({len(qas)} Questions)"):
            for i, qa in enumerate(qas):
                answer = qa.get("answer", "").strip()
                translated = st.session_state.translated_answers.get(tech, [""] * len(qas))[i]
                sentiment = st.session_state.sentiment_scores.get(tech, [0] * len(qas))[i]
                if sentiment > 0.3:
                    emoji = "😊"
                    sentiment_desc = "Positive"
                elif sentiment < -0.3:
                    emoji = "😟"
                    sentiment_desc = "Negative"
                else:
                    emoji = "😐"
                    sentiment_desc = "Neutral"
                st.markdown(f"""
                <div class="answer-block">
                <strong>Q{i+1}. {qa['question']}</strong><br>
                <em>Answer:</em> {answer or "*No answer provided*"}<br>
                <em>Translated:</em> {translated or "*N/A*"}<br>
                <span class="sentiment-emoji">{emoji}</span><em>Sentiment:</em> {sentiment_desc} ({sentiment:.2f})
                </div>
                """, unsafe_allow_html=True)

    if st.button("🔄 Restart Interview Process"):
        reset_all()
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
