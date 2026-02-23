import streamlit as st
import pandas as pd
import plotly.express as px
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

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6C63FF, #48CAE4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-title {
        color: #8b8fa8;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border: 1px solid #2e3250;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #6C63FF;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #8b8fa8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .insight-box {
        background: linear-gradient(135deg, #1a1f35, #1e2440);
        border-left: 3px solid #6C63FF;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
    }
    .anomaly-box {
        background: linear-gradient(135deg, #2a1f10, #2e2415);
        border-left: 3px solid #FFA500;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
    }
    .feedback-box {
        background: linear-gradient(135deg, #1e2130, #252840);
        border: 1px solid #2e3250;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-top: 1rem;
    }
    .error-box {
        background: linear-gradient(135deg, #2a1010, #2e1515);
        border-left: 3px solid #ff4444;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
    }
    [data-testid="stSidebar"] {
        background-color: #13151f;
        border-right: 1px solid #1e2130;
    }
    .stTextInput > div > div > input {
        background-color: #1e2130 !important;
        border: 1px solid #2e3250 !important;
        border-radius: 8px !important;
        color: white !important;
        font-size: 1rem !important;
        padding: 0.75rem !important;
    }
    hr { border-color: #1e2130 !important; }
</style>
""", unsafe_allow_html=True)

# Session state
if "question" not in st.session_state:
    st.session_state.question = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_sql" not in st.session_state:
    st.session_state.last_sql = ""
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = False
if "report_data" not in st.session_state:
    st.session_state.report_data = []

# Sidebar
with st.sidebar:
    st.markdown("""
        <div style='text-align:center; padding: 1rem 0;'>
            <span style='font-size:2rem'>🧠</span>
            <div style='color:#6C63FF; font-weight:700; font-size:1.2rem'>QueryMind</div>
            <div style='color:#8b8fa8; font-size:0.75rem'>AI Business Intelligence</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💡 Try Asking")
    examples = [
        "What is the total revenue?",
        "Show me top 5 customers by spending",
        "Which product is selling the most?",
        "Show me all pending orders",
        "What is the revenue by category?",
        "Show me premium customers",
        "Show me low stock products",
        "What is the average order value?",
        "What is the most popular payment method?",
        "Which city has the most customers?",
        "Show me top rated products",
        "Revenue by state",
    ]
    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state.question = example
            st.session_state.feedback_given = False

    st.markdown("---")
    trusted = get_query_count()
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{trusted}</div>
            <div class='metric-label'>🧠 Trusted Queries in Memory</div>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Only 👍 approved queries saved")

    st.markdown("---")
    st.markdown("### 🕓 Recent History")
    if st.session_state.chat_history:
        for chat in reversed(st.session_state.chat_history[-5:]):
            with st.expander(f"🔍 {chat['question'][:28]}..."):
                st.code(chat["sql"], language="sql")
                st.caption(f"✅ {chat['rows']} rows returned")
    else:
        st.caption("No queries yet!")

    st.markdown("---")

    # Report section in sidebar
    st.markdown("### 📄 Report Builder")
    if st.session_state.report_data:
        st.success(f"✅ {len(st.session_state.report_data)} queries ready")
        if st.button("📥 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("📄 Building your report..."):
                try:
                    pdf_bytes = create_report(st.session_state.report_data)
                    st.download_button(
                        label="⬇️ Download Report",
                        data=pdf_bytes,
                        file_name=f"querymind_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Report error: {e}")
        if st.button("🗑️ Clear Report", use_container_width=True):
            st.session_state.report_data = []
            st.rerun()
    else:
        st.caption("Run queries and approve them to add to report")

    if st.session_state.chat_history:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

# Main content
st.markdown("<p class='main-title'>🧠 QueryMind</p>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Ask anything about your business — get instant SQL-powered insights</p>", unsafe_allow_html=True)

# Quick stats
col1, col2, col3, col4 = st.columns(4)
stats = [
    ("👥", "50", "Customers"),
    ("📦", "20", "Products"),
    ("🛒", "150+", "Orders"),
    ("🏙️", "15+", "Cities"),
]
for col, (icon, val, label) in zip([col1, col2, col3, col4], stats):
    with col:
        st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:1.5rem'>{icon}</div>
                <div class='metric-value'>{val}</div>
                <div class='metric-label'>{label}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.chat_history:
    last = st.session_state.chat_history[-1]
    st.info(f"💬 Following up on: *\"{last['question']}\"* — Ask a follow-up or try something new!")

st.markdown("### 🔍 Ask Your Question")
question = st.text_input(
    "",
    placeholder="e.g., Which city generates the most revenue?",
    value=st.session_state.get("question", ""),
    label_visibility="collapsed"
)

run = st.button("⚡ Generate & Run", type="primary")

if run and question:
    conversation_context = ""
    if st.session_state.chat_history:
        conversation_context = "Previous questions in this session:\n"
        for chat in st.session_state.chat_history[-3:]:
            conversation_context += f"Q: {chat['question']}\nSQL: {chat['sql']}\n\n"

    with st.spinner("🤖 Generating SQL..."):
        sql, is_safe, reason = generate_sql(question, context=conversation_context)

    st.session_state.last_sql = sql
    st.session_state.last_question = question
    st.session_state.feedback_given = False

    st.markdown("---")
    st.markdown("### 🧠 Generated SQL")
    st.code(sql, language="sql")

    if not is_safe:
        st.error(reason)
    else:
        st.success("✅ Query is safe to execute")

        try:
            columns, rows = run_query(sql)

            if rows:
                df = pd.DataFrame(rows, columns=list(columns))

                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except:
                        pass

                numeric_cols = df.select_dtypes(include="number").columns.tolist()
                text_cols = df.select_dtypes(exclude="number").columns.tolist()

                st.markdown("---")

                if len(numeric_cols) >= 1 and len(text_cols) >= 1:
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.markdown("### 📋 Results")
                        st.dataframe(df, use_container_width=True, height=350)
                        st.caption(f"✅ {len(rows)} row(s) returned")
                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name="results.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    with col2:
                        st.markdown("### 📊 Visualization")
                        chart_type = st.selectbox(
                            "Chart type:",
                            ["Bar Chart", "Pie Chart", "Line Chart", "Horizontal Bar"]
                        )
                        x_col = text_cols[0]
                        y_col = numeric_cols[0]

                        if chart_type == "Bar Chart":
                            fig = px.bar(df, x=x_col, y=y_col,
                                        title=f"{y_col} by {x_col}",
                                        color=x_col, template="plotly_dark",
                                        color_discrete_sequence=px.colors.sequential.Purples_r)
                        elif chart_type == "Pie Chart":
                            fig = px.pie(df, names=x_col, values=y_col,
                                        title=f"{y_col} by {x_col}",
                                        template="plotly_dark",
                                        color_discrete_sequence=px.colors.sequential.Purples_r)
                        elif chart_type == "Line Chart":
                            fig = px.line(df, x=x_col, y=y_col,
                                         title=f"{y_col} over {x_col}",
                                         template="plotly_dark")
                        elif chart_type == "Horizontal Bar":
                            fig = px.bar(df, x=y_col, y=x_col,
                                        orientation="h",
                                        title=f"{y_col} by {x_col}",
                                        color=x_col, template="plotly_dark",
                                        color_discrete_sequence=px.colors.sequential.Blues_r)

                        fig.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)

                else:
                    st.markdown("### 📋 Results")
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"✅ {len(rows)} row(s) returned")
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name="results.csv",
                        mime="text/csv"
                    )

                # AI Explainability
                st.markdown("---")
                with st.spinner("🧠 Analyzing results..."):
                    df_summary = df.head(10).to_string()

                    col1, col2 = st.columns(2)

                    with col1:
                        insight = explain_result(question, sql, df_summary)
                        st.markdown("### 💡 AI Insight")
                        st.markdown(f"""
                            <div class='insight-box'>
                                {insight}
                            </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        anomaly = detect_anomalies(question, df_summary)
                        st.markdown("### 🔍 Anomaly Detection")
                        st.markdown(f"""
                            <div class='anomaly-box'>
                                {anomaly}
                            </div>
                        """, unsafe_allow_html=True)

                # Save to session
                st.session_state.chat_history.append({
                    "question": question,
                    "sql": sql,
                    "rows": len(rows)
                })

                # Save to report data
                st.session_state.report_data.append({
                    "question": question,
                    "sql": sql,
                    "df": df,
                    "insight": insight,
                    "anomaly": anomaly
                })

                st.session_state.question = ""

            else:
                st.info("No results found.")

        except Exception as e:
            # Natural Language Error Recovery
            st.markdown("---")
            with st.spinner("🔧 Analyzing error..."):
                schema = get_schema()
                recovery = error_recovery(question, str(e), schema)
            st.markdown(f"""
                <div class='error-box'>
                    {recovery}
                </div>
            """, unsafe_allow_html=True)

# Feedback
if st.session_state.last_sql and not st.session_state.feedback_given:
    st.markdown("---")
    st.markdown("""
        <div class='feedback-box'>
            <b>💬 Was this result correct?</b><br>
            <span style='color:#8b8fa8; font-size:0.85rem'>Your feedback trains the AI to get smarter over time</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 6])
    with col1:
        if st.button("👍 Correct", use_container_width=True):
            approve_query(st.session_state.last_question, st.session_state.last_sql)
            st.session_state.feedback_given = True
            st.success("✅ Saved to AI memory!")
            st.rerun()
    with col2:
        if st.button("👎 Wrong", use_container_width=True):
            reject_query(st.session_state.last_question)
            st.session_state.feedback_given = True
            st.warning("🗑️ Removed from memory!")
            st.rerun()

st.markdown("---")
st.markdown("""
    <div style='text-align:center; color:#8b8fa8; font-size:0.8rem; padding: 1rem'>
        🧠 QueryMind • Powered by LangChain • Groq Llama 3 • ChromaDB • Streamlit
    </div>
""", unsafe_allow_html=True)