import html as html_lib
import json
import re
from datetime import datetime

import streamlit as st

from backend import analyze_skills
from job_api import fetch_linkedin_jobs

from auth import (
    register_user,
    login_user,
    create_session,
    get_user_by_session,
    delete_session
)
from history import (
    save_analysis,
    get_user_history,
    get_analysis_by_id
)

# -----------------------------
# Create Database
# -----------------------------


# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="AI Career Roadmap",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="auto",
)

# -----------------------------
# Global Styles
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Deliberately NOT using `prefers-color-scheme` or Streamlit's
   --text-color/--secondary-background-color here: neither reliably
   reflects Streamlit's actual chosen app theme (a machine's OS-level
   dark-mode preference and Streamlit's own light/dark setting are
   independent, and Streamlit doesn't consistently expose its theme
   as CSS custom properties to injected <style> blocks). Streamlit's
   own default is a light main canvas with a dark sidebar chrome, so
   these custom-component colors are hardcoded to match that directly
   for guaranteed, predictable contrast. */
:root{
    --accent:#4f46e5;
    --accent-dark:#4338ca;
    --accent-light:#6366f1;
    --success:#16a34a;
    --success-bg:#dcfce7;
    --danger:#dc2626;
    --danger-bg:#fee2e2;
    --card-bg:#f8fafc;
    --text-strong:#111827;
    --muted:#6b7280;
    --donut-track:#e5e7eb;
    --radius:16px;
}

html, body, [class*="css"]{
    font-family: 'Inter', sans-serif;
}

.block-container{
    padding-top:1.75rem;
    padding-bottom:3rem;
    max-width:1200px;
}

/* ---------- Landing hero ---------- */
.landing-hero{
    text-align:center;
    padding:clamp(1.5rem, 5vw, 3rem) 1rem clamp(.75rem, 3vw, 1.25rem) 1rem;
}
.landing-hero h1{
    margin:0;
    font-size:clamp(1.6rem, 4vw, 2.35rem);
    font-weight:800;
    line-height:1.3;
}
.hero-text{
    display:inline-block;
    color:var(--text-strong);
}
.landing-subtitle{
    color:var(--muted);
    font-size:clamp(.85rem, 1.6vw, 1rem);
    max-width:600px;
    line-height:1.5;
    margin:.9rem auto 0 auto !important;
}

/* ---------- Example prompt cards ---------- */
.prompt-card{
    background:var(--card-bg);
    border:1px solid rgba(125,125,125,.15);
    border-radius:14px 14px 0 0;
    border-bottom:none;
    padding:1rem 1.05rem .8rem 1.05rem;
    min-height:118px;
}
.prompt-icon{font-size:1.35rem;margin-bottom:.45rem;}
.prompt-title{font-weight:700;font-size:.92rem;color:var(--text-strong);margin-bottom:.3rem;}
.prompt-desc{font-size:.78rem;color:var(--muted);line-height:1.4;}
div[data-testid="stColumn"]:has(.prompt-card) .stButton>button{
    border-radius:0 0 14px 14px !important;
    border:1px solid rgba(125,125,125,.15) !important;
    border-top:none !important;
    background:var(--card-bg) !important;
    color:var(--accent) !important;
    font-weight:600;
    font-size:.78rem;
    box-shadow:none !important;
    padding:.5rem 1rem !important;
}
div[data-testid="stColumn"]:has(.prompt-card) .stButton>button:hover{
    background:rgba(79,70,229,.08) !important;
    transform:none;
}

