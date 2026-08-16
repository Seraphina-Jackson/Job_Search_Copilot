import streamlit as st
import pandas as pd
from db import Session, Application
from scanner import fetch_job_emails
from ai_helper import generate_interview_prep, analyze_resume_match

st.set_page_config(page_title="Job Search Copilot", page_icon="🚀", layout="wide")

# Custom Modern Styling
st.markdown("""
    <style>
    /* Global Styles */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Card Styling */
    .job-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .job-card:hover {
        border-color: #58a6ff;
        transform: translateY(-2px);
    }
    
    /* Status Badges */
    .badge-applied { background-color: #1f6feb; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .badge-interview { background-color: #d29922; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .badge-offered { background-color: #238636; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .badge-rejected { background-color: #da3633; color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    
    /* Header Gradient */
    .gradient-header {
        background: linear-gradient(90deg, #58a6ff, #bc8cff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
    }
    </style>
""", unsafe_allow_html=True)

db_session = Session()

# Title Header
st.markdown('<h1 class="gradient-header">🚀 Job Search Copilot</h1>', unsafe_allow_html=True)
st.caption("Real-time application tracking powered by smart email parsing")

# Sidebar Setup - Real-Time Sync
st.sidebar.header("⚡ Real-Time Gmail Sync")
user_email = st.sidebar.text_input("Gmail Address", value="")
app_pass = st.sidebar.text_input("App Password", type="password")

if st.sidebar.button("🔄 Sync Inbox & Sent Mail"):
    if user_email and app_pass:
        with st.spinner("Scanning Inbox and Sent folder for active applications..."):
            found_jobs = fetch_job_emails(user_email, app_pass)
            
            if found_jobs:
                added_count = 0
                for job in found_jobs:
                    existing = db_session.query(Application).filter_by(company=job["company"]).first()
                    if not existing:
                        new_app = Application(
                            company=job["company"], 
                            role="Position from Email", 
                            status=job["status"],
                            type="Domestic"
                        )
                        db_session.add(new_app)
                        added_count += 1
                
                db_session.commit()
                st.sidebar.success(f"Synced! Added {added_count} new job(s).")
                st.rerun()
            else:
                st.sidebar.info("No new application emails found.")
    else:
        st.sidebar.error("Please provide Email and App Password!")

st.sidebar.markdown("---")

# Sidebar Setup - Master Resume (Feature 2)
st.sidebar.header("📄 Your Master Resume")
master_resume = st.sidebar.text_area(
    "Paste your Resume Text (skills, projects, experience)",
    height=150,
    help="Paste text from your resume here to enable ATS Keyword Matching on cards."
)

st.sidebar.markdown("---")

# Sidebar Setup - Quick Add Job
st.sidebar.header("➕ Quick Add Job")
manual_company = st.sidebar.text_input("Company Name")
manual_role = st.sidebar.text_input("Role Title")
manual_type = st.sidebar.selectbox("Location", ["Domestic", "International"])

if st.sidebar.button("Add to Board"):
    if manual_company and manual_role:
        new_app = Application(company=manual_company, role=manual_role, type=manual_type)
        db_session.add(new_app)
        db_session.commit()
        st.sidebar.success("Added!")
        st.rerun()
    else:
        st.sidebar.error("Please fill in both Company and Role!")

st.sidebar.markdown("---")

# Clear Database Button
if st.sidebar.button("🗑️ Clear All Applications"):
    db_session.query(Application).delete()
    db_session.commit()
    st.sidebar.success("Database cleared!")
    st.rerun()

# Fetch DB Records
apps = db_session.query(Application).all()

if apps:
    # Top Stats Bar
    col1, col2, col3, col4 = st.columns(4)
    total_apps = len(apps)
    interviewing = len([a for a in apps if a.status == "Interviewing"])
    offered = len([a for a in apps if a.status == "Offered"])
    international = len([a for a in apps if a.type == "International"])

    col1.metric("Total Applications", total_apps)
    col2.metric("Interviewing", interviewing)
    col3.metric("Offers Received", offered)
    col4.metric("International", international)

    st.markdown("---")
    st.subheader("📋 Application Board")

    # Grid Display for Applications
    cols = st.columns(3)
    for idx, app in enumerate(apps):
        with cols[idx % 3]:
            # Assign CSS Badge Color based on status
            badge_class = "badge-applied"
            if app.status == "Interviewing": badge_class = "badge-interview"
            elif app.status == "Offered": badge_class = "badge-offered"
            elif app.status == "Rejected": badge_class = "badge-rejected"

            st.markdown(f"""
                <div class="job-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0; color:#58a6ff;">{app.company}</h3>
                        <span class="{badge_class}">{app.status}</span>
                    </div>
                    <p style="margin-top:8px; color: #8b949e; font-size:14px;"><strong>Role:</strong> {app.role}</p>
                    <p style="color: #8b949e; font-size:12px;">📍 {app.type}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # 1. Status Dropdown
            new_status = st.selectbox(
                "Update status", 
                ["Applied", "Interviewing", "Offered", "Rejected"], 
                index=["Applied", "Interviewing", "Offered", "Rejected"].index(app.status),
                key=f"status_{app.id}"
            )
            
            # 2. Database Update Check
            if new_status != app.status:
                app.status = new_status
                db_session.commit()
                st.rerun()

            # 3. FEATURE 1: AI Prep Sheet (Visible when status is "Interviewing")
            if app.status == "Interviewing":
                if st.button("⚡ Generate Cheat Sheet", key=f"prep_{app.id}"):
                    sheet = generate_interview_prep(app.company, app.role)
                    st.session_state[f"cheat_sheet_{app.id}"] = sheet

                if f"cheat_sheet_{app.id}" in st.session_state:
                    with st.expander("📖 View 1-Min Prep Sheet", expanded=True):
                        st.markdown(st.session_state[f"cheat_sheet_{app.id}"])

            # 4. FEATURE 2: ATS Keyword Matcher Expander
            with st.expander("🎯 ATS Keyword Matcher"):
                jd_text = st.text_area(
                    "Paste Job Description here:", 
                    key=f"jd_{app.id}", 
                    height=100
                )
                
                if st.button("📊 Calculate Match Score", key=f"score_btn_{app.id}"):
                    if not master_resume:
                        st.warning("⚠️ Please paste your Master Resume text in the sidebar first!")
                    elif not jd_text:
                        st.warning("⚠️ Please paste the Job Description above!")
                    else:
                        res = analyze_resume_match(jd_text, master_resume)
                        
                        if res:
                            score = res["score"]
                            if score >= 70:
                                st.success(f"### Match Score: {score}% ✅ (Great Match!)")
                            elif score >= 40:
                                st.warning(f"### Match Score: {score}% ⚠️ (Moderate Match)")
                            else:
                                st.error(f"### Match Score: {score}% ❌ (Low Match)")

                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("**Found in Resume:**")
                                for m in res["matched_skills"]:
                                    st.markdown(f"- ✅ {m}")
                                if not res["matched_skills"]:
                                    st.caption("None matched.")

                            with col_b:
                                st.markdown("**Missing Keywords:**")
                                for miss in res["missing_skills"]:
                                    st.markdown(f"- ❌ {miss}")
                                if not res["missing_skills"]:
                                    st.caption("No missing keywords!")
else:
    st.info("No applications logged yet. Hit 'Sync Inbox & Sent Mail' or manually add a job from the sidebar!")