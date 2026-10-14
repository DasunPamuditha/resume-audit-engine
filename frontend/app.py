# frontend/app.py

import streamlit as st
import requests
import plotly.graph_objects as go
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Page Configuration
st.set_page_config(
    page_title="Explainable AI Resume & Code Audit Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Custom Styling for Enterprise Look
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 30px;
    }
    .card {
        padding: 20px;
        border-radius: 10px;
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .skill-badge-green {
        background-color: #DCFCE7;
        color: #166534;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 4px;
        border: 1px solid #BBF7D0;
    }
    .skill-badge-red {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 4px;
        border: 1px solid #FECACA;
    }
    .repo-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to generate Plotly radial confidence gauge
def plot_confidence_gauge(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Confidence Score", 'font': {'size': 18, 'color': '#1E293B'}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#64748B"},
            'bar': {'color': "#0F172A"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, 50], 'color': '#FEE2E2'},
                {'range': [50, 70], 'color': '#FEF3C7'},
                {'range': [70, 100], 'color': '#DCFCE7'}
            ],
            'threshold': {
                'line': {'color': "#047857", 'width': 4},
                'thickness': 0.8,
                'value': 70
            }
        }
    ))
    fig.update_layout(height=260, margin=dict(l=25, r=25, t=40, b=10))
    return fig

