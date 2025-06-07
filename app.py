import streamlit as st
import os
import re
import time
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("🚨 Please set your OPENROUTER_API_KEY in environment variables!")
    st.stop()

# Configure OpenAI client for OpenRouter API
openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

# Page config
st.set_page_config(
    page_title="TalentScout AI Hiring Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Premium UI Style ---
st.markdown("""
<style>
/* Container */
.stApp {
    max-width: 900px;
    margin: auto;
    padding: 2rem 3rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #f0f4f8, #d9e2ec);
    color: #102a43;
}

/* Buttons */
.stButton>button {
    background-color: #0052cc;
    color: white;
    font-weight: 700;
    padding: 0.7rem 1.5rem;
    border-radius: 0.6rem;
    font-size: 1.05rem;
    transition: background-color 0.3s ease;
}
.stButton>button:hover {
    background-color: #003d99;
}

/* Inputs */
input, textarea, select {
    border-radius: 0.5rem !important;
    border: 1.8px solid #bcccdc !important;
    padding: 0.5rem 0.75rem !important;
    font-size: 1rem !important;
}

/* Header */
h1 {
    font-size: 3rem !important;
    font-weight: 900 !important;
    color: #102a43 !important;
    margin-bottom: 0.3rem !important;
}

/* Subtitle */
.subtitle {
    font-size: 1.2rem;
    color: #334e68;
    margin-bottom: 2rem;
}

/* Sidebar */
.css-1d391kg {
    background: #f0f4f8 !important;
    font-weight: 600 !important;
}

/* Cards */
.card {
    background: white;
    padding: 1.8rem 2.2rem;
    border-radius: 1rem;
    box-shadow: 0 8px 20px rgb(0 0 0 / 0.1);
    margin-bottom: 2rem;
    transition: transform 0.3s ease;
}
.card:hover {
    transform: translateY(-5px);
}

/* Expanders */
.stExpander > div[role="button"] {
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    color: #0b3d91 !important;
}
</style>
""", unsafe_allow_html=True)

# Title and subtitle
st.markdown("<h1>TalentScout AI Hiring Assistant</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Accelerate your hiring process with AI-powered interview question generation and evaluation.</p>', unsafe_allow_html=True)

# Initialize session state variables
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

# Reset function
def reset():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# Generate questions using OpenRouter API
def generate_questions(tech_stack, retries=3, delay=3):
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
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="openchat/openchat-3.5-1210",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=700,
            )
            content = response.choices[0].message["content"]
            return content.strip()
        except Exception as e:
            if attempt < retries -1:
                st.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                st.error(f"API Error: {e}")
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
    return ("Excellent - Highly Recommended" if score >= 80 else
            "Good - Recommended" if score >= 60 else
            "Average - Needs Improvement" if score >= 40 else
            "Poor - Not Recommended")

# --- Step 1: Candidate Info ---
if st.session_state.step == 1:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

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
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

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
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

# Safe rerun trigger
if st.session_state.get("trigger_rerun"):
    st.session_state.trigger_rerun = False
    st.experimental_rerun()
