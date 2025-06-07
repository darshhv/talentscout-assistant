import streamlit as st
import requests
import os
import re
import time

# Get Hugging Face API token from environment (for Railway)
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

# Page setup
st.set_page_config(page_title="TalentScout AI Hiring Assistant", layout="wide")
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}
.stApp {
    background: linear-gradient(to bottom, #f9fbfd, #f2f6fa);
    padding-bottom: 3rem;
}
h1.title {
    text-align: center;
    font-size: 3rem;
    font-weight: bold;
    color: #202942;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}
.card {
    background-color: white;
    padding: 1.5rem 2rem;
    border-radius: 1rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.07);
    margin-bottom: 2rem;
}
textarea, input {
    border-radius: 0.5rem !important;
}
.stButton > button {
    background-color: #4CAF50;
    color: white;
    font-weight: 600;
    border-radius: 0.4rem;
}
.stButton > button:hover {
    background-color: #388e3c;
}
</style>
<h1 class="title">🚀 TalentScout - AI Hiring Assistant</h1>
""", unsafe_allow_html=True)

# Init state
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.candidate_info = {}
    st.session_state.tech_questions_raw = ""
    st.session_state.tech_questions = {}
    st.session_state.answers = {}
    st.session_state.score = None
    st.session_state.grade = None
if 'trigger_rerun' not in st.session_state:
    st.session_state.trigger_rerun = False

# Sidebar Navigation
steps = ["Candidate Info 📝", "Technical Interview 💻", "Evaluation Summary 📊"]
st.sidebar.title("📌 Interview Process")
for i, s in enumerate(steps, 1):
    if st.sidebar.button(s, key=f"nav_{i}"):
        st.session_state.step = i
        st.session_state.trigger_rerun = True
st.progress(st.session_state.step / len(steps))

# Reset
def reset():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# --- API Functions ---
def generate_questions(tech_stack, retries=3, delay=5):
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
        "parameters": {"max_new_tokens": 512, "temperature": 0.7}
    }
    for attempt in range(retries):
        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and 'generated_text' in data[0]:
                    return data[0]['generated_text'].strip()
                else:
                    st.error("Unexpected API response format.")
                    return None
            elif res.status_code == 401:
                st.error("🚫 Invalid Hugging Face API token. Please check your token in Railway.")
                return None
            else:
                st.error(f"API error: {res.status_code} — {res.text}")
                return None
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                st.warning(f"Timeout on attempt {attempt+1}. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                st.error("API request timed out after multiple retries.")
                return None
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return None

def parse_questions(text):
    sections = re.split(r'\n(?=###\s*)', text.strip())
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
    return (
        "🌟 Excellent - Highly Recommended" if score >= 80 else
        "✅ Good - Recommended" if score >= 60 else
        "⚠️ Average - Needs Improvement" if score >= 40 else
        "❌ Poor - Not Recommended"
    )

# --- Step 1: Candidate Info ---
if st.session_state.step == 1:
    with st.container():
        with st.form("candidate_form"):
            st.subheader("📝 Step 1: Candidate Information")
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
            submitted = st.form_submit_button("🚀 Generate Interview Questions")

        if submitted:
            if not name or not email or not phone or not tech_stack.strip():
                st.error("⚠️ Please fill all required fields!")
            else:
                st.session_state.candidate_info = {
                    "Full Name": name, "Email": email, "Phone": phone,
                    "Years of Experience": exp, "Desired Position": role,
                    "Current Location": location, "Tech Stack": tech_stack
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
                    st.success("✅ Questions generated!")
                    st.session_state.step = 2
                    st.session_state.trigger_rerun = True
                else:
                    st.error("❌ Failed to generate questions.")

# --- Step 2: Interview ---
elif st.session_state.step == 2:
    st.subheader("💻 Step 2: Technical Interview")
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
        st.success(f"🎯 Score: {score:.2f}% — {grade}")
        st.session_state.step = 3
        st.session_state.trigger_rerun = True

# --- Step 3: Summary ---
elif st.session_state.step == 3:
    st.subheader("📊 Step 3: Evaluation Summary")
    st.balloons()
    st.success("✅ Interview Completed!")

    st.markdown(f"### 👤 Candidate: **{st.session_state.candidate_info.get('Full Name')}**")
    st.markdown(f"**🎯 Score:** {st.session_state.score:.2f}%")
    st.markdown(f"**📝 Grade:** {st.session_state.grade}")

    st.markdown("### 📌 Scores by Technology")
    for tech, qas in st.session_state.answers.items():
        tech_score = evaluate_answers({tech: qas})
        tech_grade = grade_candidate(tech_score)
        st.markdown(f"- **{tech}**: {tech_score:.2f}% — {tech_grade}")

    st.markdown("---\n### 🔍 Review Answers")
    for tech, qas in st.session_state.answers.items():
        with st.expander(f"{tech} Answers"):
            for i, qa in enumerate(qas):
                st.markdown(f"**Q{i+1}. {qa['question']}**")
                st.markdown(f"**Answer:** {qa['answer'] or '_No answer provided_'}")

    if st.button("🔄 Restart Interview"):
        reset()

# Rerun handler
if st.session_state.get("trigger_rerun"):
    st.session_state.trigger_rerun = False
    st.experimental_rerun()