# Helper function to generate a professional PDF report using ReportLab
def generate_pdf_report(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    story.append(Paragraph("Explainable AI Candidate Audit Report", title_style))
    story.append(Paragraph(f"Candidate Username: <b>{data.get('username')}</b> | File: {data.get('filename')}", subtitle_style))
    
    score = data.get("confidence_score", 0)
    status = data.get("status", "unknown").upper()
    repos_count = data.get("repositories_evaluated", 0)
    
    summary_data = [
        [Paragraph("<b>Confidence Score</b>", body_style), Paragraph("<b>Verdict Status</b>", body_style), Paragraph("<b>Evaluated Repos</b>", body_style)],
        [Paragraph(f"{score} / 100", body_style), Paragraph(f"{status}", body_style), Paragraph(f"{repos_count}", body_style)]
    ]
    t = Table(summary_data, colWidths=[180, 180, 180])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Explainable AI (XAI) Justification", heading_style))
    story.append(Paragraph(data.get("xai_rationale", "No rationale provided."), body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Granular Forensic Audit & Security Flags", heading_style))
    forensic_summary = data.get("forensic_audit_summary", {})
    critical_errors = forensic_summary.get("critical_errors", [])
    warnings = forensic_summary.get("warnings", [])
    
    if not critical_errors and not warnings:
        story.append(Paragraph("<i>No critical errors or security warnings detected.</i>", body_style))
    else:
        for err in critical_errors:
            story.append(Paragraph(f"<font color='#DC2626'><b>[CRITICAL]</b></font> Category: {err.get('category')} (Line {err.get('line')}): {err.get('message')}", body_style))
        for warn in warnings:
            story.append(Paragraph(f"<font color='#D97706'><b>[WARNING]</b></font> Category: {warn.get('category')} (Line {warn.get('line')}): {warn.get('message')}", body_style))
            
    story.append(Spacer(1, 10))

    story.append(Paragraph("Skill-Gap & Repository Analysis", heading_style))
    skill_data = data.get("skill_gap_analysis", {})
    matched = ", ".join(skill_data.get("matched_skills", [])) or "None"
    unverified = ", ".join(skill_data.get("unverified_claims", [])) or "None"
    
    story.append(Paragraph(f"<b>Matched Skills:</b> {matched}", body_style))
    story.append(Paragraph(f"<b>Unverified Claims:</b> {unverified}", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# App Title & Overview
st.markdown('<p class="main-header">🛡️ Explainable AI Resume & Code Audit Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated Candidate Screening, GitHub Artifact Verification & Granular Forensic Auditing</p>', unsafe_allow_html=True)

# Initialize Session State safely
if "audit_data" not in st.session_state:
    st.session_state.audit_data = None

# Sidebar Controls
st.sidebar.header("🔍 Candidate Evaluation Panel")
github_username = st.sidebar.text_input("GitHub Username", placeholder="e.g. torvalds")
uploaded_file = st.sidebar.file_uploader("Upload Candidate Resume (.pdf or .txt)", type=["pdf", "txt"])

API_URL = "http://127.0.0.1:8007"

try:
    health_check = requests.get(f"{API_URL}/", timeout=2)
    if health_check.status_code == 200:
        st.sidebar.success("🟢 Backend Connected (Port 8007)")
    else:
        st.sidebar.warning("🟡 Backend responding with warnings.")
except Exception:
    st.sidebar.error("🔴 Backend Offline! Start your FastAPI server first.")

if st.sidebar.button("🚀 Run AI Audit Pipeline", type="primary"):
    if not github_username or not uploaded_file:
        st.warning("⚠️ Please provide both a GitHub username and upload a resume file.")
    else:
        with st.spinner("Analyzing candidate profile, parsing AST/lexical code structures, and computing XAI rationale..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(f"{API_URL}/audit-candidate/{github_username}", files=files, timeout=30)
                
                if response.status_code == 200:
                    st.session_state.audit_data = response.json()
                else:
                    st.error(f"Server error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend API: {e}")

# Render Dashboard if Audit Data Exists in Session State
if st.session_state.audit_data:
    data = st.session_state.audit_data
    
    st.markdown("### 📊 Executive Summary & Verdict")
    col1, col2, col3 = st.columns([1.2, 1, 1])
    
    with col1:
        score = data.get("confidence_score", 0)
        st.plotly_chart(plot_confidence_gauge(score), use_container_width=True)
        
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        status = data.get("status", "unknown").upper()
        if status == "VERIFIED":
            st.success(f"**Verdict Status:**\n\n### {status}")
        else:
            st.error(f"**Verdict Status:**\n\n### {status}")
            
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric(label="Evaluated Repositories", value=data.get("repositories_evaluated", 0))
        
        pdf_bytes = generate_pdf_report(data)
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=f"audit_report_{data.get('username', 'candidate')}.pdf",
            mime="application/pdf"
        )
        
    st.markdown("### 🤖 Explainable AI (XAI) Justification")
    st.info(data.get("xai_rationale", "No rationale generated."))
    
    st.markdown("### 🔍 Granular Forensic Audit & Security Flags")
    forensic_summary = data.get("forensic_audit_summary", {})
    total_flags = forensic_summary.get("total_flags", 0)
    
    if total_flags == 0:
        st.success("✨ Zero security issues or forensic anomalies detected across codebase analysis.")
    else:
        critical_errors = forensic_summary.get("critical_errors", [])
        warnings = forensic_summary.get("warnings", [])
        notices = forensic_summary.get("notices", [])
        
        f_tab1, f_tab2, f_tab3 = st.tabs([
            f"🔴 Critical Errors ({len(critical_errors)})", 
            f"🟡 Warnings ({len(warnings)})", 
            f"🔵 Notices ({len(notices)})"
        ])
        
        with f_tab1:
            if critical_errors:
                for err in critical_errors:
                    st.error(f"**Category:** {err.get('category')} | **Line {err.get('line', 'N/A')}:** {err.get('message')}")
            else:
                st.markdown("No critical errors found.")
                
        with f_tab2:
            if warnings:
                for warn in warnings:
                    st.warning(f"**Category:** {warn.get('category')} | **Line {warn.get('line', 'N/A')}:** {warn.get('message')}")
            else:
                st.markdown("No warnings found.")
                
        with f_tab3:
            if notices:
                for note in notices:
                    st.info(f"**Category:** {note.get('category')} | **Line {note.get('line', 'N/A')}:** {note.get('message')}")
            else:
                st.markdown("No notices found.")

    st.markdown("### 🧬 Skill-Gap & Repository Evidence")
    sg_col1, sg_col2 = st.columns(2)
    
    skill_data = data.get("skill_gap_analysis", {})
    matched_skills = skill_data.get("matched_skills", [])
    unverified_skills = skill_data.get("unverified_claims", [])
    
    with sg_col1:
        st.markdown("#### ✅ Verified / Matched Skills")
        if matched_skills:
            badges_html = "".join([f'<span class="skill-badge-green">✓ {skill.upper()}</span>' for skill in matched_skills])
            st.markdown(f"<div style='padding: 10px 0;'>{badges_html}</div>", unsafe_allow_html=True)
        else:
            st.info("No verified skills matched against codebase artifacts.")
            
    with sg_col2:
        st.markdown("#### ⚠️ Unverified Claims / Gaps")
        if unverified_skills:
            badges_html = "".join([f'<span class="skill-badge-red">⚠ {skill.upper()}</span>' for skill in unverified_skills])
            st.markdown(f"<div style='padding: 10px 0;'>{badges_html}</div>", unsafe_allow_html=True)
        else:
            st.success("✨ Zero skill gaps or unverified claims detected!")
            
    st.markdown("#### 📂 Evaluated Public Repositories")
    repos = data.get("repositories", [])
    if repos:
        for repo in repos:
            repo_name = repo.get('name')
            repo_url = repo.get('html_url')
            stars = repo.get('stargazers_count', 0)
            lang = repo.get('language', 'Mixed/Unknown')
            
            st.markdown(f"""
                <div class="repo-card">
                    <div>
                        <a href="{repo_url}" target="_blank" style="font-weight: 600; color: #0284C7; text-decoration: none; font-size: 1.05rem;">📦 {repo_name}</a>
                        <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">Primary Language: <b>{lang}</b></div>
                    </div>
                    <div style="text-align: right; font-size: 0.85rem; color: #475569;">
                        ⭐ <b>{stars}</b> stars
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("_No public repositories found or mock fallback utilized._")