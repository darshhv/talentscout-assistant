import streamlit as st
import os
import re
import cohere
import time
from dotenv import load_dotenv
from io import StringIO

# Page must start with config
st.set_page_config(page_title="🎯 TalentScout AI", layout="wide", initial_sidebar_state="expanded")

# Load environment
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY") or "your-cohere-key"
co = cohere.Client(COHERE_API_KEY)

# ---- Custom Styling ----
st.markdown("""
    <style>
    body { font-family: 'Poppins', sans-serif; }
    .title { font-size: 3rem; font-weight: 800; color: #1a237e; text-align: center; }
    .stApp { background: linear-gradient(120deg, #fdfbfb, #ebedee); padding: 1rem; }
    .question-card { background: #fff; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 14px rgba(0,0,0,0.1); margin-bottom: 1rem; }
    .metric-card { border-left: 6px solid #3949ab; padding: 1rem; margin-bottom: 1rem; background: #f1f3f4; border-radius: 8px; }
    .feedback { color: green; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>TalentScout AI Hiring Assistant</div>", unsafe_allow_html=True)

# ---- Session State Init ----
if 'step' not in st.session_state:
    st.session_state.update({
        'step': 1,
        'candidate': {},
        'raw_questions': "",
        'questions': {},
        'answers': {},
        'score': None,
        'grade': None,
        'feedback': {},
    })

# ---- Helper Functions ----
def generate_questions(tech_stack):
    prompt = f"""
You are a technical interviewer.
A candidate has the tech stack: {tech_stack}.
Generate 3 to 5 interview questions per technology.
Format as:
### Tech
* Question 1
* Question 2
    """
    try:
        res = co.generate(prompt=prompt, model="command", max_tokens=512)
        return res.generations[0].text.strip()
    except Exception as e:
        st.error(f"API Error: {e}")
        return ""

def parse_questions(text):
    tech_blocks = re.split(r"\n(?=### )", text)
    parsed = {}
    for block in tech_blocks:
        lines = block.strip().split('\n')
        if not lines: continue
        tech = lines[0].replace('###', '').strip()
        qs = [re.sub(r"^[*-]\s*", "", q).strip() for q in lines[1:] if q.strip()]
        if qs: parsed[tech] = qs
    return parsed

def evaluate(answers):
    total, filled = 0, 0
    for qlist in answers.values():
        for qa in qlist:
            total += 1
            if qa['answer'].strip(): filled += 1
    score = (filled / total) * 100 if total else 0
    grade = ("Excellent" if score >= 80 else
             "Good" if score >= 60 else
             "Average" if score >= 40 else
             "Poor")
    return score, grade

def give_feedback(answer):
    if not answer.strip(): return "✍ No answer provided."
    return "✅ Looks good! Add examples or code if possible."

# ---- Sidebar Navigation ----
st.sidebar.title("🧭 Navigation")
st.session_state.step = st.sidebar.radio("Choose Stage", [1, 2, 3], format_func=lambda x: ["📝 Info", "💻 Interview", "📊 Summary"][x-1])

# ---- Step 1: Info & Upload ----
if st.session_state.step == 1:
    with st.form("form_info"):
        st.subheader("📝 Candidate Information")
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        resume = st.file_uploader("📄 Upload Resume (optional)", type=["txt", "pdf"])
        tech_stack = st.text_input("Tech Stack (comma-separated)")
        submit = st.form_submit_button("👉 Generate Questions")

    if submit:
        st.session_state.candidate = {"name": name, "email": email, "tech_stack": tech_stack}
        with st.spinner("Generating interview questions..."):
            text = generate_questions(tech_stack)
            parsed = parse_questions(text)
            st.session_state.raw_questions = text
            st.session_state.questions = parsed
            st.session_state.answers = {
                tech: [{"question": q, "answer": ""} for q in qs]
                for tech, qs in parsed.items()
            }
            st.success("✅ Questions Ready! Move to next step.")

# ---- Step 2: Answer Questions ----
elif st.session_state.step == 2:
    st.subheader("💻 Technical Interview")
    with st.form("form_questions"):
        for tech, qlist in st.session_state.answers.items():
            st.markdown(f"### 🔧 {tech}")
            for i, qa in enumerate(qlist):
                st.markdown(f"<div class='question-card'><b>Q{i+1}: {qa['question']}</b>", unsafe_allow_html=True)
                key = f"{tech}_{i}"
                st.session_state.answers[tech][i]['answer'] = st.text_area("Answer", value=qa['answer'], key=key)
                st.markdown("</div>", unsafe_allow_html=True)
        done = st.form_submit_button("✅ Submit Answers")

    if done:
        score, grade = evaluate(st.session_state.answers)
        feedback = {
            tech: [give_feedback(qa['answer']) for qa in qlist]
            for tech, qlist in st.session_state.answers.items()
        }
        st.session_state.score, st.session_state.grade = score, grade
        st.session_state.feedback = feedback
        st.success(f"🎯 Score: {score:.2f}% — {grade}")

# ---- Step 3: Summary ----
elif st.session_state.step == 3:
    st.subheader("📊 Evaluation Summary")
    c1, c2 = st.columns(2)
    c1.metric("Total Score", f"{st.session_state.score:.1f}%")
    c2.metric("Grade", st.session_state.grade)

    for tech, qlist in st.session_state.answers.items():
        st.markdown(f"### 🧠 {tech}")
        for i, qa in enumerate(qlist):
            st.markdown(f"**Q{i+1}: {qa['question']}**")
            st.markdown(f"**Your Answer:** {qa['answer'] or '_Not answered_'}")
            st.markdown(f"<span class='feedback'>{st.session_state.feedback[tech][i]}</span>", unsafe_allow_html=True)

    if st.button("🔁 Restart"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()

# ---- Footer ----
st.markdown("""
---
*Built with ❤️ by Darshan Reddy — 2025*
""")
