import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from backend.llm import generate_sql
from backend.database import run_query, get_schema
from backend.rag import get_query_count, approve_query, reject_query
from backend.explainer import explain_result, error_recovery, detect_anomalies
from backend.report import create_report

st.set_page_config(
    page_title="QueryMind — Business Intelligence",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #0A0D16;
    font-family: 'DM Sans', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stToolbar"] { display: none; }

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.4); border-radius: 2px; }

/* ── SIDEBAR ─────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1117 0%, #0A0D16 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
.sidebar-brand {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 1.1rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 0.75rem;
}
.brand-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, #7C3AED, #2563EB);
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(124,58,237,0.35);
}
.brand-name { font-size: 0.95rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.3px; }
.brand-sub  { font-size: 0.6rem; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; }

.sec-label {
    font-size: 0.58rem; font-weight: 600; color: #334155;
    letter-spacing: 1.5px; text-transform: uppercase;
    padding: 0.6rem 1rem 0.2rem;
}

[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #64748B !important;
    border-radius: 7px !important;
    font-size: 0.76rem !important;
    padding: 0.32rem 0.65rem !important;
    font-family: 'DM Sans', sans-serif !important;
    text-align: left !important;
    justify-content: flex-start !important;
    transition: all 0.15s !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(124,58,237,0.08) !important;
    border-color: rgba(124,58,237,0.2) !important;
    color: #A78BFA !important;
}

.hist-badge {
    font-size: 0.58rem; font-weight: 600;
    padding: 0.08rem 0.35rem; border-radius: 3px;
    background: rgba(16,185,129,0.12); color: #10B981;
}
.report-ready-badge {
    margin: 0 0.75rem 0.4rem;
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 6px; padding: 0.3rem 0.65rem;
    font-size: 0.72rem; color: #10B981; font-weight: 500;
}

/* ── PAGE HEADER ─────────────── */
.page-header {
    padding: 1.25rem 0 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    margin-bottom: 1.1rem;
}
.breadcrumb { font-size: 0.65rem; color: #334155; letter-spacing: 0.4px; margin-bottom: 0.3rem; }
.breadcrumb b { color: #7C3AED; }
.page-h1   { font-size: 1.65rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.4px; line-height: 1.2; }
.page-desc { font-size: 0.82rem; color: #64748B; margin-top: 0.2rem; }

/* ── STAT CARDS ──────────────── */
.stat-card {
    background: linear-gradient(145deg, #0F1623, #131B2E);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 0.9rem 1rem;
    position: relative; overflow: hidden; transition: all 0.2s;
}
.stat-card:hover { border-color: rgba(124,58,237,0.25); transform: translateY(-1px); }
.stat-accent { position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 12px 12px 0 0; }
.stat-ico  { font-size: 1rem; margin-bottom: 0.4rem; display: block; }
.stat-val  { font-size: 1.4rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.4px; line-height: 1; }
.stat-lbl  { font-size: 0.65rem; color: #475569; text-transform: uppercase; letter-spacing: 0.7px; margin-top: 0.15rem; }

/* ── INPUT ───────────────────── */
.stTextInput > div > div > input {
    background: rgba(15,22,35,0.8) !important;
    border: 1px solid rgba(124,58,237,0.25) !important;
    border-radius: 10px !important;
    color: #F1F5F9 !important;
    font-size: 0.88rem !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0.6rem 1rem !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(124,58,237,0.6) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important;
}
.stTextInput > div { border: none !important; box-shadow: none !important; }

/* ── BUTTONS ─────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7C3AED, #2563EB) !important;
    border: none !important; border-radius: 10px !important;
    color: white !important; font-weight: 600 !important;
    font-size: 0.84rem !important; padding: 0.6rem 1.25rem !important;
    font-family: 'DM Sans', sans-serif !important;
    box-shadow: 0 4px 16px rgba(124,58,237,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 22px rgba(124,58,237,0.4) !important;
}

/* ── SQL BLOCK ───────────────── */
.sql-block {
    background: linear-gradient(135deg, #080D1A, #0D1424);
    border: 1px solid rgba(124,58,237,0.18);
    border-left: 3px solid #7C3AED;
    border-radius: 10px; padding: 0.85rem 1.1rem; margin: 0.6rem 0;
}
.sql-tag  { font-size: 0.6rem; font-weight: 700; color: #7C3AED; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 0.4rem; }
.sql-text { font-family: 'JetBrains Mono', monospace; font-size: 0.77rem; color: #CBD5E1; line-height: 1.65; white-space: pre-wrap; }

/* ── BADGES ──────────────────── */
.badge-ok  {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2);
    border-radius: 6px; padding: 0.28rem 0.7rem;
    font-size: 0.72rem; font-weight: 500; color: #10B981;
}
.badge-err {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2);
    border-radius: 6px; padding: 0.28rem 0.7rem;
    font-size: 0.72rem; font-weight: 500; color: #EF4444;
}

/* ── KPI STRIP ───────────────── */
.kpi-strip {
    display: flex; gap: 0.75rem; margin: 0.75rem 0;
}
.kpi-box {
    flex: 1; border-radius: 10px; padding: 0.85rem 1rem;
    border: 1px solid rgba(255,255,255,0.06); text-align: center;
}
.kpi-val  { font-size: 1.6rem; font-weight: 700; line-height: 1; letter-spacing: -0.5px; }
.kpi-lbl  { font-size: 0.6rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-top: 0.2rem; color: #64748B; }

/* ── CHART CARDS ─────────────── */
.chart-card {
    background: linear-gradient(145deg, #0F1623, #111827);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 1rem 1rem 0.5rem;
}
.chart-title { font-size: 0.82rem; font-weight: 600; color: #E2E8F0; }
.chart-sub   { font-size: 0.67rem; color: #475569; margin: 0.1rem 0 0.6rem; }

/* ── TABLE CARD ──────────────── */
.tbl-card  {
    background: linear-gradient(145deg, #0F1623, #111827);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 1rem;
}
.tbl-title { font-size: 0.82rem; font-weight: 600; color: #E2E8F0; margin-bottom: 0.65rem; }

/* ── INSIGHT / ANOMALY CARDS ─── */
.ins-card {
    background: linear-gradient(135deg, #0C1428, #0F1A30);
    border: 1px solid rgba(59,130,246,0.18);
    border-left: 3px solid #3B82F6;
    border-radius: 10px; padding: 1rem 1.1rem; height: 100%;
}
.ano-card {
    background: linear-gradient(135deg, #0E0A02, #160E04);
    border: 1px solid rgba(245,158,11,0.2);
    border-left: 3px solid #F59E0B;
    border-radius: 10px; padding: 1rem 1.1rem; height: 100%;
}
.card-tag { font-size: 0.6rem; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 0.6rem; }
.ins-tag  { color: #60A5FA; }
.ano-tag  { color: #FBBF24; }

/* Insight bullets */
.ins-bullet {
    display: flex; gap: 0.5rem; align-items: flex-start;
    margin-bottom: 0.5rem;
}
.ins-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: #3B82F6; flex-shrink: 0; margin-top: 0.35rem;
}
.ins-txt { font-size: 0.78rem; color: #94A3B8; line-height: 1.6; }

/* Anomaly signal */
.ano-signal {
    font-size: 1rem; font-weight: 700; margin-bottom: 0.5rem;
    letter-spacing: 0.5px;
}
.ano-body { font-size: 0.77rem; color: #94A3B8; line-height: 1.6; }
.signal-ok     { color: #10B981; }
.signal-warn   { color: #F59E0B; }
.signal-danger { color: #EF4444; }

/* ── ERROR CARD ──────────────── */
.err-card {
    background: linear-gradient(135deg, #140808, #1A0C0C);
    border: 1px solid rgba(239,68,68,0.18);
    border-left: 3px solid #EF4444;
    border-radius: 10px; padding: 1rem 1.1rem;
    font-size: 0.79rem; color: #FCA5A5; line-height: 1.65;
}

/* ── FEEDBACK BAR ────────────── */
.fb-bar {
    background: linear-gradient(135deg, #0F1623, #111827);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 0.7rem 1.1rem; margin-top: 0.75rem;
}
.fb-txt   { font-size: 0.78rem; color: #64748B; }
.fb-txt b { color: #CBD5E1; }

/* ── RIGHT PANEL ─────────────── */
.rp-card {
    background: linear-gradient(145deg, #0F1623, #111827);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 0.9rem 1rem; margin-bottom: 0.65rem;
}
.rp-title {
    font-size: 0.78rem; font-weight: 600; color: #CBD5E1;
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.6rem;
}
.rp-num {
    font-size: 1.8rem; font-weight: 700;
    background: linear-gradient(135deg, #7C3AED, #2563EB);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1; display: inline;
}
.rp-lbl  { font-size: 0.72rem; color: #475569; margin-left: 0.3rem; }
.rp-hint { font-size: 0.62rem; color: #334155; margin-top: 0.25rem; }

/* ── MISC ────────────────────── */
[data-testid="stDataFrameResizable"] { border: none !important; border-radius: 8px !important; }

.stDownloadButton > button {
    background: rgba(124,58,237,0.08) !important;
    border: 1px solid rgba(124,58,237,0.25) !important;
    color: #A78BFA !important; border-radius: 8px !important;
    font-size: 0.76rem !important; font-weight: 500 !important;
    width: 100% !important; margin-top: 0.4rem !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stDownloadButton > button:hover { background: rgba(124,58,237,0.15) !important; }

.stSuccess { background: rgba(16,185,129,0.07) !important; border: 1px solid rgba(16,185,129,0.2) !important; border-radius: 8px !important; }
.stError   { background: rgba(239,68,68,0.07) !important;  border: 1px solid rgba(239,68,68,0.2) !important;  border-radius: 8px !important; }
.stWarning { background: rgba(245,158,11,0.07) !important; border: 1px solid rgba(245,158,11,0.2) !important; border-radius: 8px !important; }
.stInfo    { background: rgba(37,99,235,0.07) !important;  border: 1px solid rgba(37,99,235,0.2) !important;  border-radius: 8px !important; color: #60A5FA !important; }

hr { border-color: rgba(255,255,255,0.04) !important; margin: 0.75rem 0 !important; }
.stSpinner > div { border-top-color: #7C3AED !important; }
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.02) !important; border-radius: 7px !important;
    font-size: 0.73rem !important; color: #64748B !important;
    font-family: 'DM Sans', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE ─────────────────────────────────────────
for k, v in {
    "question": "", "chat_history": [], "last_sql": "",
    "last_question": "", "feedback_given": False,
    "report_data": [], "current_insight": "", "current_anomaly": ""
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── HELPERS ───────────────────────────────────────────────
def strip_markdown(text: str) -> str:
    """Remove all markdown from LLM output."""
    if not text:
        return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*',     r'\1', text)
    text = re.sub(r'__(.*?)__',     r'\1', text)
    text = re.sub(r'#+\s*',         '',    text)
    text = re.sub(r'`(.*?)`',       r'\1', text)
    return text.strip()


def parse_bullets(text: str) -> list[str]:
    """Convert LLM insight text into max 3 clean bullets."""
    text = strip_markdown(text)
    parts = re.split(
        r'(?:Insight:|Recommendation:|Note:|Finding:|Result:|\n\n|\n-\s|\n•\s)',
        text
    )
    bullets = []
    for p in parts:
        p = p.strip().strip("•-").strip()
        if len(p) > 25:
            bullets.append(p[:180] + "..." if len(p) > 180 else p)
        if len(bullets) == 3:
            break
    if not bullets and text:
        bullets = [text[:200]]
    return bullets


def anomaly_signal(text: str) -> tuple[str, str]:
    """Return (label, css_class) for anomaly status."""
    t = text.lower()
    if any(w in t for w in ["no anomal", "looks healthy", "normal", "consistent", "no significant"]):
        return "✅ ALL CLEAR", "signal-ok"
    elif any(w in t for w in ["significant", "unusual", "investigate", "worth noting", "monitor"]):
        return "⚠️ REVIEW NEEDED", "signal-warn"
    elif any(w in t for w in ["critical", "fraud", "error", "alert", "danger"]):
        return "🚨 FLAG", "signal-danger"
    return "⚠️ MONITOR", "signal-warn"


def extract_kpi(df: pd.DataFrame) -> tuple[str, str, str]:
    """Return (value, label, color) for KPI strip."""
    numeric = df.select_dtypes(include="number").columns.tolist()
    if not numeric:
        return f"{len(df):,}", "TOTAL RECORDS", "#7C3AED"

    col = numeric[0]
    col_lower = col.lower()
    total = df[col].sum()
    mx    = df[col].max()

    if any(k in col_lower for k in ["amount","revenue","total","sales","value","price"]):
        if total >= 1_000_000:
            return f"₹{total/1_000_000:.1f}M", f"TOTAL {col.upper().replace('_',' ')}", "#F59E0B"
        elif total >= 1_000:
            return f"₹{total/1_000:.0f}K", f"TOTAL {col.upper().replace('_',' ')}", "#F59E0B"
        else:
            return f"₹{total:,.0f}", f"TOTAL {col.upper().replace('_',' ')}", "#F59E0B"
    else:
        if mx >= 1_000_000:
            return f"{mx/1_000_000:.1f}M", f"PEAK {col.upper().replace('_',' ')}", "#3B82F6"
        elif mx >= 1_000:
            return f"{mx/1_000:.0f}K", f"PEAK {col.upper().replace('_',' ')}", "#3B82F6"
        else:
            return f"{mx:,.0f}", f"PEAK {col.upper().replace('_',' ')}", "#3B82F6"


# ── CHART FUNCTION ────────────────────────────────────────
GRAD_COLORS = ["#F59E0B","#3B82F6","#10B981","#8B5CF6",
               "#EF4444","#EC4899","#06B6D4","#84CC16",
               "#F97316","#A78BFA"]

def smart_charts(df: pd.DataFrame, question: str):
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    text_cols    = df.select_dtypes(exclude="number").columns.tolist()
    n_rows = len(df)

    if numeric_cols and text_cols:
        x_col, y_col = text_cols[0], numeric_cols[0]
        df_plot = df.head(12)
        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"""<div class='chart-card'>
                <div class='chart-title'>📊 {y_col.replace('_',' ').title()} by {x_col.replace('_',' ').title()}</div>
                <div class='chart-sub'>Bar chart view</div>""", unsafe_allow_html=True)
            fig = go.Figure(go.Bar(
                x=df_plot[x_col].astype(str), y=df_plot[y_col],
                marker=dict(color=list(range(len(df_plot))),
                           colorscale=[[0,"#1E3A5F"],[0.45,"#3B82F6"],[1,"#F59E0B"]],
                           line=dict(width=0)),
                text=[f"{v:,.0f}" if isinstance(v,(int,float)) and v>999
                      else str(round(v,1)) if isinstance(v,float) else str(v)
                      for v in df_plot[y_col]],
                textposition="outside", textfont=dict(size=8.5, color="#94A3B8")
            ))
            fig.update_layout(height=260, margin=dict(l=10,r=10,t=15,b=50),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8", size=9),
                xaxis=dict(showgrid=False, tickangle=-35 if n_rows>6 else 0, tickfont=dict(size=8)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=8)),
                showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("""<div class='chart-card'>
                <div class='chart-title'>🍩 Distribution</div>
                <div class='chart-sub'>Proportional breakdown</div>""", unsafe_allow_html=True)
            fig2 = go.Figure(go.Pie(
                labels=df_plot[x_col].astype(str), values=df_plot[y_col],
                hole=0.52, marker=dict(colors=GRAD_COLORS[:len(df_plot)],
                                       line=dict(color="#0A0D16", width=2)),
                textfont=dict(size=8.5), textinfo="percent", insidetextorientation="radial"
            ))
            fig2.update_layout(height=260, margin=dict(l=0,r=80,t=15,b=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8", size=8.5),
                legend=dict(font=dict(size=8, color="#94A3B8"),
                           bgcolor="rgba(0,0,0,0)", x=1, y=0.5), showlegend=True)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)
        return True

    elif numeric_cols and not text_cols:
        df_plot = df.head(15)
        x_axis  = list(range(1, len(df_plot)+1))
        c1, c2  = st.columns(2)
        with c1:
            st.markdown(f"""<div class='chart-card'>
                <div class='chart-title'>📈 {numeric_cols[0].replace('_',' ').title()} Trend</div>
                <div class='chart-sub'>Row-by-row progression</div>""", unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_axis, y=df_plot[numeric_cols[0]],
                mode="lines+markers", line=dict(color="#F59E0B", width=2.5),
                marker=dict(color="#FCD34D", size=6),
                fill="tozeroy", fillcolor="rgba(245,158,11,0.07)"))
            fig.update_layout(height=240, margin=dict(l=10,r=10,t=15,b=30),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8", size=9),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
                showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)

        if len(numeric_cols) >= 2:
            with c2:
                st.markdown(f"""<div class='chart-card'>
                    <div class='chart-title'>📊 {numeric_cols[1].replace('_',' ').title()} Trend</div>
                    <div class='chart-sub'>Row-by-row progression</div>""", unsafe_allow_html=True)
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=x_axis, y=df_plot[numeric_cols[1]],
                    mode="lines+markers", line=dict(color="#3B82F6", width=2.5),
                    marker=dict(color="#60A5FA", size=6),
                    fill="tozeroy", fillcolor="rgba(37,99,235,0.07)"))
                fig2.update_layout(height=240, margin=dict(l=10,r=10,t=15,b=30),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94A3B8", size=9),
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
                    showlegend=False)
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
                st.markdown("</div>", unsafe_allow_html=True)
        return True

    elif text_cols and not numeric_cols:
        val_counts = df[text_cols[0]].value_counts().head(12)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class='chart-card'>
                <div class='chart-title'>📊 {text_cols[0].replace('_',' ').title()} Frequency</div>
                <div class='chart-sub'>Count of unique values</div>""", unsafe_allow_html=True)
            fig = go.Figure(go.Bar(
                x=val_counts.index.astype(str), y=val_counts.values,
                marker=dict(color=list(range(len(val_counts))),
                           colorscale=[[0,"#1E3A5F"],[0.5,"#3B82F6"],[1,"#F59E0B"]],
                           line=dict(width=0)),
                text=val_counts.values, textposition="outside",
                textfont=dict(size=9, color="#94A3B8")
            ))
            fig.update_layout(height=250, margin=dict(l=10,r=10,t=15,b=50),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8", size=9),
                xaxis=dict(showgrid=False, tickangle=-30 if len(val_counts)>5 else 0, tickfont=dict(size=8)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
                showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            vc2 = df[text_cols[1]].value_counts().head(10) if len(text_cols) >= 2 else val_counts
            lbl = text_cols[1].replace('_',' ').title() if len(text_cols) >= 2 else text_cols[0].replace('_',' ').title()
            st.markdown(f"""<div class='chart-card'>
                <div class='chart-title'>🍩 {lbl} Share</div>
                <div class='chart-sub'>Proportional breakdown</div>""", unsafe_allow_html=True)
            fig2 = go.Figure(go.Pie(
                labels=vc2.index.astype(str), values=vc2.values, hole=0.52,
                marker=dict(colors=GRAD_COLORS[:len(vc2)], line=dict(color="#0A0D16", width=2)),
                textfont=dict(size=8.5), textinfo="percent"
            ))
            fig2.update_layout(height=250, margin=dict(l=0,r=80,t=15,b=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8", size=8.5),
                legend=dict(font=dict(size=8, color="#94A3B8"), bgcolor="rgba(0,0,0,0)", x=1, y=0.5),
                showlegend=True)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)
        return True

    return False


# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class='sidebar-brand'>
            <div class='brand-icon'>🧠</div>
            <div>
                <div class='brand-name'>QueryMind</div>
                <div class='brand-sub'>Business Intelligence</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sec-label'>Examples</div>", unsafe_allow_html=True)
    examples = [
        "What is the total revenue?",
        "Show me top 5 customers",
        "Which product is selling most?",
        "Show me all pending orders",
        "Revenue by category",
        "Show me premium customers",
        "Show me top state",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
            st.session_state.question = ex
            st.session_state.feedback_given = False
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='sec-label'>Recent Queries</div>", unsafe_allow_html=True)

    if st.session_state.chat_history:
        for chat in reversed(st.session_state.chat_history[-4:]):
            q = chat['question'][:30] + "..." if len(chat['question']) > 30 else chat['question']
            with st.expander(q):
                st.code(chat["sql"], language="sql")
                st.markdown(f"<span class='hist-badge'>{chat['rows']} rows</span>", unsafe_allow_html=True)
        if st.button("🗑️ Clear History", use_container_width=True, key="clr_hist"):
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.markdown("<div style='padding:0.2rem 1rem;font-size:0.7rem;color:#334155'>No queries yet</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='sec-label'>Report Builder</div>", unsafe_allow_html=True)

    if st.session_state.report_data:
        st.markdown(f"<div class='report-ready-badge'>✓ {len(st.session_state.report_data)} queries ready</div>", unsafe_allow_html=True)
        if st.button("📄 Generate PDF", use_container_width=True, type="primary", key="sb_pdf"):
            with st.spinner("Building report..."):
                try:
                    pdf = create_report(st.session_state.report_data)
                    st.download_button("⬇ Download PDF", pdf,
                        f"querymind_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                        "application/pdf", use_container_width=True, key="sb_dl")
                except Exception as e:
                    st.error(str(e))
        if st.button("Clear Report", use_container_width=True, key="clr_rpt"):
            st.session_state.report_data = []
            st.rerun()
    else:
        st.markdown("<div style='padding:0.2rem 1rem;font-size:0.7rem;color:#334155'>Run queries to build report</div>", unsafe_allow_html=True)


# ── MAIN + RIGHT ──────────────────────────────────────────
main_col, right_col = st.columns([3.2, 0.9])

with main_col:
    st.markdown("""
        <div class='page-header'>
            <div class='breadcrumb'>QueryMind &nbsp;▸&nbsp; <b>Business Intelligence</b></div>
            <div class='page-h1'>Welcome to QueryMind</div>
            <div class='page-desc'>Ask anything about your business — get instant SQL-powered insights</div>
        </div>
    """, unsafe_allow_html=True)

    # ── Stat cards ────────────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    cards = [
        (c1, "#7C3AED,#5B21B6", "👥", "5K+",  "Customers"),
        (c2, "#2563EB,#1D4ED8", "📦", "1K+",  "Products"),
        (c3, "#059669,#047857", "🛒", "30K+", "Orders"),
        (c4, "#D97706,#B45309", "🏙️", "500+", "Cities"),
        (c5, "#0891B2,#0E7490", "⭐", "6",    "Categories"),
    ]
    for col, grad, ico, val, lbl in cards:
        with col:
            st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-accent' style='background:linear-gradient(90deg,{grad})'></div>
                    <span class='stat-ico'>{ico}</span>
                    <div class='stat-val'>{val}</div>
                    <div class='stat-lbl'>{lbl}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.chat_history:
        last = st.session_state.chat_history[-1]
        st.info(f"💬 Following up on: *\"{last['question']}\"*")

    # ── Query input ───────────────────────────────────────
    inp_c, btn_c = st.columns([5, 1])
    with inp_c:
        question = st.text_input("", placeholder="Which city generates the most revenue?",
                                  value=st.session_state.get("question",""),
                                  label_visibility="collapsed", key="qinput")
    with btn_c:
        run = st.button("⚡ Generate & Run", type="primary", use_container_width=True)

    # ── RUN ──────────────────────────────────────────────
    if run and question:
        ctx = ""
        if st.session_state.chat_history:
            ctx = "Previous:\n" + "\n".join(
                f"Q:{c['question']}\nSQL:{c['sql']}"
                for c in st.session_state.chat_history[-3:]
            ) + "\n\n"

        with st.spinner("🤖 Generating SQL..."):
            sql, is_safe, reason = generate_sql(question, context=ctx)

        st.session_state.last_sql      = sql
        st.session_state.last_question = question
        st.session_state.feedback_given = False

        if sql:
            st.markdown(
                f"<div class='{'badge-ok' if is_safe else 'badge-err'}'>"
                f"{'✓ Query executed successfully' if is_safe else f'✗ {reason}'}</div>",
                unsafe_allow_html=True
            )
            st.markdown(f"""
                <div class='sql-block'>
                    <div class='sql-tag'>Generated SQL</div>
                    <div class='sql-text'>{sql}</div>
                </div>
            """, unsafe_allow_html=True)

        if not is_safe:
            with st.spinner("Analyzing error..."):
                recovery = error_recovery(question, reason, get_schema())
            st.markdown(f"<div class='err-card'>{strip_markdown(recovery)}</div>", unsafe_allow_html=True)

        else:
            try:
                columns, rows = run_query(sql)
                if rows:
                    df = pd.DataFrame(rows, columns=list(columns))
                    for col in df.columns:
                        try: df[col] = pd.to_numeric(df[col])
                        except: pass

                    st.markdown("<br>", unsafe_allow_html=True)

                    # ── KPI STRIP ─────────────────────────────────
                    kpi_val, kpi_lbl, kpi_col = extract_kpi(df)
                    row_count = f"{len(df):,}"
                    st.markdown(f"""
                        <div class='kpi-strip'>
                            <div class='kpi-box' style='background:rgba(245,158,11,0.06);border-color:rgba(245,158,11,0.18)'>
                                <div class='kpi-val' style='color:{kpi_col}'>{kpi_val}</div>
                                <div class='kpi-lbl'>{kpi_lbl}</div>
                            </div>
                            <div class='kpi-box' style='background:rgba(59,130,246,0.06);border-color:rgba(59,130,246,0.18)'>
                                <div class='kpi-val' style='color:#3B82F6'>{row_count}</div>
                                <div class='kpi-lbl'>Rows Returned</div>
                            </div>
                            <div class='kpi-box' style='background:rgba(16,185,129,0.06);border-color:rgba(16,185,129,0.18)'>
                                <div class='kpi-val' style='color:#10B981'>LIVE</div>
                                <div class='kpi-lbl'>Data Source</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # ── Charts ────────────────────────────────────
                    smart_charts(df, question)
                    st.markdown("<br>", unsafe_allow_html=True)

                    # ── Table + Anomaly ───────────────────────────
                    tbl_c, ano_c = st.columns([3, 2])
                    with tbl_c:
                        st.markdown(f"<div class='tbl-card'><div class='tbl-title'>📋 Results — {len(df):,} rows</div>", unsafe_allow_html=True)
                        st.dataframe(df.head(10), use_container_width=True, height=270, hide_index=True)
                        csv = df.to_csv(index=False).encode()
                        st.download_button("📥 Export CSV", csv, "results.csv", "text/csv", use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    with ano_c:
                        with st.spinner("Detecting anomalies..."):
                            anomaly = detect_anomalies(question, df.head(10).to_string())
                            st.session_state.current_anomaly = anomaly

                        sig_label, sig_class = anomaly_signal(anomaly)
                        ano_clean = strip_markdown(anomaly)
                        sentences = re.split(r'(?<=[.!?])\s+', ano_clean)
                        ano_short = " ".join(sentences[:2]) if sentences else ano_clean
                        if len(ano_short) > 260:
                            ano_short = ano_short[:257] + "..."

                        st.markdown(f"""
                            <div class='ano-card' style='min-height:320px'>
                                <div class='card-tag ano-tag'>🔍 Risk / Anomaly Assessment</div>
                                <div class='ano-signal {sig_class}'>{sig_label}</div>
                                <div class='ano-body'>{ano_short}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # ── AI Insight — clean bullets ─────────────────
                    with st.spinner("Generating insight..."):
                        insight = explain_result(question, sql, df.head(10).to_string())
                        st.session_state.current_insight = insight

                    bullets = parse_bullets(insight)
                    bullets_html = "".join([
                        f"<div class='ins-bullet'><div class='ins-dot'></div><div class='ins-txt'>{b}</div></div>"
                        for b in bullets
                    ])
                    st.markdown(f"""
                        <div class='ins-card'>
                            <div class='card-tag ins-tag'>💡 AI Business Insight</div>
                            {bullets_html}
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.session_state.chat_history.append({
                        "question": question, "sql": sql, "rows": len(rows)
                    })
                    st.session_state.report_data.append({
                        "question": question, "sql": sql,
                        "df": df, "insight": insight, "anomaly": anomaly
                    })
                    st.session_state.question = ""

                else:
                    st.info("No results found for this query.")

            except Exception as e:
                with st.spinner("Analyzing error..."):
                    recovery = error_recovery(question, str(e), get_schema())
                st.markdown(f"<div class='err-card'>{strip_markdown(recovery)}</div>", unsafe_allow_html=True)

    # ── Feedback ──────────────────────────────────────────
    if st.session_state.last_sql and not st.session_state.feedback_given:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
            <div class='fb-bar'>
                <div class='fb-txt'><b>Was this result correct?</b> &nbsp;·&nbsp; Your feedback trains the AI memory</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        fa, fb, fc = st.columns([1,1,3])
        with fa:
            if st.button("👍 Correct", key="appr"):
                approve_query(st.session_state.last_question, st.session_state.last_sql)
                st.session_state.feedback_given = True
                st.success("✓ Saved to memory!")
                st.rerun()
        with fb:
            if st.button("👎 Wrong", key="rejt"):
                reject_query(st.session_state.last_question)
                st.session_state.feedback_given = True
                st.warning("Removed from memory")
                st.rerun()
        with fc:
            st.markdown("<div style='font-size:0.7rem;color:#334155;padding-top:0.55rem'>Help QueryMind learn from every query</div>", unsafe_allow_html=True)


# ── RIGHT PANEL ───────────────────────────────────────────
with right_col:
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    trusted = get_query_count()
    st.markdown(f"""
        <div class='rp-card'>
            <div class='rp-title'>Trusted Memory</div>
            <div>
                <span class='rp-num'>{trusted}</span>
                <span class='rp-lbl'>Trusted<br>Queries</span>
            </div>
            <div class='rp-hint'>Only 👍 approved queries saved</div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.report_data:
        st.markdown(f"""
            <div class='rp-card'>
                <div class='rp-title'>Report Builder</div>
                <div style='font-size:0.72rem;color:#10B981;font-weight:500;margin-bottom:0.5rem'>
                    ✓ {len(st.session_state.report_data)} queries ready
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📄 Generate PDF Report", use_container_width=True, type="primary", key="rp_pdf"):
            with st.spinner("Building..."):
                try:
                    pdf = create_report(st.session_state.report_data)
                    st.download_button("⬇ Download PDF", pdf,
                        f"querymind_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                        "application/pdf", use_container_width=True, key="rp_dl")
                except Exception as e:
                    st.error(str(e))
    else:
        st.markdown("""
            <div class='rp-card'>
                <div class='rp-title'>Report Builder</div>
                <div style='font-size:0.7rem;color:#334155'>Run & approve queries to build a PDF report</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style='font-size:0.6rem;color:#1E293B;text-align:center;margin-top:0.75rem;line-height:1.7'>
            QueryMind v1.0<br>
            Groq · LangChain<br>ChromaDB · MySQL
        </div>
    """, unsafe_allow_html=True)