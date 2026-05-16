import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

try:
    from streamlit_option_menu import option_menu
    HAS_OPTION_MENU = True
except ImportError:
    HAS_OPTION_MENU = False

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Clarity AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── White & Neon Green Theme ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Global Reset */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: #334155 !important; /* Slate 700 */
    background-color: #FFFFFF !important;
}

/* Pure White Background with Subtle Neon Green Glows */
.stApp {
    background-image: 
        radial-gradient(circle at 85% 0%, rgba(0, 255, 102, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 15% 100%, rgba(0, 255, 102, 0.05) 0%, transparent 40%);
    background-attachment: fixed;
}

/* Hide Streamlit Cruft */
header { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* Crisp Light Sidebar */
[data-testid="stSidebar"] {
    background: #F8FAFC !important; /* Slate 50 */
    border-right: 1px solid #E2E8F0 !important;
    min-width: 260px !important;
    max-width: 260px !important;
}

/* Remove Unnecessary Empty Spaces */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px !important;
}

/* Modern Typography Hierarchy */
.startup-title {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -0.04em;
    color: #000000; 
    margin-bottom: 4px;
    line-height: 1.2;
}
.startup-subtitle {
    font-size: 16px;
    color: #64748B; /* Slate 500 */
    margin-bottom: 32px;
    font-weight: 500;
}

/* Clean White Cards */
.premium-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 24px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
}
.premium-card:hover {
    border-color: #00FF66; /* Neon Green */
    box-shadow: 0 12px 30px rgba(0, 255, 102, 0.15);
    transform: translateY(-4px);
}

.metric-title {
    font-size: 13px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #000000;
    line-height: 1.1;
}

/* Dataframe & Plotly Overrides */
[data-testid="stDataFrame"] { background: transparent !important; }
[data-testid="stDataFrame"] > div {
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    background: #FFFFFF !important;
}
.js-plotly-plot {
    border-radius: 16px;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    padding: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    transition: all 0.3s ease;
}
.js-plotly-plot:hover {
    border-color: #00FF66;
    box-shadow: 0 12px 30px rgba(0, 255, 102, 0.15);
}

/* Inputs and Controls */
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stChatInput > div {
    background-color: #FFFFFF !important;
    border: 2px solid #E2E8F0 !important;
    color: #000000 !important;
    border-radius: 10px !important;
    padding: 14px 16px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stTextInput > div > div > input:focus, .stChatInput > div:focus-within {
    border-color: #00FF66 !important;
    box-shadow: 0 0 0 4px rgba(0, 255, 102, 0.2) !important;
}

/* Neon Green Buttons */
.stButton > button[kind="primary"] {
    background: #00FF66 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 14px rgba(0, 255, 102, 0.3) !important;
    text-transform: uppercase;
    letter-spacing: 0.02em;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 255, 102, 0.5) !important;
    background: #00E65C !important;
}
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #000000 !important;
    border: 2px solid #E2E8F0 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #00FF66 !important;
    color: #000000 !important;
    background: rgba(0, 255, 102, 0.05) !important;
}

