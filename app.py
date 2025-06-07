import streamlit as st
import requests
import os
import re
from dotenv import load_dotenv

# Load HuggingFace Token
load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

# Page config & style
st.set_page_config(page_title="TalentScout AI Hiring Assistant", layout="wide")
st.markdown("""
<style>
.stApp {
    max-width: 900px;
    margin: auto;
    padding: 1rem 2rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f7f9fc;
}
.stButton>button {
    background-color: #4CAF50;
    color: white;
    font-weight: 600;
    padding: 0.5rem 1rem;
    border-radius: 0.4rem;
}
.stButton>button:hover {
    background-color: #45a049;
}
textarea, input {
    border-radius: 0.3rem !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state defaults
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'candidate_info' not in st.session_state:
    st.session_state.candidate_info = {}
if 'tech_questions_raw' not in st.session_state:
    st.session_state.tech_questions_raw = ""
if 'tech_questions' not in st.session_state:
    st.session_state.tech_questions = {}
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'score' not in st.session_state:
    st.session_state.score = None
if 'grade' not in st.session_state:
    st.session_state.grade = None
if 'trigger_rerun' not in st.session_state:
    st.session_state.trigger_rerun = False

# Sidebar Navigation
steps = ["Candidate Info 📝", "Technical Interview 💻", "Evaluation Summary 📊"]
st.sidebar.title("Interview Process")
for i, s in enumerate(steps, 1):
    if st.sidebar.button(s, key=f"nav_{i}"):
        st.session_state.step = i
        st.session_state.trigger_rerun = True

st.progress(st.session_state.step / len(steps))

# Reset function
def reset():
    keys_to_clear = [
        'step', 'candidate_info', 'tech_questions_raw', 'tech_questions',
        'answers', 'score', 'grade', 'trigger_rerun'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.experimental_rerun()

# --- Core Functions ---
def generate_questions(tech_stack):
    prompt = f"""
You're a technical interviewer.

A candidate has listed the following tech stack: {tech_stack}.

Generate 3 to 5 technical interview questions for each technology mentioned.

Respond in this format:
### TechnologyName
* Question 1
* Question 2
* Question 3
"""
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 256, "temperature": 0.7}
    }
    res = requests.post(API_URL, headers=headers, json=payload)
    if res.status_code == 200:
        try:
            return res.json()[0]['generated_text'].strip()
        except Exception:
            st.error("Error parsing response from model.")
            return None
    else:
        st.error(f"API error: {res.status_code} - {res.text}")
        return None

def parse_questions(text):
    lines = text.split('\n')
    sections = re.split(r'\n(?=###\s*)', "\n".join(lines))
    parsed = {}
    for sec in sections:
        lines = sec.strip().split('\n')
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
    with st.form("candidate_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=st.session_state.candidate_info.get("Full Name", ""))
            email = st.text_input("Email Address", value=st.session_state.candidate_info.get("Email", ""))
            phone = st.text_input("Phone Number", value=st.session_state.candidate_info.get("Phone", ""))
            exp = st.number_input("Years of Experience", 0, 50, value=st.session_state.candidate_info.get("Years of Experience", 0))
        with col2:
            role = st.text_input("Desired Position", value=st.session_state.candidate_info.get("Desired Position", ""))
            location = st.text_input("Current Location", value=st.session_state.candidate_info.get("Current Location", ""))
            tech_stack = st.text_area("Tech Stack (comma-separated)", value=st.session_state.candidate_info.get("Tech Stack", ""))
        submitted = st.form_submit_button("👉 Generate Interview Questions")

    if submitted:
        if not name or not email or not phone or not tech_stack.strip():
            st.error("⚠️ Please fill all required fields!")
        else:
            st.session_state.candidate_info = {
                "Full Name": name, "Email": email, "Phone": phone,
                "Years of Experience": exp, "Desired Position": role,
                "Current Location": location, "Tech Stack": tech_stack
            }
            with st.spinner("🧠 Generating questions..."):
                questions_text = generate_questions(tech_stack)
            if questions_text:
                st.session_state.tech_questions_raw = questions_text
                st.session_state.tech_questions = parse_questions(questions_text)
                st.session_state.answers = {
                    tech: [{"question": q, "answer": ""} for q in qs]
                    for tech, qs in st.session_state.tech_questions.items()
                }
                st.success("✅ Questions generated! Moving to next step...")
                st.session_state.step = 2
                st.session_state.trigger_rerun = True
            else:
                st.error("❌ Failed to generate questions. Try again later.")

# --- Step 2: Technical Interview ---
elif st.session_state.step == 2:
    st.header("💻 Step 2: Technical Interview Questions")
    with st.form("answers_form"):
        for tech, qas in st.session_state.answers.items():
            with st.expander(f"💡 {tech} ({len(qas)} questions)", expanded=False):
                for i, qa in enumerate(qas):
                    st.markdown(f"**Q{i+1}. {qa['question']}**")
                    st.session_state.answers[tech][i]["answer"] = st.text_area(
                        f"Your Answer for Q{i+1}", value=qa["answer"], height=100, key=f"{tech}_{i}"
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

# --- Step 3: Summary ---
elif st.session_state.step == 3:
    st.header("📊 Step 3: Evaluation Summary")
    st.balloons()
    st.success("✅ Interview Completed!")

    st.markdown(f"### Candidate: **{st.session_state.candidate_info.get('Full Name')}**")
    st.markdown(f"**Score:** {st.session_state.score:.2f}%")
    st.markdown(f"**Grade:** {st.session_state.grade}")

    st.markdown("### Scores by Technology")
    for tech, qas in st.session_state.answers.items():
        tech_score = evaluate_answers({tech: qas})
        tech_grade = grade_candidate(tech_score)
        st.markdown(f"- **{tech}**: {tech_score:.2f}% — {tech_grade}")

    st.markdown("---\n### Review Answers")
    for tech, qas in st.session_state.answers.items():
        with st.expander(f"🔍 {tech} Answers"):
            for i, qa in enumerate(qas):
                st.markdown(f"**Q{i+1}. {qa['question']}**")
                st.markdown(f"**Answer:** {qa['answer'] or '_No answer provided_'}")

    if st.button("🔄 Restart Interview"):
        reset()

# --- Safe rerun trigger at the end ---
if st.session_state.get("trigger_rerun"):
    st.session_state.trigger_rerun = False
    st.experimental_rerun()
