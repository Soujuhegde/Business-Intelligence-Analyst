import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI Business Intelligence Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

/* Hide default streamlit header */
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    border-right: 1px solid #2d2d4e;
}
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }

/* Main background */
.stApp { background: #0a0a14; color: #e0e0f0; }

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #2d2d4e;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}
.kpi-card:hover {
    transform: translateY(-3px);
    border-color: #7c6af7;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #7c6af7;
    font-family: 'JetBrains Mono', monospace;
}
.kpi-label {
    font-size: 0.85rem;
    color: #8888aa;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 6px;
}

/* Chat bubbles */
.chat-user {
    background: linear-gradient(135deg, #7c6af7, #5b4fcf);
    color: white;
    padding: 14px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.95rem;
}
.chat-ai {
    background: linear-gradient(135deg, #1e1e36, #2a2a4a);
    border: 1px solid #3d3d6e;
    color: #d0d0ee;
    padding: 14px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 0;
    max-width: 85%;
    font-size: 0.95rem;
    line-height: 1.6;
}

/* Section headers */
.section-header {
    font-size: 1.5rem;
    font-weight: 700;
    color: #e0e0f0;
    margin-bottom: 4px;
}
.section-sub {
    font-size: 0.9rem;
    color: #6666aa;
    margin-bottom: 24px;
}

/* Upload area */
.upload-box {
    border: 2px dashed #3d3d6e;
    border-radius: 16px;
    padding: 40px;
    text-align: center;
    background: #12121f;
}

/* Anomaly badge */
.anomaly-badge {
    display: inline-block;
    background: #ff4757;
    color: white;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Plotly chart background override */
.js-plotly-plot { border-radius: 12px; overflow: hidden; }

/* Metric delta color */
[data-testid="stMetricDelta"] { font-size: 0.8rem; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f0f1a; }
::-webkit-scrollbar-thumb { background: #3d3d6e; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Plotly dark template ───────────────────────────────────────────────────────
CHART_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk", color="#e0e0f0"),
    margin=dict(l=20, r=20, t=40, b=20),
)
PURPLE = "#7c6af7"
TEAL   = "#00d2c8"
CORAL  = "#ff6b6b"
AMBER  = "#ffd166"
COLORS = [PURPLE, TEAL, CORAL, AMBER, "#06d6a0", "#ef476f", "#118ab2"]


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
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend not running. Start it with: `uvicorn main:app --reload`")
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def api_post(endpoint, data=None, files=None):
    try:
        if files:
            r = requests.post(f"{API_URL}{endpoint}", files=files, timeout=60)
        else:
            r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend not running. Start it with: `uvicorn main:app --reload`")
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 AI BI Analyst")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📁 Upload & Clean", "📊 Dashboard", "💬 AI Chat", "📈 Forecast", "🚨 Anomalies", "📄 Reports"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Backend Status**")
    try:
        ping = requests.get(f"{API_URL}/", timeout=3)
        if ping.status_code == 200:
            st.success("🟢 Connected")
        else:
            st.error("🔴 Error")
    except:
        st.error("🔴 Offline")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem;color:#555577;'>Powered by LangChain · Groq · FastAPI</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Upload & Clean
# ══════════════════════════════════════════════════════════════════════════════
if page == "📁 Upload & Clean":
    st.markdown('<div class="section-header">📁 Upload & Clean Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Upload your CSV — the AI cleaning agent will auto-fix issues and load it into the database.</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Drop your CSV here", type=["csv"], label_visibility="collapsed")

    if uploaded:
        with st.spinner("🤖 Running cleaning agent..."):
            result = api_post("/upload", files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")})

        if result:
            report = result.get("cleaning_report", {})
            db     = result.get("database", {})

            # Summary row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Rows Loaded", f"{db.get('rows', 0):,}")
            col2.metric("Columns", len(db.get("columns", [])))
            col3.metric("Issues Found", len(report.get("issues_found", [])))
            col4.metric("Quality Score", f"{report.get('data_quality_score', 0)}%")

            st.markdown("---")
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**🔍 Issues Found**")
                issues = report.get("issues_found", [])
                if issues:
                    for issue in issues:
                        st.warning(f"⚠️ {issue}")
                else:
                    st.success("✅ No issues found!")

            with c2:
                st.markdown("**✅ Fixes Applied**")
                fixes = report.get("fixes_applied", [])
                if fixes:
                    for fix in fixes:
                        st.info(f"🔧 {fix}")

            st.markdown("---")
            st.markdown("**📋 Columns Detected**")
            cols = db.get("columns", [])
            st.code(", ".join(cols), language=None)

            st.success(f"✅ Data loaded successfully into database — {db.get('rows', 0):,} rows ready for analysis!")

    else:
        st.markdown("""
        <div class="upload-box">
            <div style="font-size:3rem;margin-bottom:12px">📂</div>
            <div style="font-size:1.1rem;color:#8888aa;">Drag and drop your CSV file here</div>
            <div style="font-size:0.85rem;color:#555577;margin-top:8px;">Supports: sales data, customer data, retail data</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**💡 Recommended Dataset**")
        st.info("Download **Sample Superstore** from Kaggle: `kaggle.com/datasets/vivek468/superstore-dataset-final`")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Dashboard
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    st.markdown('<div class="section-header">📊 Business Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Real-time KPIs and performance charts from your data.</div>', unsafe_allow_html=True)

    with st.spinner("Loading dashboard..."):
        data = api_get("/dashboard")

    if data:
        kpis   = data.get("kpis", {})
        charts = data.get("charts", {})

        # ── KPI Row ────────────────────────────────────────────────────────
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.markdown(f'<div class="kpi-card"><div class="kpi-value">{fmt_currency(kpis.get("total_revenue",0))}</div><div class="kpi-label">Total Revenue</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card"><div class="kpi-value">{fmt_currency(kpis.get("total_profit",0))}</div><div class="kpi-label">Total Profit</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card"><div class="kpi-value">{kpis.get("profit_margin",0):.1f}%</div><div class="kpi-label">Profit Margin</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi-card"><div class="kpi-value">{kpis.get("total_orders",0):,}</div><div class="kpi-label">Total Orders</div></div>', unsafe_allow_html=True)
        k5.markdown(f'<div class="kpi-card"><div class="kpi-value">{kpis.get("unique_customers",0):,}</div><div class="kpi-label">Customers</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 1: Monthly trend + Region ─────────────────────────────────
        c1, c2 = st.columns([2, 1])

        with c1:
            monthly = charts.get("monthly_revenue", [])
            if monthly:
                df_m = pd.DataFrame(monthly)
                fig = px.area(
                    df_m, x="month", y="sales",
                    title="Monthly Revenue Trend",
                    color_discrete_sequence=[PURPLE],
                )
                fig.update_traces(fill="tozeroy", fillcolor="rgba(124,106,247,0.15)")
                fig.update_layout(**CHART_THEME)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            region = charts.get("sales_by_region", [])
            if region:
                df_r = pd.DataFrame(region)
                fig = px.pie(
                    df_r, values="sales", names="region",
                    title="Sales by Region",
                    color_discrete_sequence=COLORS,
                    hole=0.45,
                )
                fig.update_layout(**CHART_THEME)
                st.plotly_chart(fig, use_container_width=True)

        # ── Row 2: Top products + Category ────────────────────────────────
        c3, c4 = st.columns([2, 1])

        with c3:
            products = charts.get("top_products", [])
            if products:
                df_p = pd.DataFrame(products).sort_values("sales")
                fig = px.bar(
                    df_p, x="sales", y="product_name",
                    orientation="h",
                    title="Top 10 Products by Revenue",
                    color="sales",
                    color_continuous_scale=[[0, "#2d2d6e"], [1, PURPLE]],
                )
                fig.update_layout(**CHART_THEME, showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

        with c4:
            cat = charts.get("sales_by_category", [])
            if cat:
                df_c = pd.DataFrame(cat)
                fig = px.bar(
                    df_c, x="category", y="sales",
                    title="Sales by Category",
                    color="category",
                    color_discrete_sequence=COLORS,
                )
                fig.update_layout(**CHART_THEME, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # ── Segment breakdown ──────────────────────────────────────────────
        seg = charts.get("sales_by_segment", [])
        if seg:
            df_s = pd.DataFrame(seg)
            fig = px.bar(
                df_s, x="segment", y="sales",
                title="Revenue by Customer Segment",
                color="segment",
                color_discrete_sequence=COLORS,
                text="sales",
            )
            fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
            fig.update_layout(**CHART_THEME, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — AI Chat
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬 AI Chat":
    st.markdown('<div class="section-header">💬 Ask Your Data Anything</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Natural language → SQL → Business insight. Powered by Groq LLM.</div>', unsafe_allow_html=True)

    # Example questions
    st.markdown("**💡 Try these questions:**")
    examples = [
        "Why did revenue drop in Q3?",
        "Which region has the highest profit margin?",
        "Who are our top 5 customers by revenue?",
        "Which product category is most profitable?",
        "What is the average order value by segment?",
    ]
    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state["prefill"] = ex

    st.markdown("---")

    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">🧑‍💼 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    prefill = st.session_state.pop("prefill", "")
    question = st.chat_input("Ask a business question...")

    if question or prefill:
        q = question or prefill
        st.session_state.chat_history.append({"role": "user", "content": q})
        st.markdown(f'<div class="chat-user">🧑‍💼 {q}</div>', unsafe_allow_html=True)

        with st.spinner("🤖 Analyzing your data..."):
            result = api_post("/query", data={"question": q})

        if result:
            answer = result.get("answer", "No answer returned.")
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.markdown(f'<div class="chat-ai">🤖 {answer}</div>', unsafe_allow_html=True)

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Forecast
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Forecast":
    st.markdown('<div class="section-header">📈 Sales Forecasting</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">ML-powered revenue prediction using linear regression on historical sales.</div>', unsafe_allow_html=True)

    days = st.slider("Forecast horizon (days)", min_value=7, max_value=90, value=30, step=7)

    if st.button("🔮 Run Forecast", type="primary"):
        with st.spinner("Running forecasting model..."):
            data = api_get(f"/forecast?days={days}")

        if data:
            summary = data.get("summary", {})

            # Summary KPIs
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Avg Daily (Historical)", fmt_currency(summary.get("historical_avg_daily_sales", 0)))
            c2.metric("Avg Daily (Forecast)", fmt_currency(summary.get("forecast_avg_daily_sales", 0)))
            c3.metric(
                "Growth",
                f"{summary.get('growth_percent', 0):+.1f}%",
                delta=f"{summary.get('growth_percent', 0):+.1f}%"
            )
            c4.metric("Total Forecast Revenue", fmt_currency(summary.get("total_forecast_revenue", 0)))

            st.markdown("---")

            # Build chart
            historical = pd.DataFrame(data.get("historical", []))
            forecast   = pd.DataFrame(data.get("forecast", []))

            if not historical.empty and not forecast.empty:
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=historical["date"], y=historical["sales"],
                    name="Historical Sales",
                    line=dict(color=PURPLE, width=2),
                    mode="lines",
                ))

                fig.add_trace(go.Scatter(
                    x=forecast["date"], y=forecast["sales"],
                    name=f"{days}-Day Forecast",
                    line=dict(color=TEAL, width=2, dash="dash"),
                    mode="lines",
                    fill="tozeroy",
                    fillcolor="rgba(0,210,200,0.08)",
                ))

                fig.update_layout(
                    **CHART_THEME,
                    title=f"Sales Forecast — Next {days} Days",
                    xaxis_title="Date",
                    yaxis_title="Revenue ($)",
                    hovermode="x unified",
                )
                st.plotly_chart(fig, use_container_width=True)

                # Forecast table
                st.markdown("**📋 Forecast Data**")
                st.dataframe(
                    forecast.rename(columns={"date": "Date", "sales": "Predicted Sales ($)"}),
                    use_container_width=True,
                    height=300,
                )
    else:
        st.info("👆 Set your forecast horizon and click **Run Forecast**")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Anomalies
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🚨 Anomalies":
    st.markdown('<div class="section-header">🚨 Anomaly Detection</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">IsolationForest ML model flags unusual orders — potential fraud, errors, or outliers.</div>', unsafe_allow_html=True)

    if st.button("🔍 Detect Anomalies", type="primary"):
        with st.spinner("Running IsolationForest model..."):
            data = api_get("/anomalies")

        if data:
            summary = data.get("summary", {})

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Records", f"{data.get('total_records', 0):,}")
            c2.metric("Anomalies Found", f"{data.get('total_anomalies', 0):,}")
            c3.metric("Anomaly Rate", f"{data.get('anomaly_rate_percent', 0):.1f}%")

            st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Avg Sales (Anomalies):** `${summary.get('avg_anomaly_sales', 0):,.2f}`")
            with col2:
                st.markdown(f"**Avg Sales (Normal):** `${summary.get('avg_normal_sales', 0):,.2f}`")

            st.markdown("---")
            st.markdown("**🚨 Flagged Records**")

            anomalies = data.get("anomalies", [])
            if anomalies:
                df_a = pd.DataFrame(anomalies)
                st.dataframe(
                    df_a,
                    use_container_width=True,
                    height=400,
                )
                st.warning(f"⚠️ {len(anomalies)} anomalous orders detected. Review these records manually.")
            else:
                st.success("✅ No anomalies detected in your data!")
    else:
        st.info("👆 Click **Detect Anomalies** to run the ML model on your data")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — Reports
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Reports":
    st.markdown('<div class="section-header">📄 Automated Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">AI generates a full business report with KPIs and executive summary as a downloadable PDF.</div>', unsafe_allow_html=True)

    st.markdown("""
    **What's included in the report:**
    - ✅ AI-written executive summary (Groq LLM)
    - ✅ All key KPIs (revenue, profit, margin, orders)
    - ✅ Top region, category, and product
    - ✅ Professional PDF formatting
    """)

    st.markdown("---")

    if st.button("🤖 Generate AI Report", type="primary", use_container_width=True):
        with st.spinner("🤖 AI is writing your report..."):
            result = api_post("/report/generate")

        if result:
            st.success("✅ Report generated successfully!")

            # Show AI summary
            st.markdown("**📝 AI Executive Summary**")
            st.info(result.get("ai_summary", "No summary available."))

            # Show KPIs
            kpis = result.get("kpis", {})
            if kpis:
                st.markdown("**📊 KPIs in Report**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Revenue", fmt_currency(kpis.get("total_revenue", 0)))
                c2.metric("Profit", fmt_currency(kpis.get("total_profit", 0)))
                c3.metric("Margin", f"{kpis.get('profit_margin', 0):.1f}%")

            st.markdown("---")

            # Download button
            try:
                pdf_response = requests.get(f"{API_URL}/report/download", timeout=30)
                if pdf_response.status_code == 200:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_response.content,
                        file_name=f"business_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary",
                    )
            except Exception as e:
                st.error(f"Download error: {str(e)}")
    else:
        st.markdown("""
        <div style="background:#12121f;border:1px dashed #3d3d6e;border-radius:16px;padding:40px;text-align:center;">
            <div style="font-size:3rem;margin-bottom:12px">📊</div>
            <div style="font-size:1.1rem;color:#8888aa;">Click the button above to generate your AI-powered report</div>
            <div style="font-size:0.85rem;color:#555577;margin-top:8px;">Make sure data is uploaded first</div>
        </div>
        """, unsafe_allow_html=True)