/* ---------- Auth card ---------- */
.auth-card{
    text-align:center;
    padding:.5rem 0 1rem 0;
}
.auth-logo{
    width:56px;height:56px;border-radius:16px;
    background:linear-gradient(135deg, var(--accent), #7c3aed);
    display:flex;align-items:center;justify-content:center;
    font-size:1.6rem;margin:0 auto .75rem auto;
    box-shadow:0 8px 20px -8px rgba(79,70,229,.6);
}
.auth-card h1{
    font-size:1.5rem;font-weight:800;margin:0 0 .35rem 0;
    color:var(--text-strong);
}
.auth-subtitle{
    color:var(--muted);font-size:.9rem;margin:0;
}

/* ---------- Buttons ---------- */
.stButton>button{
    width:100%;
    border-radius:10px;
    background:linear-gradient(135deg, var(--accent), var(--accent-dark));
    color:#fff;
    border:none;
    font-weight:600;
    padding:.6rem 1rem;
    transition:transform .12s ease, box-shadow .12s ease, opacity .12s ease;
    box-shadow:0 4px 12px -4px rgba(79,70,229,.5);
}
.stButton>button:hover{
    transform:translateY(-1px);
    box-shadow:0 8px 18px -6px rgba(79,70,229,.6);
    opacity:.96;
}
.stButton>button:active{
    transform:translateY(0);
}

/* ---------- Inputs ---------- */
.stTextInput input, .stTextArea textarea{
    border-radius:10px !important;
    font-size:16px;
}
.stTextInput input:focus, .stTextArea textarea:focus{
    border-color:var(--accent) !important;
    box-shadow:0 0 0 1px var(--accent) !important;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"]{
    gap:.5rem;
}
.stTabs [data-baseweb="tab"]{
    border-radius:8px 8px 0 0;
    font-weight:600;
}
.stTabs [aria-selected="true"]{
    color:var(--accent) !important;
}

/* ---------- Chips ---------- */
.chip-row{
    display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.5rem;
}
.chip{
    display:inline-flex;align-items:center;gap:.4rem;
    padding:.38rem .85rem .48rem .85rem;border-radius:999px;
    font-size:.85rem;font-weight:600;line-height:1;
    white-space:nowrap;
}
.chip-matched{background:var(--success-bg);color:var(--success);border:1px solid rgba(22,163,74,.25);}
.chip-missing{background:var(--danger-bg);color:var(--danger);border:1px solid rgba(220,38,38,.25);}
.chip-role{background:rgba(79,70,229,.1);color:var(--accent);border:1px solid rgba(79,70,229,.25);}
.chip-empty{color:var(--muted);font-size:.9rem;font-weight:500;margin-top:.5rem;}

/* ---------- Score donut ---------- */
.score-donut{
    width:150px;height:150px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    margin:.25rem auto;
}
.score-donut-inner{
    width:118px;height:118px;border-radius:50%;
    background:var(--card-bg);
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    text-align:center;
}
.score-value{font-size:1.5rem;font-weight:800;color:var(--text-strong);}
.score-label{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:.15rem;}

/* ---------- Roadmap timeline ---------- */
.roadmap{list-style:none;margin:.5rem 0 0 0;padding:0;}
.roadmap li{
    position:relative;padding:.35rem 0 1rem 2.35rem;
    color:var(--text-strong);
}
.roadmap li::before{
    content:attr(data-step);
    position:absolute;left:0;top:.15rem;
    width:1.7rem;height:1.7rem;border-radius:50%;
    background:linear-gradient(135deg, var(--accent), #7c3aed);
    color:#fff;font-size:.78rem;font-weight:700;
    display:flex;align-items:center;justify-content:center;
}
.roadmap li::after{
    content:"";position:absolute;left:.85rem;top:1.9rem;bottom:0;
    width:2px;background:rgba(125,125,125,.25);
}
.roadmap li:last-child::after{display:none;}
.roadmap li:last-child{padding-bottom:.35rem;}

/* ---------- Job cards ---------- */
.job-grid{
    display:grid;
    grid-template-columns:repeat(auto-fill, minmax(250px, 1fr));
    gap:1rem;margin-top:.5rem;
}
.job-card{
    background:var(--card-bg);
    border:1px solid rgba(125,125,125,.15);
    border-radius:14px;padding:1rem 1.1rem;
    transition:transform .15s ease, box-shadow .15s ease;
}
.job-card:hover{
    transform:translateY(-3px);
    box-shadow:0 10px 24px -10px rgba(0,0,0,.25);
}
.job-card h4{margin:0 0 .5rem 0;font-size:1rem;color:var(--text-strong);}
.job-card .job-meta{font-size:.85rem;color:var(--muted);margin:.15rem 0;}
.job-card a.job-link{
    display:inline-block;margin-top:.65rem;font-size:.85rem;
    font-weight:700;color:var(--accent);text-decoration:none;
}
.job-card a.job-link:hover{text-decoration:underline;}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] > div{
    padding-top:.5rem;
}
.user-card{
    display:flex;align-items:center;gap:.6rem;min-width:0;
    padding:.6rem .7rem;border-radius:14px;
    background:#ffffff;
    border:1px solid rgba(15,23,42,.1);
    height:100%;box-sizing:border-box;
}
.user-avatar{
    width:38px;height:38px;border-radius:50%;flex-shrink:0;
    background:linear-gradient(135deg, var(--accent), #7c3aed);
    color:#fff;display:flex;align-items:center;justify-content:center;
    font-weight:700;font-size:.9rem;
}
.user-info{min-width:0;}
.user-name{
    font-weight:700;font-size:.88rem;color:var(--text-strong);
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.user-email{
    font-size:.72rem;color:var(--muted);
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}

/* Logout icon button sits beside the user card, so it's square/compact
   rather than the full-width style every other sidebar button uses. */
div[data-testid="stColumn"]:has(.logout-col-marker) .stButton>button{
    height:52px;
    padding:0 !important;
    font-size:1.05rem;
    text-align:center;
    justify-content:center;
}

.sidebar-heading{
    font-size:.75rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
    color:var(--muted);margin:1.2rem .1rem .55rem .1rem;
}
.sidebar-empty{
    font-size:.82rem;color:var(--muted);line-height:1.5;margin:0;
}

section[data-testid="stSidebar"] .stButton>button{
    background:#ffffff !important;
    color:var(--text-strong) !important;
    box-shadow:none !important;
    border:1px solid rgba(15,23,42,.12) !important;
    text-align:left;
    justify-content:flex-start;
    font-weight:500;
    font-size:.83rem;
    display:block;
    height:auto;
    padding-top:.5rem;
    padding-bottom:.5rem;
}
section[data-testid="stSidebar"] .stButton>button *{
    color:inherit !important;
}
/* History entries render as two markdown paragraphs (title, then
   date/score) — style them as a title + muted subtitle, each
   truncating on its own line rather than the whole button clipping. */
section[data-testid="stSidebar"] .stButton>button div[data-testid="stMarkdownContainer"] p{
    margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
section[data-testid="stSidebar"] .stButton>button div[data-testid="stMarkdownContainer"] p:first-child{
    font-weight:700;font-size:.85rem;
}
section[data-testid="stSidebar"] .stButton>button div[data-testid="stMarkdownContainer"] p:not(:first-child):not(:only-child){
    font-weight:400;font-size:.72rem;opacity:.65;margin-top:.15rem;
}
section[data-testid="stSidebar"] .stButton>button:hover{
    border-color:var(--accent) !important;
    color:var(--accent) !important;
    background:rgba(79,70,229,.08) !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]{
    background:linear-gradient(135deg, var(--accent), #7c3aed) !important;
    color:#fff !important;
    border-color:transparent !important;
}

/* ---------- Small screens ---------- */
@media (max-width: 640px){
    .block-container{padding-left:1rem;padding-right:1rem;}
    .landing-hero{padding:1rem .5rem .5rem .5rem;}
    .score-donut{width:120px;height:120px;}
    .score-donut-inner{width:94px;height:94px;}
    .score-value{font-size:1.15rem;}
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Example starter prompts (click to prefill the form)
# -----------------------------
EXAMPLE_PROMPTS = [
    {
        "icon": "📊",
        "title": "Data Analyst",
        "desc": "See how your skills map to a Data Analyst role",
        "skills": "Python, SQL, Excel, Power BI, Data Cleaning, Statistics",
        "jd": "We are looking for a Data Analyst to interpret data, analyze results "
              "using statistical techniques, and provide ongoing reports. Requirements: "
              "SQL, Excel, Power BI or Tableau, strong analytical skills, and experience "
              "with Python for data analysis.",
    },
    {
        "icon": "💻",
        "title": "Software Engineer",
        "desc": "Check your fit for a Software Engineer opening",
        "skills": "Python, Java, Git, REST APIs, Object-Oriented Programming, SQL",
        "jd": "We are hiring a Software Engineer to design, build and maintain scalable "
              "backend services. Requirements: strong experience with Python or Java, "
              "REST API design, version control with Git, and relational databases.",
    },
    {
        "icon": "🧠",
        "title": "Data Scientist",
        "desc": "Find your skill gaps for a Data Scientist role",
        "skills": "Python, Pandas, scikit-learn, Statistics, SQL, Machine Learning",
        "jd": "We are seeking a Data Scientist to build predictive models and extract "
              "insights from large datasets. Requirements: strong Python skills, "
              "experience with machine learning libraries, statistics, and SQL.",
    },
    {
        "icon": "🎨",
        "title": "Product Designer",
        "desc": "Explore a Product Designer career path",
        "skills": "Figma, UX Research, Wireframing, Prototyping, Design Systems",
        "jd": "We are looking for a Product Designer to craft intuitive user experiences. "
              "Requirements: proficiency in Figma, experience with user research, "
              "wireframing, prototyping, and building design systems.",
    },
]


# -----------------------------
# Render helpers
# -----------------------------
def esc(text):
    return html_lib.escape(str(text))


def history_title(recommended_jobs_json, skills):
    try:
        jobs = json.loads(recommended_jobs_json) if recommended_jobs_json else []
    except (TypeError, ValueError):
        jobs = []
    if jobs:
        return jobs[0]
    if skills:
        return skills.split(",")[0].strip()[:40]
    return "Analysis"


def format_history_label(created_at, score, title):
    try:
        dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        when = dt.strftime("%b %d, %Y · %I:%M %p")
    except (TypeError, ValueError):
        when = str(created_at)
    return f"{title}\n\n{when}  —  {score}"


def render_chips(items, kind, icon):
    if not items:
        st.markdown('<p class="chip-empty">Nothing to show here.</p>', unsafe_allow_html=True)
        return
    chips = "".join(
        f'<span class="chip chip-{kind}">{icon} {esc(item)}</span>' for item in items
    )
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def render_roadmap(steps):
    if not steps:
        st.info("No roadmap steps available.")
        return
    items = "".join(
        f'<li data-step="{i + 1}">{esc(step)}</li>' for i, step in enumerate(steps)
    )
    st.markdown(f'<ul class="roadmap">{items}</ul>', unsafe_allow_html=True)


def render_score_gauge(score_text):
    match = re.search(r"\d+(\.\d+)?", str(score_text) if score_text else "")
    pct = max(0.0, min(100.0, float(match.group()))) if match else 0.0
    display_text = score_text if score_text else "N/A"
    st.markdown(f"""
    <div class="score-donut" style="background: conic-gradient(var(--accent) {pct}%, var(--donut-track) {pct}% 100%);">
        <div class="score-donut-inner">
            <span class="score-value">{esc(display_text)}</span>
            <span class="score-label">Match Score</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_linkedin_jobs(jobs):
    if not jobs:
        st.warning("No LinkedIn jobs found.")
        return
    # Built as single-line HTML per card (no embedded blank lines): Streamlit's
    # markdown parser stays in raw-HTML mode only until the first blank line,
    # after which indented lines get treated as a Markdown code block instead
    # of HTML and render as literal text.
    card_parts = []
    for job in jobs:
        title = esc(job.get("title", "No Title"))
        company = esc(job.get("company", "Unknown"))
        location = esc(job.get("location", "Unknown"))
        link = job.get("link", "")
        link_html = (
            f'<a class="job-link" href="{esc(link)}" target="_blank" rel="noopener noreferrer">View Job →</a>'
            if link else ""
        )
        card_parts.append(
            f'<div class="job-card"><h4>{title}</h4>'
            f'<div class="job-meta">🏢 {company}</div>'
            f'<div class="job-meta">📍 {location}</div>'
            f'{link_html}</div>'
        )
    st.markdown(f'<div class="job-grid">{"".join(card_parts)}</div>', unsafe_allow_html=True)


def render_analysis_report(match_score, matched_skills, missing_skills, roadmap,
                            recommended_jobs, linkedin_jobs=None):
    gauge_col, summary_col = st.columns([1, 2], gap="large")
    with gauge_col:
        render_score_gauge(match_score)
    with summary_col:
        st.markdown(f"""
        <div style="padding-top:.5rem;">
            <p style="margin:.2rem 0;">✅ <strong>{len(matched_skills)}</strong> skills matched</p>
            <p style="margin:.2rem 0;">⚠️ <strong>{len(missing_skills)}</strong> skills to develop</p>
            <p style="margin:.2rem 0;">🛣 <strong>{len(roadmap)}</strong>-step roadmap generated</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🎯 Skills Gap")
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.markdown("**Matched Skills**")
        render_chips(matched_skills, "matched", "✅")
    with col_b:
        st.markdown("**Missing Skills**")
        render_chips(missing_skills, "missing", "❌")

    st.divider()
    st.markdown("#### 🛣 Roadmap")
    render_roadmap(roadmap)

    st.divider()
    st.markdown("#### 💼 Job Roles")
    render_chips(recommended_jobs, "role", "💼")

    st.divider()
    st.markdown("#### 🔗 LinkedIn Jobs")
    render_linkedin_jobs(linkedin_jobs or [])


# -----------------------------
# Session State
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# Restore login from the session token in the URL (survives page reloads)
if not st.session_state.logged_in:
    session_token = st.query_params.get("session")
    if session_token:
        restored_user = get_user_by_session(session_token)
        if restored_user:
            st.session_state.logged_in = True
            st.session_state.user = restored_user

# ============================================================
# LOGIN / REGISTER
# ============================================================
if not st.session_state.logged_in:
    left, center, right = st.columns([1, 1.3, 1])
    with center:
        st.markdown("""
        <div class="auth-card">
            <div class="auth-logo">🔐</div>
            <h1>AI Career Roadmap</h1>
            <p class="auth-subtitle">Sign in to analyze your skills and discover your next career move.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            login_tab, register_tab = st.tabs(["Login", "Register"])

            # ---------------- Login ----------------
            with login_tab:
                email = st.text_input("Email", key="login_email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
                if st.button("Login", key="login_btn"):
                    if email and password:
                        user = login_user(email, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.query_params["session"] = create_session(user["_id"])

                            if "selected_analysis" in st.session_state:
                                del st.session_state["selected_analysis"]

                            st.success("Login Successful!")
                            st.rerun()
                        else:
                            st.error("Invalid Email or Password")
                    else:
                        st.warning("Please enter both email and password.")

            # ---------------- Register ----------------
            with register_tab:
                full_name = st.text_input("Full Name", key="reg_name", placeholder="Jane Doe")
                reg_email = st.text_input("Email", key="reg_email", placeholder="you@example.com")
                reg_password = st.text_input("Password", type="password", key="reg_password", placeholder="Create a password")
                if st.button("Create Account", key="reg_btn"):
                    if full_name and reg_email and reg_password:
                        success, message = register_user(full_name, reg_email, reg_password)
                        if success:
                            st.success(f"{message} You can now log in.")
                        else:
                            st.error(message)
                    else:
                        st.warning("Please fill in all fields.")

# ============================================================
# AFTER LOGIN
# ============================================================
else:
    user_id = st.session_state.user["_id"]
    full_name = st.session_state.user["full_name"]
    user_email = st.session_state.user["email"]
    initials = "".join(part[0].upper() for part in full_name.split()[:2]) or "U"

    with st.sidebar:
        # -----------------------------
        # User card + Logout (side by side)
        # -----------------------------
        user_col, logout_col = st.columns([4, 1], vertical_alignment="center")
        with user_col:
            st.markdown(f"""
            <div class="user-card">
                <div class="user-avatar">{esc(initials)}</div>
                <div class="user-info">
                    <div class="user-name">{esc(full_name)}</div>
                    <div class="user-email">{esc(user_email)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with logout_col:
            st.markdown('<div class="logout-col-marker"></div>', unsafe_allow_html=True)
            if st.button("", key="logout_btn", use_container_width=True, help="Logout", icon=":material/logout:"):
                session_token = st.query_params.get("session")
                if session_token:
                    delete_session(session_token)
                st.query_params.clear()
                st.session_state.logged_in = False
                st.session_state.user = None
                if "selected_analysis" in st.session_state:
                    del st.session_state["selected_analysis"]
                st.rerun()

        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

        # -----------------------------
        # New Chat Button
        # -----------------------------
        if st.button("✚ New Chat", key="new_chat_btn", use_container_width=True, type="primary"):
            if "selected_analysis" in st.session_state:
                del st.session_state["selected_analysis"]
            for text_key in ("skills_input", "jd_input"):
                if text_key in st.session_state:
                    del st.session_state[text_key]
            st.rerun()

        # -----------------------------
        # Analysis History
        # -----------------------------
        st.markdown('<div class="sidebar-heading">📜 Analysis History</div>', unsafe_allow_html=True)
        history = get_user_history(user_id)
        if history:
            for item in history:

                analysis_id, score, recommended_jobs, skills = item

                title = history_title(json.dumps(recommended_jobs), skills)

                is_active = st.session_state.get("selected_analysis") == analysis_id

                if st.button(
                    format_history_label("Recent", score, title),
                    key=f"history_{analysis_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.selected_analysis = analysis_id
                    st.rerun()
        else:
            st.markdown(
                '<p class="sidebar-empty">No analyses yet.<br>Run your first analysis to see it here.</p>',
                unsafe_allow_html=True,
            )

    # ------------------------------------------------
    # Previous Analysis Report — when viewing history, this is the ONLY
    # thing shown (no homepage/new-chat content underneath it). Use
    # the sidebar's "New Chat" button to get back to the homepage.
    # ------------------------------------------------
    show_homepage = True
    if "selected_analysis" in st.session_state:
        report = get_analysis_by_id(user_id, st.session_state.selected_analysis)
        if report:
            show_homepage = False

            with st.container(border=True):

                st.markdown("#### 📜 Previous Analysis")

                render_analysis_report(
                    match_score=report.get("match_score", "N/A"),
                    matched_skills=report.get("matched_skills", []),
                    missing_skills=report.get("missing_skills", []),
                    roadmap=report.get("career_roadmap", []),
                    recommended_jobs=report.get("recommended_jobs", []),
                    linkedin_jobs=report.get("linkedin_jobs", []),
                )
        else:
            del st.session_state["selected_analysis"]

    if show_homepage:
        # ------------------------------------------------
        # Landing hero
        # ------------------------------------------------
        first_name = full_name.split()[0] if full_name else "there"
        st.markdown(f"""
        <div class="landing-hero">
            <h1><span class="hero-text">Hey {esc(first_name)}</span> 👋</h1>
            <h1><span class="hero-text">What role are you aiming for?</span></h1>
            <p class="landing-subtitle">Paste your skills and a job description below — I'll score your match,
            map out the gaps, and build you a learning roadmap with real LinkedIn openings.</p>
        </div>
        """, unsafe_allow_html=True)

        # ------------------------------------------------
        # Example starter cards (click to prefill the form)
        # ------------------------------------------------
        example_cols = st.columns(4, gap="medium")
        for col, prompt in zip(example_cols, EXAMPLE_PROMPTS):
            with col:
                st.markdown(f"""
                <div class="prompt-card">
                    <div class="prompt-icon">{prompt['icon']}</div>
                    <div class="prompt-title">{esc(prompt['title'])}</div>
                    <div class="prompt-desc">{esc(prompt['desc'])}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Use example", key=f"example_{prompt['title']}", use_container_width=True):
                    st.session_state["skills_input"] = prompt["skills"]
                    st.session_state["jd_input"] = prompt["jd"]

        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

        # ------------------------------------------------
        # Input Form
        # ------------------------------------------------
        with st.container(border=True):
            col1, col2 = st.columns(2, gap="large")
            with col1:
                user_skills = st.text_area(
                    "Enter Your Skills",
                    height=180,
                    key="skills_input",
                    placeholder="e.g. Python, SQL, Pandas, Power BI, Communication..."
                )
            with col2:
                job_description = st.text_area(
                    "Enter Job Description",
                    height=180,
                    key="jd_input",
                    placeholder="Paste the full job description you're targeting..."
                )
            analyze = st.button("🚀 Analyze My Career")

        # ------------------------------------------------
        # Run Analysis
        # ------------------------------------------------
        if analyze:
            if user_skills and job_description:
                try:
                    with st.spinner("Analyzing..."):
                        if "selected_analysis" in st.session_state:
                            del st.session_state["selected_analysis"]

                        result = analyze_skills(user_skills, job_description)

                    jobs = result.get("recommended_jobs", [])
                    linkedin_jobs = []
                    if jobs:
                        linkedin_query = ", ".join(jobs[:3])
                        try:
                            with st.spinner("Fetching LinkedIn Jobs..."):
                                linkedin_jobs = fetch_linkedin_jobs(
                                    linkedin_query,
                                    location="Bangladesh",
                                    rows=10
                                )
                        except Exception as e:
                            st.warning("LinkedIn jobs could not be fetched.")
                            st.error(str(e))

                    save_analysis(user_id, user_skills, job_description, result, linkedin_jobs)

                    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
                    st.markdown("### 📊 Your Results")
                    with st.container(border=True):
                        render_analysis_report(
                            match_score=result.get("match_score", "N/A"),
                            matched_skills=result.get("matched_skills", []),
                            missing_skills=result.get("missing_skills", []),
                            roadmap=result.get("career_roadmap", []),
                            recommended_jobs=jobs,
                            linkedin_jobs=linkedin_jobs,
                        )
                except Exception as e:
                    st.error("Something went wrong.")
                    st.error(str(e))
            else:
                st.warning("Please enter both Skills and Job Description.")
