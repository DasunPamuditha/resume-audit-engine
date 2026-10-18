# frontend/app.py

import streamlit as st
import requests
import plotly.graph_objects as go
import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VediCode — Resume & GitHub Skill Checker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. CLEAN, HUMAN-CRAFTED DESIGN SYSTEM
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #FAFAFA;
        -webkit-font-smoothing: antialiased;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #09090B !important;
        border-right: 1px solid #27272A !important;
        min-width: 290px !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    [data-testid="stToolbarActions"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1360px !important;
    }

    /* Top Header Bar */
    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0 16px 0;
        border-bottom: 1px solid #27272A;
        margin-bottom: 24px;
    }
    .brand-title {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 800;
        font-size: 1.3rem;
        color: #FAFAFA;
        letter-spacing: -0.02em;
    }
    .brand-sub {
        font-size: 0.82rem;
        color: #A1A1AA;
    }

    /* Candidate Info Bar */
    .dossier-bar {
        background: #121215;
        border: 1px solid #27272A;
        border-radius: 8px;
        padding: 16px 22px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }
    .dossier-meta-group {
        display: flex;
        gap: 32px;
        flex-wrap: wrap;
        align-items: center;
    }
    .dossier-item-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #A1A1AA;
        margin-bottom: 3px;
        font-weight: 600;
    }
    .dossier-item-val {
        font-size: 0.94rem;
        color: #F4F4F5;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .dossier-date-only {
        font-size: 0.82rem;
        color: #A1A1AA;
        font-family: 'JetBrains Mono', monospace;
        background: #18181B;
        border: 1px solid #27272A;
        padding: 6px 12px;
        border-radius: 6px;
    }

    /* Section Headers */
    .sec-header {
        margin-top: 26px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 1px solid #27272A;
        padding-bottom: 8px;
    }
    .sec-title {
        font-size: 1.02rem;
        font-weight: 600;
        color: #F4F4F5;
        margin: 0;
    }
    .sec-desc {
        font-size: 0.82rem;
        color: #A1A1AA;
        margin: 0;
    }

    /* Cards */
    .surface-card {
        background: #121215;
        border: 1px solid #27272A;
        border-radius: 8px;
        padding: 18px 20px;
        height: 100%;
    }
    .metric-label {
        font-size: 0.76rem;
        font-weight: 600;
        color: #A1A1AA;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }
    .metric-big {
        font-size: 2.1rem;
        font-weight: 700;
        color: #FAFAFA;
        line-height: 1.1;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-foot {
        font-size: 0.82rem;
        color: #A1A1AA;
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid #1F1F23;
        line-height: 1.5;
    }

    /* Status Badges */
    .status-pass {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34D399;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .status-fail {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.35);
        color: #F87171;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .dot-green {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-red {
        width: 8px;
        height: 8px;
        background-color: #EF4444;
        border-radius: 50%;
        display: inline-block;
    }

    /* Executive Narrative Block */
    .narrative-block {
        background: #121215;
        border: 1px solid #27272A;
        border-left: 3px solid #6366F1;
        border-radius: 6px;
        padding: 16px 20px;
        color: #E4E4E7;
        font-size: 0.93rem;
        line-height: 1.65;
    }

    /* Skill Tags */
    .tag-verified {
        background: #18181B;
        color: #E4E4E7;
        border: 1px solid #27272A;
        border-left: 3px solid #10B981;
        padding: 5px 12px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
        margin: 4px 6px 4px 0;
    }
    .tag-unverified {
        background: #18181B;
        color: #E4E4E7;
        border: 1px solid #27272A;
        border-left: 3px solid #EF4444;
        padding: 5px 12px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
        margin: 4px 6px 4px 0;
    }

    /* Repository Row Item */
    .repo-item {
        background: #121215;
        border: 1px solid #27272A;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .repo-title {
        font-weight: 600;
        color: #FAFAFA !important;
        text-decoration: none;
        font-size: 0.92rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .repo-title:hover {
        color: #818CF8 !important;
    }
    .repo-lang {
        font-size: 0.75rem;
        color: #D4D4D8;
        background: #18181B;
        border: 1px solid #27272A;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 500;
        display: inline-block;
        margin-right: 6px;
    }
    .badge-solo {
        font-size: 0.74rem;
        color: #34D399;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 9px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
        margin-right: 6px;
    }
    .badge-group {
        font-size: 0.74rem;
        color: #FBBF24;
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 3px 9px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
        margin-right: 6px;
    }

    /* Primary Button */
    div.stButton > button[kind="primary"] {
        background-color: #FAFAFA !important;
        color: #09090B !important;
        border: 1px solid #FAFAFA !important;
        font-weight: 600 !important;
        font-size: 0.86rem !important;
        border-radius: 6px !important;
        padding: 0.55rem 1rem !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #E4E4E7 !important;
        border-color: #E4E4E7 !important;
    }
    </style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def plot_confidence_gauge(score):
    bar_color = "#10B981" if score >= 70 else ("#F59E0B" if score >= 50 else "#EF4444")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'suffix': "%", 'font': {'size': 34, 'color': '#FAFAFA', 'family': 'JetBrains Mono'}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#27272A", 'tickfont': {'color': '#71717A', 'size': 10}},
            'bar': {'color': bar_color, 'thickness': 0.8},
            'bgcolor': "#18181B",
            'borderwidth': 1,
            'bordercolor': "#27272A",
            'threshold': {
                'line': {'color': "#FAFAFA", 'width': 2},
                'thickness': 0.85,
                'value': 70
            }
        }
    ))
    fig.update_layout(
        height=165,
        margin=dict(l=16, r=16, t=16, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def build_humanized_summary(
    username, score, matched_skills, unverified_skills, repos_count, crit_count, warn_count, solo_count, group_count
):
    if not matched_skills and repos_count == 0 and not unverified_skills:
        return f"We could not find any technical skills on {username}'s resume or any public GitHub projects to check."

    parts = [
        f"{username} achieved an overall skill match score of {score}% after evaluating {repos_count} public GitHub project(s) ({solo_count} individual project(s) and {group_count} group project(s))."
    ]

    if matched_skills:
        skills_formatted = ", ".join([f"{s.upper()}" for s in matched_skills])
        parts.append(
            f"Cross-examining the uploaded resume against live repository telemetry confirmed hands-on evidence for {skills_formatted}."
        )
    else:
        parts.append(
            "Zero skill matches were found between the candidate's self-declared resume claims and their public GitHub repositories."
        )

    if unverified_skills:
        unverified_formatted = ", ".join([f"{s.upper()}" for s in unverified_skills])
        parts.append(
            f"Resume claims lacking corroborating public repository or manifest evidence include {unverified_formatted}. Note that these skills may have been utilized in private enterprise environments."
        )

    if crit_count > 0 or warn_count > 0:
        parts.append(
            f"The Git Provenance and Coding Pattern Analyzer flagged {crit_count} critical anomaly(s) and {warn_count} warning(s) across commit timestamps, coding patterns, and repository structures."
        )
    else:
        parts.append(
            "No temporal provenance anomalies, coding pattern shifts, or code security warnings were found across the evaluated repositories."
        )

    return " ".join(parts)


def generate_pdf_report(data, summary_text, score):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=15,
        textColor=colors.HexColor('#09090B'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#52525B'),
        spaceAfter=14
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=11.5,
        textColor=colors.HexColor('#18181B'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=9.5,
        textColor=colors.HexColor('#27272A'),
        spaceAfter=6
    )

    role_str = data.get("target_role") or "Software Developer"
    exec_time = data.get("execution_time_seconds", 0.0)
    ownership = data.get("project_ownership_summary", {})
    solo_c = ownership.get("individual_projects_count", 0)
    group_c = ownership.get("group_projects_count", 0)

    story.append(Paragraph("VEDICODE — CANDIDATE SKILL & GITHUB CHECK REPORT", title_style))
    story.append(Paragraph(
        f"GitHub User: <b>{data.get('username')}</b> | Role: <b>{role_str}</b> | Resume: {data.get('filename')} | Checked in: {exec_time}s",
        subtitle_style
    ))

    status_label = "VERIFIED" if (score >= 70 and len(data.get("forensic_audit_summary", {}).get("critical_errors", [])) < 2) else "NEEDS REVIEW"
    repos_count = data.get("repositories_evaluated", 0)

    summary_data = [
        [Paragraph("<b>Overall Match Score</b>", body_style), Paragraph("<b>Check Result</b>", body_style), Paragraph("<b>Projects (Solo / Group)</b>", body_style)],
        [Paragraph(f"{score}%", body_style), Paragraph(f"{status_label}", body_style), Paragraph(f"{repos_count} ({solo_c} Solo / {group_c} Group)", body_style)]
    ]
    t = Table(summary_data, colWidths=[180, 180, 180])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F4F5F5')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D4D4D8'))
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Executive Audit Summary", heading_style))
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Skills Found vs. Not Found", heading_style))
    skill_data = data.get("skill_gap_analysis", {})
    matched = ", ".join(s.upper() for s in skill_data.get("matched_skills", [])) or "None"
    unverified = ", ".join(s.upper() for s in skill_data.get("unverified_claims", [])) or "None"

    story.append(Paragraph(f"<b>Skills Proven by GitHub Code:</b> {matched}", body_style))
    story.append(Paragraph(f"<b>Skills on Resume Only (Not Found in Public Code):</b> {unverified}", body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Commit History, Coding Patterns & Project Ownership Check", heading_style))
    forensic_summary = data.get("forensic_audit_summary", {})
    critical_errors = forensic_summary.get("critical_errors", [])
    warnings = forensic_summary.get("warnings", [])

    if not critical_errors and not warnings:
        story.append(Paragraph("<i>No suspicious commit patterns, coding style shifts, or code issues were found.</i>", body_style))
    else:
        for err in critical_errors:
            story.append(Paragraph(
                f"<font color='#DC2626'><b>[SERIOUS ISSUE]</b></font> {err.get('category', 'Issue')} ({err.get('line', '')}): {err.get('message', '')}",
                body_style
            ))
        for warn in warnings:
            story.append(Paragraph(
                f"<font color='#D97706'><b>[WARNING]</b></font> {warn.get('category', 'Warning')} ({warn.get('line', '')}): {warn.get('message', '')}",
                body_style
            ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# -----------------------------------------------------------------------------
# 4. LEFT SIDEBAR (INPUT PANEL)
# -----------------------------------------------------------------------------
API_URL = "http://127.0.0.1:8007"

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None

with st.sidebar:
    st.markdown("""
        <div style="padding: 4px 0 14px 0; border-bottom: 1px solid #27272A; margin-bottom: 18px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 1.15rem; color: #FAFAFA;">
                VediCode
            </div>
            <div style="font-size: 0.8rem; color: #A1A1AA; margin-top: 3px;">
                Resume & GitHub Skill Checker
            </div>
        </div>
    """, unsafe_allow_html=True)

    github_username = st.text_input(
        "GitHub Username or Profile Link",
        placeholder="e.g. DasunPamuditha or github.com/..."
    )
    target_role = st.text_input(
        "Job Role (Optional)",
        placeholder="e.g. Software Engineer"
    )
    uploaded_file = st.file_uploader(
        "Upload Candidate Resume (PDF or TXT)",
        type=["pdf", "txt"]
    )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    run_audit = st.button("Check Candidate Now", type="primary", use_container_width=True)

    if run_audit:
        if not github_username or not uploaded_file:
            st.warning("Please enter a GitHub username (or link) and upload a resume first.")
        else:
            with st.spinner("Checking resume, coding patterns, group/solo project ownership, and commit history..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    form_data = {"target_role": target_role}
                    response = requests.post(
                        f"{API_URL}/audit-candidate/{github_username.strip()}",
                        files=files,
                        data=form_data,
                        timeout=60
                    )

                    if response.status_code == 200:
                        st.session_state.audit_data = response.json()
                    else:
                        st.error(f"Could not complete check ({response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"Could not connect to the backend server: {e}")

    st.markdown("""
        <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #27272A; font-size: 0.76rem; color: #71717A; line-height: 1.5;">
            <b>Privacy Note:</b> Uploaded resumes are checked in memory only and never saved on disk. Personal phone numbers and emails are automatically hidden.
        </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. TOP BAR
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="topbar">
        <div class="brand-title">VediCode</div>
        <div class="brand-sub">Simple, Evidence-Based Resume & GitHub Verification</div>
    </div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. MAIN WORKSPACE CONTENT
# -----------------------------------------------------------------------------
if not st.session_state.audit_data:
    st.markdown("""
        <div class="surface-card" style="padding: 52px 32px; text-align: center; margin-top: 16px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #A1A1AA; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;">
                Step 1: Enter Details on the Left Panel
            </div>
            <h3 style="color: #FAFAFA; font-weight: 600; font-size: 1.35rem; margin-bottom: 10px;">
                Check If a Resume Matches Real GitHub Code
            </h3>
            <p style="color: #A1A1AA; font-size: 0.92rem; max-width: 580px; margin: 0 auto 26px auto; line-height: 1.6;">
                Enter the candidate's GitHub username (or link) and upload their PDF resume on the left.
                We will check their real code, coding style patterns, individual vs. group projects, and commit history in seconds.
            </p>
            <div style="display: inline-flex; gap: 10px; flex-wrap: wrap; justify-content: center;">
                <span class="repo-lang">1. Reads Resume Skills</span>
                <span class="repo-lang">2. Checks Coding Style Patterns</span>
                <span class="repo-lang">3. Verifies Solo vs. Group Projects</span>
                <span class="repo-lang">4. Catches Unnatural Commits</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

else:
    data = st.session_state.audit_data
    username = data.get("username", "unknown")
    role_display = data.get("target_role") or "Software Developer"
    filename = data.get("filename", "Resume.pdf")
    exec_time = data.get("execution_time_seconds", 0.0)
    repos_count = data.get("repositories_evaluated", 0)

    forensic_summary = data.get("forensic_audit_summary", {})
    critical_errors = forensic_summary.get("critical_errors", [])
    warnings = forensic_summary.get("warnings", [])
    notices = forensic_summary.get("notices", [])
    total_flags = len(critical_errors) + len(warnings)

    skill_data = data.get("skill_gap_analysis", {})
    matched_skills = skill_data.get("matched_skills", [])
    unverified_skills = skill_data.get("unverified_claims", [])
    heuristic = data.get("heuristic_breakdown", {})
    ownership = data.get("project_ownership_summary", {})
    solo_count = ownership.get("individual_projects_count", 0)
    group_count = ownership.get("group_projects_count", 0)

    raw_score = data.get("confidence_score", 0)
    score = 0 if (not matched_skills and (repos_count == 0 or raw_score == 0)) else raw_score

    is_verified = (score >= 70 and len(critical_errors) < 2)
    status_text = "VERIFIED" if is_verified else "NEEDS REVIEW"

    gmt_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M GMT")
    human_summary = build_humanized_summary(
        username, score, matched_skills, unverified_skills, repos_count, len(critical_errors), len(warnings), solo_count, group_count
    )

    # --- CANDIDATE HEADER BAR ---
    st.markdown(f"""
        <div class="dossier-bar">
            <div class="dossier-meta-group">
                <div>
                    <div class="dossier-item-label">GitHub Account</div>
                    <div class="dossier-item-val">@{username}</div>
                </div>
                <div>
                    <div class="dossier-item-label">Job Role</div>
                    <div class="dossier-item-val">{role_display}</div>
                </div>
                <div>
                    <div class="dossier-item-label">Uploaded Resume</div>
                    <div class="dossier-item-val">{filename}</div>
                </div>
            </div>
            <div class="dossier-date-only">
                Checked in {exec_time}s &bull; {gmt_now}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- ROW 1: 3 MAIN SUMMARY CARDS ---
    col1, col2, col3 = st.columns([1.25, 1, 1])

    with col1:
        st.markdown("""
            <div class="surface-card" style="padding-bottom: 8px;">
                <div class="metric-label">Overall Skill Match Score</div>
        """, unsafe_allow_html=True)
        st.plotly_chart(plot_confidence_gauge(score), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        badge_html = (
            f'<div class="status-pass"><span class="dot-green"></span>{status_text}</div>'
            if is_verified
            else f'<div class="status-fail"><span class="dot-red"></span>{status_text}</div>'
        )
        s_lang_val = heuristic.get("s_lang", 0.0)
        s_dep_val = heuristic.get("s_dep", 0.0)
        s_temp_val = heuristic.get("s_temp", 0.0)
        st.markdown(f"""
            <div class="surface-card">
                <div class="metric-label">Check Result & Score Breakdown</div>
                <div style="margin: 14px 0 14px 0;">
                    {badge_html}
                </div>
                <div class="metric-foot">
                    <b>Code Languages:</b> <span style="color:#FAFAFA;">{s_lang_val}%</span><br>
                    <b>Setup Files (Dependencies):</b> <span style="color:#FAFAFA;">{s_dep_val}%</span><br>
                    <b>Real Commit History:</b> <span style="color:#FAFAFA;">{s_temp_val}%</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="surface-card">
                <div class="metric-label">GitHub Projects & Ownership</div>
                <div class="metric-big">{repos_count} <span style="font-size: 0.9rem; color: #A1A1AA; font-weight: 500;">public projects</span></div>
                <div class="metric-foot">
                    Solo Projects: <span style="color:#34D399; font-weight:600;">{solo_count}</span> &nbsp;&bull;&nbsp;
                    Group Projects: <span style="color:#FBBF24; font-weight:600;">{group_count}</span><br>
                    Proven Skills: <span style="color:#34D399; font-weight:600;">{len(matched_skills)}</span> &nbsp;&bull;&nbsp;
                    Issues / Warnings: <span style="color:#F87171; font-weight:600;">{total_flags}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        pdf_bytes = generate_pdf_report(data, human_summary, score)
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"VediCode_Report_{username}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # --- SECTION: EXECUTIVE AUDIT SUMMARY ---
    st.markdown("""
        <div class="sec-header">
            <p class="sec-title">Executive Audit Summary</p>
            <p class="sec-desc">High-level synthesis of candidate verification and repository forensics</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="narrative-block">
            {human_summary}
        </div>
    """, unsafe_allow_html=True)

    # --- SECTION: SKILLS FOUND VS NOT FOUND ---
    st.markdown("""
        <div class="sec-header">
            <p class="sec-title">Skills on Resume vs. Real GitHub Code</p>
            <p class="sec-desc">Side-by-side comparison of verified and unverified technical claims</p>
        </div>
    """, unsafe_allow_html=True)

    sg_col1, sg_col2 = st.columns(2)

    with sg_col1:
        matched_tags = (
            "".join([f'<span class="tag-verified">{skill.upper()}</span>' for skill in matched_skills])
            if matched_skills
            else '<span style="color: #71717A; font-size: 0.86rem;">No matching skills found on GitHub.</span>'
        )

        st.markdown(f"""
            <div class="surface-card">
                <div class="metric-label" style="color: #34D399;">Skills Proven by GitHub Code ({len(matched_skills)})</div>
                <div style="margin-top: 10px; margin-bottom: 10px;">
                    {matched_tags}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with sg_col2:
        unverified_html = (
            "".join([f'<span class="tag-unverified">{skill.upper()}</span>' for skill in unverified_skills])
            if unverified_skills
            else '<span style="color: #A1A1AA; font-size: 0.86rem;">All resume skills were proven on GitHub!</span>'
        )
        helper_note = (
            '<div style="margin-top: 14px; font-size: 0.8rem; color: #A1A1AA; line-height: 1.5; border-top: 1px solid #1F1F23; padding-top: 10px;">'
            '<b>Fair Interview Tip:</b> If a skill is listed here, it means we did not see it in their <i>public</i> GitHub projects. '
            'Ask the candidate about these skills during their interview, as they may have used them in private company work.'
            '</div>'
            if unverified_skills else ""
        )
        st.markdown(f"""
            <div class="surface-card">
                <div class="metric-label" style="color: #F87171;">Skills Listed on Resume Only ({len(unverified_skills)})</div>
                <div style="margin-top: 10px;">
                    {unverified_html}
                </div>
                {helper_note}
            </div>
        """, unsafe_allow_html=True)

    # --- SECTION: COMMIT HISTORY, CODING PATTERNS & CODE AUTHENTICITY CHECK ---
    st.markdown("""
        <div class="sec-header">
            <p class="sec-title">Commit History, Coding Patterns & Authenticity Check</p>
            <p class="sec-desc">Checks for unnatural commit dates, coding style shifts across files/lines, group project shares, and code safety</p>
        </div>
    """, unsafe_allow_html=True)

    if len(critical_errors) == 0 and len(warnings) == 0 and len(notices) == 0:
        st.markdown("""
            <div class="surface-card" style="padding: 16px 22px; border-left: 3px solid #10B981;">
                <span style="color: #E4E4E7; font-size: 0.9rem; font-weight: 500;">
                    ✅ Everything looks good! We found no suspicious commit dates, coding style shifts, or security issues in their repositories.
                </span>
            </div>
        """, unsafe_allow_html=True)
    else:
        f_tab1, f_tab2, f_tab3 = st.tabs([
            f"Serious Issues ({len(critical_errors)})",
            f"Warnings & Pattern Shifts ({len(warnings)})",
            f"Project Ownership & Code Notes ({len(notices)})"
        ])

        with f_tab1:
            if critical_errors:
                for err in critical_errors:
                    ref_label = err.get("line", "Check")
                    url_link = f" — [Open on GitHub]({err['url']})" if err.get("url") else ""
                    st.error(f"**{err.get('category', 'Serious Issue')}** (`{ref_label}`): {err.get('message', '')}{url_link}")
            else:
                st.caption("No serious issues found.")

        with f_tab2:
            if warnings:
                for warn in warnings:
                    ref_label = warn.get("line", "Check")
                    url_link = f" — [Open on GitHub]({warn['url']})" if warn.get("url") else ""
                    st.warning(f"**{warn.get('category', 'Warning')}** (`{ref_label}`): {warn.get('message', '')}{url_link}")
            else:
                st.caption("No warnings or coding pattern shifts found.")

        with f_tab3:
            if notices:
                for note in notices:
                    ref_label = note.get("line", "Info")
                    url_link = f" — [Open on GitHub]({note['url']})" if note.get("url") else ""
                    st.info(f"**{note.get('category', 'Note')}** (`{ref_label}`): {note.get('message', '')}{url_link}")
            else:
                st.caption("No extra notes.")

    # --- SECTION: CHECKED GITHUB PROJECTS (WITH SOLO VS GROUP VERIFICATION) ---
    st.markdown("""
        <div class="sec-header">
            <p class="sec-title">Checked GitHub Projects (Individual vs. Group Verification)</p>
            <p class="sec-desc">Shows whether each repository is an Individual Project or a Group Project alongside the candidate's commit share</p>
        </div>
    """, unsafe_allow_html=True)

    repos = data.get("repositories", [])
    if matched_skills and repos:
        repo_cols = st.columns(2)
        for idx, repo in enumerate(repos):
            repo_name = repo.get('name', 'unnamed-repository')
            repo_url = repo.get('html_url', '#')
            stars = repo.get('stargazers_count', 0)
            lang = repo.get('language') or 'Multiple Languages'
            p_type = repo.get('project_type', 'Individual Project')
            contribs_count = repo.get('contributors_count', 1)
            share_pct = repo.get('candidate_contribution_pct', 100.0)

            if p_type == "Group Project":
                ownership_badge = f'<span class="badge-group">Group Project ({contribs_count} Contributors &bull; {share_pct}% Share)</span>'
            elif p_type == "Copied Fork":
                ownership_badge = '<span class="badge-group">Copied Fork</span>'
            else:
                ownership_badge = f'<span class="badge-solo">Individual Project (Solo &bull; {share_pct}% Authored)</span>'

            with repo_cols[idx % 2]:
                st.markdown(f"""
                    <div class="repo-item">
                        <div>
                            <a href="{repo_url}" target="_blank" class="repo-title">{repo_name} &nearr;</a>
                            <div style="margin-top: 8px;">
                                <span class="repo-lang">{lang}</span>
                                {ownership_badge}
                            </div>
                        </div>
                        <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #A1A1AA;">
                            {stars} stars
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="surface-card" style="padding: 16px 22px; border-left: 3px solid #EF4444;">
                <span style="color: #E4E4E7; font-size: 0.88rem; font-weight: 500;">
                    No public GitHub projects matched the skills written on the resume.
                </span>
            </div>
        """, unsafe_allow_html=True)