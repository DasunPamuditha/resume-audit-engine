# VediCode: Automated Evidence-Linking and Confidence-Scoring Engine 🛡️

**BSc Hons in Computing - Final Year Research Project**  
*Coventry University & National Institute of Business Management (NIBM)*

VediCode is a forensic-driven technical recruitment tool that bridges the gap between static resume claims and live software engineering artifacts. Instead of relying on traditional keyword matching, VediCode programmatically cross-examines a candidate's uploaded curriculum vitae (CV) against their public GitHub repository telemetry, structural dependency manifests, and temporal Git provenance.

## 🚀 Key Features

* **Resume Skill Extraction:** Uses Natural Language Processing (NLP) to safely extract self-reported technical skills from PDF resumes while redacting sensitive Personal Identifiable Information (PII).
* **Live GitHub Telemetry:** Asynchronously fetches repository metadata, languages, and setup files (`package.json`, `requirements.txt`, `pom.xml`) to verify d skills.
* **Temporal Forensics & Git Provenance:** Analyzes commit cadences and timestamps (`GIT_AUTHOR_DATE` vs. `GIT_COMMITTER_DATE`) to detect proxy-authorship, bulk-dumps, and synthetic portfolio padding.
* **Explainable AI (XAI) Dashboard:** Provides a clear, plain-English executive summary, a 0-100% heuristic confidence score, and direct clickable evidence links pointing to specific GitHub commit hashes and files.

## 🛠️ Technology Stack

* **Backend:** Python, FastAPI, Uvicorn, Httpx (Async REST/GraphQL API integration)
* **Frontend:** Streamlit, Plotly (Commercial Obsidian Design System)
* **Document Parsing:** PyMuPDF, pypdf
* **Reporting:** ReportLab (Automated PDF Audit Dossier generation)

---

## ⚙️ Local Setup & Installation Guide

Follow these steps to run the VediCode engine locally on your machine.

### 1. Prerequisites
* **Python 3.9+** installed on your system.
* A **GitHub Personal Access Token (PAT)** (Highly recommended to bypass GitHub's 60-requests-per-hour public rate lim# 2. Clone the Repository
`git clone https://github.com/DasunPamuditha/resume-audit-engine.git`
`cd resume-audit-engine`

### 3. Create a Virtual Environment (Optional but Recommended)
`python3 -m venv venv`
`source venv/bin/activate`

### 4. Install Dependencies
Install all required Python libraries:
`pip install fastapi uvicorn streamlit httpx pypdf pymupdf plotly reportlab requests python-multipart`

### 5. Add Your GitHub Token (Bypass Rate Limits)
For the best performance during testing, export a GitHub token to your terminal environment:
* **Mac/Linux:** `export GITHUB_TOKEN="your_personal_access_token_here"`
* **Windows (CMD):** `set GITHUB_TOKEN="your_personal_access_token_here"`

---

## 🚀 Running the Application

VediCode requires both the backend API server and the frontend UI to run simultaneously. You will need to open **two separate terminal windows**.

### Terminal 1: Start the FastAPI Backend
Ensure you are in the project root folder, then run:
`python3 -m uvicorn backend.main:app --reloa--port 8007`
*The backend server will start at http://127.0.0.1:8007.*

### Terminal 2: Start the Streamlit Frontend
Open a new terminal window, navigate to the project folder, and run:
`python3 -m streamlit run frontend/app.py`
*The interactive dashboard will automatically open in your web browser at http://localhost:8501.*

---

## 🧪 How to Use the System
1. Open the web dashboard.
2. Enter a candidate's **GitHub Username** (or paste their full GitHub profile URL).
3. Upload their **Technical Resume** (PDF format).
4. Click **"Check Candidate Now"**. The system will parse the resume, scan the GitHub repositories, perform forensic analysis, and generate the final audit report within seconds.

---
*Developed by Dasun Pamuditha for academic research and evaluation.*
