import streamlit as st
import os
import re
import time
import cohere
import fitz  # PyMuPDF
from dotenv import load_dotenv
from pdfminer.high_level import extract_text
from io import BytesIO
from textblob import TextBlob
from deep_translator import GoogleTranslator

# --- Load Environment Variables ---
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY") or "your-default-key-here"
co = cohere.Client(COHERE_API_KEY)

# --- Page Config ---
st.set_page_config(
    page_title="TalentScout AI Hiring Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🤖"
)

# --- Custom CSS Styling ---
st.markdown(
    """
    <style>
    /* Container styling */
    .stApp {
        max-width: 900px;
        margin: 2rem auto 3rem;
        padding: 2.5rem 3rem;
        background: linear-gradient(135deg, #e0eafc, #cfdef3);
        border-radius: 16px;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.15);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Main header */
    h1 {
        font-size: 3.6rem !important;
        font-weight: 900 !important;
        color: #1a237e !important;
        text-align: center !important;
        margin-bottom: 1.5rem !important;
        font-family: 'Poppins', sans-serif !important;
        letter-spacing: 1.1px;
        text-shadow: 1px 1px 2px #c5c9e4;
    }
    /* Sidebar buttons */
    .stSidebar .stButton > button {
        background-color: #3949ab !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 0.8rem !important;
        font-size: 1.1rem !important;
        padding: 0.7rem 1.8rem !important;
        margin-bottom: 0.75rem;
        border: none !important;
        width: 100%;
        transition: background-color 0.3s ease;
    }
    .stSidebar .stButton > button:hover {
        background-color: #303f9f !important;
        cursor: pointer;
    }
    /* Main buttons */
    .stButton > button {
        background-color: #3949ab !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 0.7rem 1.8rem !important;
        border-radius: 0.8rem !important;
        font-size: 1.1rem !important;
        border: none !important;
        width: 100%;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #303f9f !important;
        cursor: pointer;
    }
    /* Inputs, textareas, selects */
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
        box-shadow: 0 0 10px #3949abaa !important;
    }
    /* Expander header styling */
    .streamlit-expanderHeader {
        font-weight: 700 !important;
        color: #283593 !important;
        font-size: 1.1rem !important;
    }
    /* Progress bar color */
    .stProgress > div > div {
        background: #3949ab !important;
    }
    /* Form label bold */
    label[data-baseweb="label"] {
        font-weight: 600 !important;
        color: #1a237e !important;
        font-size: 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Title ---
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
    st.session_state.lang = "en"
    st.session_state.translated_answers = {}
    st.session_state.sentiment_scores = {}
    st.session_state.job_recommendation = ""
    st.session_state.upskill_recommendation = ""

if "trigger_rerun" not in st.session_state:
    st.session_state.trigger_rerun = False

# --- Sidebar: Navigation ---
steps = [
    "Candidate Info 📝",
    "Technical Interview 💻",
    "Evaluation Summary 📊"
]
st.sidebar.title("Interview Process")
for i, label in enumerate(steps, 1):
    if st.sidebar.button(label):
        st.session_state.step = i
        st.session_state.trigger_rerun = True
st.sidebar.progress(st.session_state.step / len(steps))

# --- Helper functions (unchanged, no logic edits) ---
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

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

def sentiment_analysis(text):
    if not text.strip():
        return 0.0
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def parse_resume(file_bytes, filename):
    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf_doc:
                text += page.get_text()
        elif filename.lower().endswith(".txt"):
            text = file_bytes.decode("utf-8")
        else:
            text = extract_text(BytesIO(file_bytes))
    except Exception as e:
        st.warning(f"Could not parse resume: {e}")
    return text

def extract_skills_from_resume(text):
    skills = []
    lines = text.lower().split("\n")
    keywords = ["python", "java", "react", "docker", "aws", "c++", "sql", "javascript",
                "html", "css", "tensorflow", "pytorch", "git", "linux", "node.js", "azure", "gcp"]
    for kw in keywords:
        for line in lines:
            if kw in line:
                skills.append(kw.capitalize())
                break
    return sorted(set(skills))

def recommend_jobs_and_upskill(score, tech_stack):
    if score >= 80:
        job = "Senior Developer / Lead"
        upskill = "Consider mentoring or learning architecture design."
    elif score >= 60:
        job = "Mid-level Developer"
        upskill = "Enhance problem-solving skills and system design."
    elif score >= 40:
        job = "Junior Developer"
        upskill = "Focus on core programming and project experience."
    else:
        job = "Intern / Trainee"
        upskill = "Improve fundamentals and complete online courses."

    if tech_stack:
        upskill += f" Upskill in {tech_stack} technologies is recommended."

    return job, upskill

def translate_text(text, target_language='en'):
    if not text.strip():
        return ""
    try:
        translated = GoogleTranslator(source='auto', target=target_language).translate(text)
        return translated
    except Exception as e:
        st.warning(f"Translation failed: {e}")
        return text

# --- Step 1: Candidate Info ---
if st.session_state.step == 1:
    st.header("📝 Step 1: Candidate Information")

    with st.form("candidate_form", clear_on_submit=False):
        col1, col2 = st.columns(2, gap="large")

        with col1:
            name = st.text_input("Full Name", value=st.session_state.candidate_info.get("Full Name", ""))
            email = st.text_input("Email Address", value=st.session_state.candidate_info.get("Email", ""))
            phone = st.text_input("Phone Number", value=st.session_state.candidate_info.get("Phone", ""))
            exp = st.number_input("Years of Experience",
                                  min_value=0, max_value=50,
                                  value=st.session_state.candidate_info.get("Years of Experience", 0),
                                  step=1)
        with col2:
            role = st.text_input("Desired Position", value=st.session_state.candidate_info.get("Desired Position", ""))
            location = st.text_input("Current Location", value=st.session_state.candidate_info.get("Current Location", ""))
            tech_stack = st.text_area(
                "Tech Stack (comma-separated)",
                value=st.session_state.candidate_info.get("Tech Stack", ""),
                height=120,
                placeholder="E.g., Python, React, Docker, AWS",
            )

        resume_file = st.file_uploader("Upload Your Resume (PDF or TXT)", type=["pdf", "txt"])

        submitted = st.form_submit_button("👉 Generate Interview Questions")

    # Extract skills from resume and update tech stack if empty or append
    if resume_file:
        raw_bytes = resume_file.read()
        resume_text = parse_resume(raw_bytes, resume_file.name)
        extracted_skills = extract_skills_from_resume(resume_text)
        if extracted_skills:
            st.info(f"Extracted skills from resume: {', '.join(extracted_skills)}")
            if not tech_stack:
                tech_stack = ", ".join(extracted_skills)
            else:
                current_skills = [x.strip().lower() for x in tech_stack.split(",")]
                for s in extracted_skills:
                    if s.lower() not in current_skills:
                        tech_stack += ", " + s
            st.session_state.candidate_info["Tech Stack"] = tech_stack

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

    lang_option = st.selectbox(
        "Choose your language (answers will be translated to English for evaluation):",
        options=["English", "Hindi", "Spanish", "French", "German", "Chinese", "Other"],
        index=0,
    )
    lang_code = lang_option[:2].lower()
    st.session_state.lang = lang_code

    with st.form("answers_form"):
        for tech, qas in st.session_state.answers.items():
            with st.expander(f"💡 {tech} ({len(qas)} questions)", expanded=False):
                for i, qa in enumerate(qas):
                    st.markdown(f"**Q{i + 1}. {qa['question']}**")
                    ans = st.text_area(
                        f"Your Answer for Q{i + 1}",
                        value=qa["answer"],
                        height=110,
                        key=f"{tech}_{i}",
                        placeholder="Type your answer here...",
                    )
                    st.session_state.answers[tech][i]["answer"] = ans
        submitted = st.form_submit_button("✅ Submit Answers")

    if submitted:
        translated = {}
        sentiments = {}
        for tech, qas in st.session_state.answers.items():
            translated[tech] = []
            sentiments[tech] = []
            for qa in qas:
                text = qa.get("answer", "").strip()
                if lang_code != "en" and text:
                    text_en = translate_text(text, target_language="en")
                else:
                    text_en = text
                translated[tech].append(text_en)
                sentiments[tech].append(sentiment_analysis(text_en))

        st.session_state.translated_answers = translated
        st.session_state.sentiment_scores = sentiments

        score = evaluate_answers(st.session_state.answers)
        grade = grade_candidate(score)

        job, upskill = recommend_jobs_and_upskill(score, st.session_state.candidate_info.get("Tech Stack", ""))
        st.session_state.job_recommendation = job
        st.session_state.upskill_recommendation = upskill

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

    info = st.session_state.candidate_info
    st.markdown(f"### Candidate: **{info.get('Full Name', 'N/A')}**")
    st.markdown(f"**Overall Score:** {st.session_state.score:.2f}%")
    st.markdown(f"**Final Grade:** {st.session_state.grade}")

    st.markdown(f"### Recommended Job Role: **{st.session_state.job_recommendation}**")
    st.markdown(f"### Upskill Suggestions: {st.session_state.upskill_recommendation}")

    st.markdown("### Scores & Sentiments by Technology")
    for tech, qas in st.session_state.answers.items():
        tech_score = evaluate_answers({tech: qas})
        tech_grade = grade_candidate(tech_score)
        avg_sentiment = 0
        if tech in st.session_state.sentiment_scores:
            scores = st.session_state.sentiment_scores[tech]
            avg_sentiment = sum(scores) / len(scores) if scores else 0
        sentiment_text = (
            "Positive 😊" if avg_sentiment > 0.1 else
            "Neutral 😐" if -0.1 <= avg_sentiment <= 0.1 else
            "Negative 😞"
        )
        st.markdown(f"- **{tech}**: {tech_score:.2f}% — {tech_grade} — Sentiment: {sentiment_text}")

    st.markdown("---")
    st.markdown("### Review Answers and Translations")
    for tech, qas in st.session_state.answers.items():
        with st.expander(f"🔍 {tech} Answers", expanded=False):
            for i, qa in enumerate(qas):
                answer = qa.get("answer") or "_No answer provided_"
                translated = st.session_state.translated_answers.get(tech, [""] * len(qas))[i]
                st.markdown(f"**Q{i + 1}. {qa['question']}**")
                st.markdown(f"**Answer:** {answer}")
                if answer.strip() and answer != translated:
                    st.markdown(f"**(Translated to English):** {translated}")

    if st.button("🔄 Restart Interview"):
        reset_all()

# --- Manual rerun ---
if st.session_state.get("trigger_rerun"):
    st.session_state.trigger_rerun = False
    st.rerun()
