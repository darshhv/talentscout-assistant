import streamlit as st
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

st.set_page_config(page_title="TalentScout AI Hiring Assistant", layout="wide")
st.markdown(
    """
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
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        color: white;
    }
    .stTextInput>div>input, .stNumberInput>div>input, textarea {
        border-radius: 0.3rem;
        border: 1px solid #ccc;
        padding: 0.5rem;
    }
    .css-1lcbmhc {
        padding-bottom: 3rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Steps navigation in sidebar ---
steps = ["Candidate Info 📝", "Technical Interview 💻", "Evaluation Summary 📊"]
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.candidate_info = {}
    st.session_state.tech_questions_raw = ""
    st.session_state.tech_questions = {}
    st.session_state.answers = {}
    st.session_state.score = None
    st.session_state.grade = None

st.sidebar.title("Interview Process")
for i, s in enumerate(steps, 1):
    if st.sidebar.button(s, key=f"nav_{i}"):
        st.session_state.step = i
        st.experimental_rerun()

# Show progress bar
st.progress(min(st.session_state.step / len(steps), 1.0))

# Reset function
def reset():
    st.session_state.clear()
    st.experimental_rerun()

# --- Helper functions (same as before) ---
def generate_questions(tech_stack):
    prompt = f"""
You're a technical interviewer.

A candidate has listed the following tech stack: {tech_stack}.

Generate 3 to 5 technical interview questions for each technology mentioned to assess the candidate's skills.

Respond in a clear format:
### TechnologyName
* Question 1
* Question 2
* Question 3
"""
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "do_sample": True
        }
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data[0]['generated_text'].strip()
    else:
        return None

def parse_questions(text):
    lines = text.split('\n')
    clean_lines = []
    started = False
    for line in lines:
        if line.strip().startswith("###"):
            started = True
        if started:
            clean_lines.append(line)
    text = "\n".join(clean_lines)

    sections = re.split(r'\n(?=###\s*[^\n]+)', text)
    parsed = {}
    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue
        header = lines[0].strip()
        tech_match = re.match(r'###\s*(.+)', header)
        tech = tech_match.group(1).strip() if tech_match else "General"

        questions = []
        for line in lines[1:]:
            q = re.sub(r'^\s*[*\-]\s*', '', line).strip()
            if q:
                questions.append(q)
        if questions:
            parsed[tech] = questions
    return parsed

def evaluate_answers(questions_answers):
    total_questions = 0
    total_score = 0
    for tech, qas in questions_answers.items():
        for qa in qas:
            total_questions += 1
            answer = qa.get("answer", "").strip()
            if answer:
                total_score += 1
    return (total_score / total_questions) * 100 if total_questions else 0

def grade_candidate(score):
    if score >= 80:
        return "Excellent - Highly Recommended"
    elif score >= 60:
        return "Good - Recommended"
    elif score >= 40:
        return "Average - Needs Improvement"
    else:
        return "Poor - Not Recommended"

# --- Main app UI ---

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
                "Full Name": name,
                "Email": email,
                "Phone": phone,
                "Years of Experience": exp,
                "Desired Position": role,
                "Current Location": location,
                "Tech Stack": tech_stack
            }
            with st.spinner("🧠 Generating technical interview questions..."):
                questions_text = generate_questions(tech_stack)
            if questions_text:
                st.session_state.tech_questions_raw = questions_text
                st.session_state.tech_questions = parse_questions(questions_text)
                st.session_state.answers = {
                    tech: [{"question": q, "answer": ""} for q in qs]
                    for tech, qs in st.session_state.tech_questions.items()
                }
                st.success("✅ Questions generated successfully! Proceed to next step.")
                st.session_state.step = 2
                st.experimental_rerun()
            else:
                st.error("❌ Failed to generate questions. Try again later.")

elif st.session_state.step == 2:
    st.header("💻 Step 2: Technical Interview Questions")
    st.info("Fill in your answers below. You can expand each technology section.")

    with st.form("answers_form"):
        for tech, qas in st.session_state.answers.items():
            with st.expander(f"💡 {tech} ({len(qas)} questions)", expanded=False):
                for i, qa in enumerate(qas):
                    st.markdown(f"**Q{i+1}. {qa['question']}**")
                    ans = st.text_area(
                        label=f"Your Answer for Q{i+1}",
                        value=qa['answer'],
                        key=f"{tech}_ans_{i}",
                        height=100
                    )
                    st.session_state.answers[tech][i]["answer"] = ans
        submit_answers = st.form_submit_button("✅ Submit Answers")

    if submit_answers:
        score = evaluate_answers(st.session_state.answers)
        st.session_state.score = score
        st.session_state.grade = grade_candidate(score)
        st.success(f"🎉 Answers submitted! Your score is {score:.2f}% ({st.session_state.grade})")
        st.session_state.step = 3
        st.experimental_rerun()

elif st.session_state.step == 3:
    st.header("📊 Step 3: Evaluation Summary")
    st.balloons()
    st.success("🎯 Interview Completed Successfully!")

    st.markdown(f"### Candidate: **{st.session_state.candidate_info.get('Full Name', '')}**")
    st.markdown(f"**Overall Score:** {st.session_state.score:.2f}%")
    st.markdown(f"**Overall Grade:** {st.session_state.grade}")

    st.markdown("### Scores by Technology")
    for tech, qas in st.session_state.answers.items():
        answered = sum(1 for qa in qas if qa["answer"].strip())
        total = len(qas)
        tech_score = (answered / total) * 100 if total else 0
        tech_grade = grade_candidate(tech_score)
        st.markdown(f"- **{tech}:** {tech_score:.2f}% — {tech_grade}")

    st.markdown("---")
    st.markdown("### Review Answers")
    for tech, qas in st.session_state.answers.items():
        with st.expander(f"🔍 {tech} Answers", expanded=False):
            for i, qa in enumerate(qas):
                st.markdown(f"**Q{i+1}. {qa['question']}**")
                st.markdown(f"**Answer:** {qa['answer'] or '_No answer provided_'}")
                st.markdown("")

    st.info("🙏 Thank you for participating! HR will contact you soon.")
    if st.button("🔄 Restart Interview"):
        reset()
