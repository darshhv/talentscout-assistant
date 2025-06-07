TalentScout AI Hiring Assistant

📋 Project Overview
TalentScout AI Hiring Assistant is a cutting-edge chatbot designed to streamline the technical hiring process. It collects candidate info, generates tailored technical interview questions based on the candidate's tech stack, and evaluates responses with intelligent scoring and feedback. This tool empowers recruiters and hiring managers to conduct consistent, efficient, and data-driven interviews.

🚀 Live Demo
Try the fully functional app here:
https://talentscout-assistant-production.up.railway.app/

🎯 Features
Candidate Information Intake: Collect personal, experience, and tech stack details.

AI-generated Technical Questions: Custom questions for each technology in candidate’s profile.

Answer Submission & Scoring: Interactive Q&A interface with live scoring and grading.

Interview Summary: Detailed performance overview with breakdown by technology.

Beautiful UI: Responsive design with custom styling for optimal user experience.

Multi-step Workflow: Smooth navigation through candidate info, technical interview, and results.

🖼️ Screenshots
| Chat UI | Tech Q&A | Summary Dashboard |
|--------|-----------|-------------------|
| ![Screenshot 1](screenshots/Screenshot%202025-06-08%20000731.png) | ![Screenshot 2](screenshots/Screenshot%202025-06-08%20000914.png) | ![Screenshot 3](screenshots/Screenshot%202025-06-08%20000942.png) |

📄 Full Use Case PDFs:
- [TalentScout Assistant Use Case 1](screenshots/TalentScout%20AI%20Hiring%20Assistant.pdf)
- [Use Case Variant](screenshots/TalentScout%20AI%20Hiring%20Assistant..pdf)
- [Extended Flow Overview](screenshots/TalentScout%20AI%20Hiring%20...pdf)

⚙️ Installation Instructions
Prerequisites
Python 3.10+

Git

Cohere API key

Setup Steps
Clone the repository:

bash
Copy
Edit
git clone https://github.com/darshhv/talentscout-assistant.git
cd talentscout-assistant
Create and activate a virtual environment:

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Configure environment variables:

Create a .env file in the root directory with:

ini
Copy
Edit
COHERE_API_KEY=your_cohere_api_key_here
Run the app locally:

bash
Copy
Edit
streamlit run app.py
Open your browser at http://localhost:8501

📚 Usage Guide
Fill in candidate details and tech stack.

Generate tailored interview questions automatically.

Answer questions in the interactive form.

View your score and detailed summary to assess performance.

Restart interview anytime for a fresh session.

🧰 Technical Details
Framework: Streamlit for UI and app flow.

AI Model: Cohere's large language model (command model) for question generation.

State Management: Streamlit session state to handle multi-step navigation.

Styling: Custom CSS for polished look and feel.

Deployment: Hosted on Railway with GitHub integration for CI/CD.

✍️ Prompt Design
The core prompt instructs the Cohere model to generate 3-5 technical questions per technology in the candidate’s provided tech stack. The prompt ensures consistent formatting for easy parsing and rendering in the app UI. Careful retry logic is implemented to handle API failures gracefully.

🛠 Challenges & Solutions
Challenge: Parsing multi-technology question sets from raw AI text.
Solution: Used regex-based section splitting and cleaning to reliably extract questions.

Challenge: Ensuring smooth UI flow with multi-step forms and dynamic state.
Solution: Leveraged Streamlit session state extensively and added manual rerun triggers.

Challenge: Handling API rate limits and transient errors from Cohere.
Solution: Implemented retry logic with delay and user feedback.

Challenge: Deploying Streamlit app with environment variables securely on Railway.
Solution: Used Railway’s environment variable management with .env fallback locally.

🗺 Roadmap
 Add resume upload and automatic tech stack parsing.

 Integrate AI-driven per-question feedback and scoring.

 Build recruiter dashboard with analytics and candidate comparisons.

 Implement multi-round interview logic (MCQ → Coding → Behavioral).

 Add theme toggle (light/dark mode).

 Enhance UI with chat interface and card-style question display.

🤝 Contributing
Contributions are welcome! Please open issues or submit pull requests with improvements or bug fixes.

📄 License
This project is licensed under the MIT License.

📫 Contact
Created by Darshan Reddy
GitHub: darshhv
Email: dharsxn46@gmail.com
