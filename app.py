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

# --- Custom CSS Styling for Luxury UI ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&family=Playfair+Display:wght@700&display=swap');

    /* Root app container */
    .stApp {
        max-width: 900px;
        margin: 2rem auto 3rem;
        padding: 3rem 4rem;
        background: linear-gradient(135deg, #0b1422, #1a2a47);
        border-radius: 20px;
        box-shadow:
            0 0 20px rgba(255, 215, 0, 0.2),
            inset 0 0 15px rgba(255, 215, 0, 0.15);
        font-family: 'Montserrat', sans-serif;
        color: #f5e6c4;
        transition: background 0.5s ease;
    }

    /* Headings */
    h1 {
        font-family: 'Playfair Display', serif !important;
        font-size: 3.8rem !important;
        font-weight: 900 !important;
        color: #ffd700 !important;  /* Gold */
        text-align: center !important;
        margin-bottom: 2rem !important;
        text-shadow: 0 0 8px #ffd700aa;
    }
    h2, h3 {
        color: #ffe082 !important;
        font-weight: 700 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(10, 20, 38, 0.95);
        color: #ffe066;
        border-right: 2px solid #ffd700;
        font-family: 'Montserrat', sans-serif;
        box-shadow: 2px 0 15px rgba(255, 215, 0, 0.3);
        padding-top: 2rem;
    }
    [data-testid="stSidebar"] .css-1d391kg {
        font-weight: 700;
        font-size: 1.3rem;
        margin-bottom: 1rem;
        color: #ffd700;
        text-align: center;
        text-shadow: 0 0 5px #ffd700aa;
    }
    [data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: none !important;
        color: #f5e6c4 !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        margin-bottom: 0.8rem !important;
        width: 100% !important;
        text-align: left !important;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] button:hover {
        color: #ffd700 !important;
        text-shadow: 0 0 10px #ffd700;
        cursor: pointer;
        background-color: rgba(255, 215, 0, 0.1) !important;
        border-radius: 10px;
    }
    [data-testid="stSidebar"] .css-1pq1v3m {
        /* progress bar container */
        background: #1a2a47 !important;
        border-radius: 8px !important;
        height: 12px !important;
        margin-top: 1rem !important;
        margin-bottom: 2rem !important;
    }
    [data-testid="stSidebar"] .stProgress > div > div {
        background: #ffd700 !important;
        box-shadow: 0 0 10px #ffd700cc;
        border-radius: 8px !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #ffd700, #b8860b);
        color: #0b1422 !important;
        font-weight: 700 !important;
        padding: 0.9rem 2rem !important;
        border-radius: 15px !important;
        font-size: 1.2rem !important;
        box-shadow:
            0 0 10px #ffd700,
            inset 0 -3px 5px #b8860b;
        border: none !important;
        transition: all 0.4s ease;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #b8860b, #ffd700);
        box-shadow:
            0 0 20px #ffd700,
            inset 0 3px 6px #fffacd;
        cursor: pointer;
        transform: translateY(-2px);
    }

    /* Text inputs, textareas, selects */
    textarea, input, select {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #f5e6c4 !important;
        border-radius: 12px !important;
        border: 2px solid #ffd700 !important;
        padding: 0.9rem 1.2rem !important;
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
        box-shadow: inset 0 0 5px #ffd700aa;
        font-family: 'Montserrat', sans-serif;
        resize: vertical !important;
        width: 100% !important;
    }
    textarea::placeholder, input::placeholder {
        color: #ffe082 !important;
        font-style: italic;
    }
    textarea:focus, input:focus, select:focus {
        outline: none !important;
        border-color: #fff176 !important;
        box-shadow: 0 0 12px #fff176cc !important;
        background: rgba(255, 255, 255, 0.15) !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 700 !important;
        color: #fff176 !important;
        font-size: 1.25rem !important;
        font-family: 'Montserrat', sans-serif;
        text-shadow: 0 0 8px #ffd700aa;
    }

    /* Progress Bar */
    .stProgress > div > div {
        background: #ffd700 !important;
        box-shadow: 0 0 12px #ffd700cc;
    }

    /* Markdown links */
    a {
        color: #ffd700 !important;
        text-decoration: none !important;
        font-weight: 700 !important;
        transition: color 0.3s ease;
    }
    a:hover {
        color: #fff176 !important;
        text-decoration: underline !important;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

# --- Sidebar ---
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

# --- Helpers ---
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
    return analysis.sentiment.polarity  # Range [-1, 1]

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

# --- Candidate Info Step ---
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
        resume_file = st.file_uploader("Upload Your Resume (PDF or TXT)", type=["pdf", "txt"])
        submitted = st.form_submit_button("👉 Generate Interview Questions")

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
        options=["English", "Hindi", "Spanish", "French", "German", "Chinese", "Other"]
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
                ans = qa.get("answer", "")
                trans = translate_text(ans, target_language="en")
                translated[tech].append(trans)
                sentiments[tech].append(sentiment_analysis(trans))
        st.session_state.translated_answers = translated
        st.session_state.sentiment_scores = sentiments

        # Calculate score (simple % answered)
        score = evaluate_answers(st.session_state.answers)
        st.session_state.score = score
        grade = grade_candidate(score)
        st.session_state.grade = grade

        job, upskill = recommend_jobs_and_upskill(score, st.session_state.candidate_info.get("Tech Stack", ""))
        st.session_state.job_recommendation = job
        st.session_state.upskill_recommendation = upskill

        st.success(f"🎉 Your answers have been submitted! You scored: **{score:.1f}%** - {grade}")
        st.info(f"Suggested role: **{job}**")
        st.info(f"Upskill advice: {upskill}")

        if st.button("🔙 Go Back to Candidate Info"):
            st.session_state.step = 1
            st.experimental_rerun()
        if st.button("📊 Proceed to Evaluation Summary"):
            st.session_state.step = 3
            st.experimental_rerun()

# --- Step 3: Evaluation Summary ---
elif st.session_state.step == 3:
    st.header("📊 Step 3: Evaluation Summary")

    st.markdown("### Candidate Details")
    info = st.session_state.candidate_info
    for k, v in info.items():
        st.markdown(f"**{k}:** {v}")

    st.markdown("### Interview Performance")
    st.markdown(f"**Overall Score:** {st.session_state.score:.1f}%")
    st.markdown(f"**Grade:** {st.session_state.grade}")

    st.markdown("### Answers & Sentiment Analysis")
    for tech, answers in st.session_state.answers.items():
        with st.expander(f"🔍 {tech} Answers & Sentiments"):
            for i, qa in enumerate(answers):
                ans = qa.get("answer", "")
                trans = st.session_state.translated_answers.get(tech, [""] * len(answers))[i]
                sentiment = st.session_state.sentiment_scores.get(tech, [0.0] * len(answers))[i]
                st.markdown(f"**Q{i+1}:** {qa['question']}")
                st.markdown(f"- **Answer:** {ans or '_No answer provided_'}")
                st.markdown(f"- **Translated:** {trans or '_N/A_'}")
                st.markdown(f"- **Sentiment Score:** {sentiment:.2f}")
                st.markdown("---")

    st.markdown("### Recommendations")
    st.success(f"**Suggested Role:** {st.session_state.job_recommendation}")
    st.info(f"**Upskill Advice:** {st.session_state.upskill_recommendation}")

    if st.button("🔙 Go Back to Interview"):
        st.session_state.step = 2
        st.rerun()
    if st.button("🔄 Start Over"):
        reset_all()
