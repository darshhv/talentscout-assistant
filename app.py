import streamlit as st
import os
import re
import time
import cohere
from dotenv import load_dotenv

# Display Streamlit version for debugging
st.write(f"Streamlit version: {st.__version__}")

# --- Page Config ---
st.set_page_config(page_title="TalentScout AI Hiring Assistant", layout="wide")

# --- Load Environment Variables ---
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY") or "mKIVieau5Y6cGjqEFK960IkZfLIjRjCPs1KP3pNu"

# Initialize Cohere client
co = cohere.Client(COHERE_API_KEY)

# --- Styling ---
st.markdown("""
<style>
.stApp { max-width: 900px; margin: auto; padding: 2rem 3rem; background: linear-gradient(135deg, #e0eafc, #cfdef3); border-radius: 12px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);}
h1 { font-size: 3rem; font-weight: 900; color: #1a237e; text-align: center; font-family: 'Poppins', sans-serif;}
.stButton>button { background-color: #3949ab; color: white; font-weight: 700; padding: 0.6rem 1.4rem; border-radius: 0.6rem; font-size: 1.1rem;}
.stButton>button:hover { background-color: #303f9f;}
textarea, input, select { border-radius: 0.5rem !important; border: 1.5px solid #3949ab !important; padding: 0.6rem !important; font-size: 1rem !important;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>TalentScout AI Hiring Assistant</h1>", unsafe_allow_html=True)

# --- Session Initialization ---
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
st.sidebar.title("Interview Process")
for i, s in enumerate(steps, 1):
    if st.sidebar.button(s, key=f"nav_{i}"):
        st.session_state.step = i
        st.session_state.trigger_rerun = True
st.progress(st.session_state.step / len(steps))

def reset():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Use st.experimental_rerun only if available in your Streamlit version
    try:
        st.experimental_rerun()
    except AttributeError:
        st.stop()

# --- Function to Generate Questions from Cohere ---
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
                model='command',
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

# --- Parsing questions ---
def parse_questions(text):
    sections = re.split(r'\n(?=###\s*)', text)
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

# --- Evaluate answers completeness ---
def evaluate_answers(qas):
    total = sum(len(v) for v in qas.values())
    answered = sum(1 for v in qas.values() for qa in v if qa.get("answer", "").strip())
    return (answered / total) * 100 if total else 0

# --- Grade based on score ---
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
                "Full Name": name,
                "Email": email,
                "Phone": phone,
                "Years of Experience": exp,
                "Desired Position": role,
                "Current Location": location,
                "Tech Stack": tech_stack
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

# --- Step 3: Evaluation Summary ---
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

# --- Rerun trigger ---
if st.session_state.get("trigger_rerun"):
    st.session_state.trigger_rerun = False
    try:
        st.experimental_rerun()
    except AttributeError:
        st.stop()
