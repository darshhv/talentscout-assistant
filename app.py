import streamlit as st
import os
import re
import time
import cohere
from dotenv import load_dotenv

# --- Set Page Config (must be first Streamlit command) ---
st.set_page_config(
    page_title="TalentScout AI Hiring Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🤖"
)

# --- Load Environment Variables ---
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY") or "your-default-key-here"
co = cohere.Client(COHERE_API_KEY)

# --- Custom CSS Styling ---
st.markdown(
    """
    <style>
    /* Container */
    .stApp {
        max-width: 900px;
        margin: 1.5rem auto 3rem;
        padding: 2rem 3rem;
        background: linear-gradient(135deg, #e0eafc, #cfdef3);
        border-radius: 14px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Title */
    h1 {
        font-size: 3.4rem !important;
        font-weight: 900 !important;
        color: #1a237e !important;
        text-align: center !important;
        margin-bottom: 1rem !important;
        font-family: 'Poppins', sans-serif !important;
    }
    /* Buttons */
    .stButton > button {
        background-color: #3949ab !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 0.7rem 1.6rem !important;
        border-radius: 0.8rem !important;
        font-size: 1.1rem !important;
        transition: background-color 0.3s ease;
        border: none !important;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #303f9f !important;
        cursor: pointer;
    }
    /* Inputs & Textareas */
    textarea, input, select {
        border-radius: 0.6rem !important;
        border: 1.6px solid #3949ab !important;
        padding: 0.7rem !important;
        font-size: 1.05rem !important;
        transition: border-color 0.3s ease;
    }
    textarea:focus, input:focus, select:focus {
        outline: none !important;
        border-color: #1a237e !important;
        box-shadow: 0 0 8px #3949abaa !important;
    }
    /* Expander Header */
    .streamlit-expanderHeader {
        font-weight: 700 !important;
        color: #283593 !important;
    }
    /* Progress bar */
    .stProgress > div > div {
        background: #3949ab !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Page Title ---
st.markdown("<h1>TalentScout AI Hiring Assistant</h1>", unsafe_allow_html=True)

# --- Initialize session state ---
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.candidate_info = {}
    st.session_state.tech_questions_raw = ""
    st.session_state.tech_questions = {}
    st.session_state.answers = {}
    st.session_state.score = None
    st.session_state.grade = None
if "trigger_rerun" not in st.session_state:
    st.session_state.trigger_rerun = False

# --- Sidebar navigation ---
steps = [
    "Candidate Info 📝",
    "Technical Interview 💻",
    "Evaluation Summary 📊"
]
st.sidebar.title("Interview Process")
for i, label in enumerate(steps, 1):
    selected = (st.session_state.step == i)
    if st.sidebar.button(label, key=f"nav_{i}"):
        st.session_state.step = i
        st.session_state.trigger_rerun = True
st.sidebar.progress(st.session_state.step / len(steps))

# --- Utilities ---
def reset():
    keys = list(st.session_state.keys())
    for key in keys:
        del st.session_state[key]
    st.experimental_rerun()

def generate_questions(tech_stack, retries=3, delay=5):
    prompt = f"""
You are a technical interviewer.

A candidate has the following tech stack: {tech_stack}.

Generate 3 to 5 technical interview questions for each technology mentioned.

Format your response exactly as:

### TechnologyName
* Question 1
* Question 2
* Question 3
"""
    for attempt in range(retries):
        try:
            response = co.generate(
                model="command",
                prompt=prompt,
                max_tokens=512,
                temperature=0.7,
                k=0,
                p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop_sequences=[]
            )
            return response.generations[0].text.strip()
        except Exception as e:
            if attempt < retries - 1:
                st.warning(f"⏳ Cohere API error on attempt {attempt + 1}: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                st.error(f"❌ Cohere API failed after {retries} attempts: {e}")
                return None

def parse_questions(text):
    sections = re.split(r"\n(?=###\s*)", text)
    parsed = {}
    for sec in sections:
        lines = sec.strip().split("\n")
        if not lines:
            continue
        tech = lines[0].replace("###", "").strip()
        qs = [re.sub(r"^[*-]\s*", "", l).strip() for l in lines[1:] if l.strip()]
        if qs:
            parsed[tech] = qs
    return parsed

def evaluate_answers(qas):
    total = sum(len(v) for v in qas.values())
    answered = sum(1 for v in qas.values() for qa in v if qa.get("answer", "").strip())
    return (answered / total) * 100 if total else 0

def grade_candidate(score):
    if score >= 80:
        return "Excellent - Highly Recommended"
    elif score >= 60:
        return "Good - Recommended"
    elif score >= 40:
        return "Average - Needs Improvement"
    else:
        return "Poor - Not Recommended"

# --- Step 1: Candidate Info ---
if st.session_state.step == 1:
    st.header("📝 Step 1: Candidate Information")
    with st.form("candidate_form", clear_on_submit=False):
        col1, col2 = st.columns(2, gap="large")
        with col1:
            name = st.text_input(
                "Full Name", value=st.session_state.candidate_info.get("Full Name", "")
            )
            email = st.text_input(
                "Email Address", value=st.session_state.candidate_info.get("Email", "")
            )
            phone = st.text_input(
                "Phone Number", value=st.session_state.candidate_info.get("Phone", "")
            )
            exp = st.number_input(
                "Years of Experience",
                min_value=0,
                max_value=50,
                value=st.session_state.candidate_info.get("Years of Experience", 0),
                step=1,
            )
        with col2:
            role = st.text_input(
                "Desired Position",
                value=st.session_state.candidate_info.get("Desired Position", ""),
            )
            location = st.text_input(
                "Current Location",
                value=st.session_state.candidate_info.get("Current Location", ""),
            )
            tech_stack = st.text_area(
                "Tech Stack (comma-separated)",
                value=st.session_state.candidate_info.get("Tech Stack", ""),
                height=120,
                placeholder="E.g., Python, React, Docker, AWS",
            )
        submitted = st.form_submit_button("👉 Generate Interview Questions")

    if submitted:
        if not name.strip() or not email.strip() or not phone.strip() or not tech_stack.strip():
            st.error("⚠️ Please fill all required fields before generating questions!")
        else:
            st.session_state.candidate_info = {
                "Full Name": name.strip(),
                "Email": email.strip(),
                "Phone": phone.strip(),
                "Years of Experience": exp,
                "Desired Position": role.strip(),
                "Current Location": location.strip(),
                "Tech Stack": tech_stack.strip(),
            }
            with st.spinner("🧠 Generating technical questions..."):
                questions_text = generate_questions(tech_stack)
            if questions_text:
                st.session_state.tech_questions_raw = questions_text
                st.session_state.tech_questions = parse_questions(questions_text)
                st.session_state.answers = {
                    tech: [{"question": q, "answer": ""} for q in qs]
                    for tech, qs in st.session_state.tech_questions.items()
                }
                st.success("✅ Questions generated successfully! Proceed to the next step.")
                st.session_state.step = 2
                st.session_state.trigger_rerun = True
            else:
                st.error("❌ Failed to generate questions. Please try again later.")

# --- Step 2: Technical Interview ---
elif st.session_state.step == 2:
    st.header("💻 Step 2: Technical Interview Questions")
    with st.form("answers_form"):
        for tech, qas in st.session_state.answers.items():
            with st.expander(f"💡 {tech} ({len(qas)} questions)", expanded=False):
                for i, qa in enumerate(qas):
                    st.markdown(f"**Q{i + 1}. {qa['question']}**")
                    st.session_state.answers[tech][i]["answer"] = st.text_area(
                        f"Your Answer for Q{i + 1}",
                        value=qa["answer"],
                        height=110,
                        key=f"{tech}_{i}",
                        placeholder="Type your answer here...",
                    )
        submitted = st.form_submit_button("✅ Submit Answers")

    if submitted:
        score = evaluate_answers(st.session_state.answers)
        grade = grade_candidate(score)
        st.session_state.score = score
        st.session_state.grade = grade
        st.success(f"🎯 Your Score: {score:.2f}% — {grade}")
        st.session_state.step = 3
        st.session_state.trigger_rerun = True

# --- Step 3: Evaluation Summary ---
elif st.session_state.step == 3:
    st.header("📊 Step 3: Evaluation Summary")
    st.balloons()
    st.success("✅ Interview Completed!")

    st.markdown(f"### Candidate: **{st.session_state.candidate_info.get('Full Name', 'N/A')}**")
    st.markdown(f"**Overall Score:** {st.session_state.score:.2f}%")
    st.markdown(f"**Final Grade:** {st.session_state.grade}")

    st.markdown("### Scores by Technology")
    for tech, qas in st.session_state.answers.items():
        tech_score = evaluate_answers({tech: qas})
        tech_grade = grade_candidate(tech_score)
        st.markdown(f"- **{tech}**: {tech_score:.2f}% — {tech_grade}")

    st.markdown("---")
    st.markdown("### Review Answers")
    for tech, qas in st.session_state.answers.items():
        with st.expander(f"🔍 {tech} Answers", expanded=False):
            for i, qa in enumerate(qas):
                st.markdown(f"**Q{i + 1}. {qa['question']}**")
                st.markdown(f"**Answer:** {qa['answer'] or '_No answer provided_'}")

    if st.button("🔄 Restart Interview"):
        reset()

# --- Manual Rerun Trigger ---
if st.session_state.get("trigger_rerun"):
    st.session_state.trigger_rerun = False
    st.experimental_rerun()