/* Minimalist AI Chatbot */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 24px;
    margin-bottom: 32px;
}
.chat-row {
    display: flex;
    gap: 16px;
    align-items: flex-start;
}
.chat-avatar {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 700;
    flex-shrink: 0;
}
.chat-avatar.user { background: #F1F5F9; color: #000000; border: 1px solid #E2E8F0; }
.chat-avatar.ai { background: #00FF66; color: #000000; box-shadow: 0 4px 10px rgba(0,255,102,0.3); }
.chat-content {
    flex-grow: 1;
    color: #1E293B;
    font-size: 16px;
    line-height: 1.6;
    padding-top: 6px;
}

/* High-Contrast Badges */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    color: #000000;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}
.status-indicator.green { background: #00FF66; box-shadow: 0 0 12px #00FF66; }
.status-indicator.red { background: #FF0044; box-shadow: 0 0 12px #FF0044; }

/* Interactive Upload Area — Full Override */
[data-testid="stFileUploader"] {
    background: #FFFFFF !important;
    border: 2px dashed #CBD5E1 !important;
    border-radius: 16px !important;
    padding: 32px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #00FF66 !important;
    background: rgba(0, 255, 102, 0.02) !important;
    box-shadow: 0 10px 30px rgba(0, 255, 102, 0.1) !important;
}
/* Fix the dark inner drag section */
[data-testid="stFileUploader"] > div {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
[data-testid="stFileUploader"] section {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
}
/* Style the inner upload button to Neon Green */
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploader"] button {
    background: #00FF66 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 12px rgba(0,255,102,0.3) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFileUploaderDropzone"] button:hover,
[data-testid="stFileUploader"] button:hover {
    box-shadow: 0 6px 20px rgba(0,255,102,0.5) !important;
    transform: translateY(-1px) !important;
}
/* Fix the text color inside uploader */
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span {
    color: #64748B !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Neon Green & White Plotly Theme ───────────────────────────────────────────
CHART_THEME = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#64748B", size=13),
    margin=dict(l=10, r=10, t=30, b=10),
)
# Neon Green, Obsidian, Slate Colors
COLORS = ["#00FF66", "#0F172A", "#334155", "#94A3B8", "#00E65C"]

# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_currency(val):
    if val >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    elif val >= 1_000:
        return f"${val/1_000:.1f}K"
    return f"${val:.2f}"

def api_get(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return None

def api_post(endpoint, data=None, files=None):
    try:
        if files:
            r = requests.post(f"{API_URL}{endpoint}", files=files, timeout=60)
        else:
            r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=60)
        r.raise_for_status()
        return r.json()
    except:
        return None

def style_fig(fig):
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9', zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9', zeroline=False)
    return fig


# ── Elegant Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;padding:8px 4px;">
            <div style="background:#000000; color:#00FF66; width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">⚡</div>
            <div style="font-size:20px; font-weight:800; color:#000000; letter-spacing:-0.03em;">Clarity AI</div>
        </div>
        <div style="font-size:11px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:12px; padding-left:8px;">Main Menu</div>
    """, unsafe_allow_html=True)
    
    if HAS_OPTION_MENU:
        page = option_menu(
            menu_title=None,
            options=["Data Upload", "Dashboard", "AI Copilot", "Forecast", "Anomalies", "Reports"],
            icons=["cloud-upload", "grid", "chat-square", "graph-up", "shield-exclamation", "file-earmark-pdf"],
            menu_icon="cast",
            default_index=1,
            styles={
                "container": {
                    "padding": "0!important", 
                    "background-color": "#F8FAFC", # Match sidebar background explicitly
                    "border": "none"
                },
                "icon": {
                    "font-size": "16px", 
                    "margin-right": "12px"
                }, 
                "nav-link": {
                    "font-size": "15px", 
                    "text-align": "left", 
                    "margin": "4px 0", 
                    "color": "#334155", 
                    "font-weight": "600", 
                    "border-radius": "10px", 
                    "padding": "12px 14px", 
                    "font-family": "system-ui, -apple-system, sans-serif", 
                    "transition": "all 0.2s ease"
                },
                "nav-link-selected": {
                    "background-color": "#00FF66", 
                    "color": "#000000", 
                    "font-weight": "800", 
                    "box-shadow": "0 4px 12px rgba(0,255,102,0.2)"
                },
                "nav-link:hover": {
                    "background-color": "rgba(0, 255, 102, 0.1)",
                    "color": "#000000"
                }
            }
        )
    else:
        page = st.radio("Navigation", ["Data Upload", "Dashboard", "AI Copilot", "Forecast", "Anomalies", "Reports"], label_visibility="collapsed")
    
    st.markdown("<div style='margin-top:auto;padding-top:60px;'></div>", unsafe_allow_html=True)
    
    # Premium Workspace / User Profile Widget
    st.markdown("""
        <div style="margin-bottom: 24px; padding: 12px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="width: 36px; height: 36px; border-radius: 50%; background: #F1F5F9; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #000000; border: 1px solid #E2E8F0;">
                JD
            </div>
            <div style="line-height: 1.2;">
                <div style="font-size: 13px; font-weight: 700; color: #000000;">John Doe</div>
                <div style="font-size: 11px; font-weight: 600; color: #64748B;">Admin Workspace</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        ping = requests.get(f"{API_URL}/", timeout=2)
        if ping.status_code == 200:
            st.markdown('<div class="status-badge" style="width:100%; justify-content:center;"><div class="status-indicator green"></div> System Online</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge" style="width:100%; justify-content:center;"><div class="status-indicator red"></div> Offline</div>', unsafe_allow_html=True)
    except:
        st.markdown('<div class="status-badge" style="width:100%; justify-content:center;"><div class="status-indicator red"></div> Offline</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Upload
# ══════════════════════════════════════════════════════════════════════════════
if page == "Data Upload":
    st.markdown('<div class="startup-title">Data Integration</div>', unsafe_allow_html=True)
    st.markdown('<div class="startup-subtitle">Upload and sanitize raw CSV files through the automated ML pipeline.</div>', unsafe_allow_html=True)

    # Premium upload dropzone header
    st.markdown("""
    <div style="
        border: 2px dashed #CBD5E1;
        border-radius: 16px;
        padding: 40px 32px 20px;
        background: #FFFFFF;
        text-align: center;
        margin-bottom: -20px;
        transition: all 0.3s ease;
    ">
        <div style="font-size: 40px; margin-bottom: 12px;">☁️</div>
        <div style="font-size: 17px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">
            Drop your CSV file here
        </div>
        <div style="font-size: 14px; color: #94A3B8; margin-bottom: 20px; font-weight: 500;">
            Supports <b style="color:#64748B">CSV</b> files up to 200MB · Auto-cleansed &amp; validated
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("", type=["csv"], label_visibility="collapsed")

    if uploaded:
        with st.spinner("Processing through neural pipeline..."):
            result = api_post("/upload", files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")})

        if result:
            report = result.get("cleaning_report", {})
            db     = result.get("database", {})

            st.markdown(f'''
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 32px;">
                <div class="premium-card">
                    <div class="metric-title">Rows Ingested</div>
                    <div class="metric-value">{db.get('rows', 0):,}</div>
                </div>
                <div class="premium-card">
                    <div class="metric-title">Features</div>
                    <div class="metric-value">{len(db.get("columns", []))}</div>
                </div>
                <div class="premium-card">
                    <div class="metric-title">Anomalies Fixed</div>
                    <div class="metric-value">{len(report.get("issues_found", []))}</div>
                </div>
                <div class="premium-card" style="border-color:#00FF66;">
                    <div class="metric-title">Quality Score</div>
                    <div class="metric-value" style="color:#00D859;">{report.get('data_quality_score', 0)}%</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            st.markdown("<div style='font-size:14px; color:#64748B; margin-bottom:8px; font-weight:600;'>Detected Schema</div>", unsafe_allow_html=True)
            cols = db.get("columns", [])
            st.code(", ".join(cols), language=None)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Dashboard
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Dashboard":
    st.markdown('<div class="startup-title">Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="startup-subtitle">Real-time telemetry and financial intelligence.</div>', unsafe_allow_html=True)

    with st.spinner("Fetching live metrics..."):
        data = api_get("/dashboard")

    if data:
        kpis   = data.get("kpis", {})
        charts = data.get("charts", {})

        st.markdown(f'''
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 32px;">
            <div class="premium-card">
                <div class="metric-title">Gross Revenue</div>
                <div class="metric-value">{fmt_currency(kpis.get("total_revenue",0))}</div>
            </div>
            <div class="premium-card">
                <div class="metric-title">Net Profit</div>
                <div class="metric-value">{fmt_currency(kpis.get("total_profit",0))}</div>
            </div>
            <div class="premium-card" style="border-color:#00FF66;">
                <div class="metric-title">Margin</div>
                <div class="metric-value" style="color:#00D859;">{kpis.get("profit_margin",0):.1f}%</div>
            </div>
            <div class="premium-card">
                <div class="metric-title">Orders</div>
                <div class="metric-value">{kpis.get("total_orders",0):,}</div>
            </div>
            <div class="premium-card">
                <div class="metric-title">Active Users</div>
                <div class="metric-value">{kpis.get("unique_customers",0):,}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        monthly = charts.get("monthly_revenue", [])
        if monthly:
            df_m = pd.DataFrame(monthly)
            fig = px.area(df_m, x="month", y="sales", title="Revenue Velocity", color_discrete_sequence=[COLORS[0]])
            fig.update_traces(fill="tozeroy", fillcolor="rgba(0, 255, 102, 0.15)", line=dict(width=3, color="#00FF66"))
            fig.update_layout(**CHART_THEME)
            st.plotly_chart(style_fig(fig), use_container_width=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            region = charts.get("sales_by_region", [])
            if region:
                df_r = pd.DataFrame(region)
                total_sales = df_r["sales"].sum()
                fig = px.pie(
                    df_r, values="sales", names="region", 
                    title="Market Share", 
                    color_discrete_sequence=COLORS, 
                    hole=0.8
                )
                fig.update_traces(
                    textposition='outside', 
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>%{value:$,.0f}<br>%{percent}',
                    marker=dict(line=dict(color='#FFFFFF', width=3))
                )
                fig.update_layout(
                    **CHART_THEME,
                    showlegend=False,
                    annotations=[dict(
                        text=f"Total<br><b style='color:#000000;font-size:24px;'>{fmt_currency(total_sales)}</b>", 
                        x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#64748B")
                    )]
                )
                st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — AI Chat
# ══════════════════════════════════════════════════════════════════════════════
elif page == "AI Copilot":
    st.markdown('<div class="startup-title">AI Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="startup-subtitle">Interact with your data warehouse via advanced LLM synthesis.</div>', unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if not st.session_state.chat_history:
        st.markdown("<div style='font-size:14px;color:#64748B;margin-bottom:12px;font-weight:700;text-transform:uppercase;'>Quick Actions</div>", unsafe_allow_html=True)
        examples = ["Analyze Q3 revenue drop", "Show highest margin region", "Identify top 5 customers"]
        cols = st.columns(len(examples))
        for i, ex in enumerate(examples):
            if cols[i].button(ex, key=f"ex_{i}", use_container_width=True, type="secondary"):
                st.session_state["prefill"] = ex

    if st.session_state.chat_history:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'''
                <div class="chat-row">
                    <div class="chat-avatar user">U</div>
                    <div class="chat-content">{msg["content"]}</div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="chat-row">
                    <div class="chat-avatar ai">⚡</div>
                    <div class="chat-content">{msg["content"]}</div>
                </div>
                ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    prefill = st.session_state.pop("prefill", "")
    question = st.chat_input("Ask your Copilot...")

    if question or prefill:
        q = question or prefill
        st.session_state.chat_history.append({"role": "user", "content": q})
        st.rerun()

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        q = st.session_state.chat_history[-1]["content"]
        with st.spinner("Synthesizing..."):
            result = api_post("/query", data={"question": q})

        if result:
            answer = result.get("answer", "Analysis failed.")
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Forecast
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Forecast":
    st.markdown('<div class="startup-title">Predictive Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="startup-subtitle">Algorithmic sales velocity projections based on historical data.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c1:
        days = st.slider("Projection Horizon (Days)", min_value=7, max_value=90, value=30, step=7)
    with c2:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        run_btn = st.button("Initialize Model", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Training predictive models..."):
            data = api_get(f"/forecast?days={days}")

        if data:
            summary = data.get("summary", {})

            st.markdown(f'''
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 32px;">
                <div class="premium-card">
                    <div class="metric-title">Hist. Run Rate</div>
                    <div class="metric-value">{fmt_currency(summary.get("historical_avg_daily_sales", 0))}</div>
                </div>
                <div class="premium-card" style="border-color:#00FF66;">
                    <div class="metric-title">Proj. Run Rate</div>
                    <div class="metric-value" style="color:#00D859;">{fmt_currency(summary.get("forecast_avg_daily_sales", 0))}</div>
                </div>
                <div class="premium-card">
                    <div class="metric-title">Growth Delta</div>
                    <div class="metric-value">{summary.get('growth_percent', 0):+.1f}%</div>
                </div>
                <div class="premium-card">
                    <div class="metric-title">Target Pipeline</div>
                    <div class="metric-value">{fmt_currency(summary.get("total_forecast_revenue", 0))}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            historical = pd.DataFrame(data.get("historical", []))
            forecast   = pd.DataFrame(data.get("forecast", []))

            if not historical.empty and not forecast.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=historical["date"], y=historical["sales"], name="Actuals", line=dict(color="#64748B", width=2)))
                fig.add_trace(go.Scatter(x=forecast["date"], y=forecast["sales"], name="Projection", line=dict(color="#00FF66", width=3), fill="tozeroy", fillcolor="rgba(0, 255, 102, 0.15)"))
                fig.update_layout(**CHART_THEME, hovermode="x unified")
                st.plotly_chart(style_fig(fig), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Anomalies
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Anomalies":
    st.markdown('<div class="startup-title">Security & Fraud</div>', unsafe_allow_html=True)
    st.markdown('<div class="startup-subtitle">Isolation Forest ML detecting outlier transactions.</div>', unsafe_allow_html=True)

    if st.button("Initiate Deep Scan", type="primary"):
        with st.spinner("Scanning vectors..."):
            data = api_get("/anomalies")

        if data:
            st.markdown(f'''
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 32px;">
                <div class="premium-card">
                    <div class="metric-title">Vectors Scanned</div>
                    <div class="metric-value">{data.get('total_records', 0):,}</div>
                </div>
                <div class="premium-card" style="border-color: #FF0044;">
                    <div class="metric-title">Anomalies Detected</div>
                    <div class="metric-value" style="color:#FF0044;">{data.get('total_anomalies', 0):,}</div>
                </div>
                <div class="premium-card">
                    <div class="metric-title">Risk Rate</div>
                    <div class="metric-value">{data.get('anomaly_rate_percent', 0):.1f}%</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            anomalies = data.get("anomalies", [])
            if anomalies:
                st.dataframe(pd.DataFrame(anomalies), use_container_width=True)
            else:
                st.success("System secure. No anomalies detected.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — Reports
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Reports":
    st.markdown('<div class="startup-title">Intelligence Exports</div>', unsafe_allow_html=True)
    st.markdown('<div class="startup-subtitle">Generate investor-ready PDF briefs.</div>', unsafe_allow_html=True)

    if st.button("Generate Brief", type="primary"):
        with st.spinner("Synthesizing intelligence brief..."):
            result = api_post("/report/generate")
            if result:
                st.session_state["report_ready"] = result

    if "report_ready" in st.session_state:
        result = st.session_state["report_ready"]
        
        st.markdown(f'''
        <div class="premium-card" style="margin-top:24px;">
            <div style="font-size:13px; color:#64748B; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px; font-weight:700;">Executive Summary</div>
            <div style="font-size:16px; color:#0F172A; line-height:1.6;">{result.get("ai_summary", "")}</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        try:
            pdf_response = requests.get(f"{API_URL}/report/download", timeout=30)
            if pdf_response.status_code == 200:
                st.download_button("Download PDF Document", pdf_response.content, "intelligence_brief.pdf", "application/pdf", type="primary", use_container_width=True)
        except:
            st.error("Download service unavailable.")