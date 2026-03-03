# 🚀 QueryMind AI

### Intelligent Text-to-SQL Business Intelligence Platform

Turn plain English into secure, optimized SQL queries with AI-powered
insights, anomaly detection, and executive reporting.

------------------------------------------------------------------------

## 📌 Overview

QueryMind AI converts **natural language into secure SQL queries** and
delivers:

-   📊 Real-time database analytics\
-   🧠 AI-generated business insights\
-   ⚠️ Anomaly detection\
-   📄 Executive-ready PDF reports\
-   🔁 Self-improving RAG memory

Built with production-grade safety guardrails and modular AI
architecture.

------------------------------------------------------------------------

# 🏗 System Architecture

``` mermaid
flowchart TD
    A[Streamlit UI] --> B[Prompt Builder]
    B --> C[Llama 3.3 70B - Groq]
    C --> D[SQL Validator - AST + LIMIT]
    D --> E[(MySQL Database)]
    E --> F[BI Processing Layer]
    F --> G[Charts + Insights + Risk]
    G --> H[PDF Report Engine]
```

------------------------------------------------------------------------

# 🔎 Query Execution Flow

``` mermaid
flowchart TD
    U[User Question] --> P[Prompt Construction]
    P --> L[LLM SQL Generation]
    L --> V[AST Validation]
    V --> S[Safe Execution]
    S --> R[Results]
    R --> B[BI Processing]
    B --> O[Insights & Visualization]
    O --> M{Approve Query?}
    M -->|Yes| T[Store in RAG Memory]
    M -->|No| X[Discard]
```

------------------------------------------------------------------------

# ✨ Core Features

## 🔎 Natural Language → SQL

-   Schema-aware SQL generation
-   Business-rule injection
-   Optimized query construction

## 🛡 SQL Safety Layer

-   AST-based validation (`sqlglot`)
-   SELECT-only enforcement
-   Automatic LIMIT injection
-   Row threshold guardrails
-   Read-only DB user

## 🔁 Human-in-the-Loop RAG

-   Approved queries stored as trusted examples
-   Rejected queries removed
-   Semantic similarity search
-   Persistent ChromaDB storage

## 📊 Business Intelligence Engine

-   Auto chart selection
-   KPI extraction
-   Executive summaries
-   Risk & anomaly detection

## 📄 Executive PDF Builder

-   Query summary
-   Metrics overview
-   Success rate
-   Business insights

------------------------------------------------------------------------

## 🧰 Technology Stack

### 🤖 AI Layer

| Component | Technology |
|------------|------------|
| LLM | Llama 3.3 70B (Groq) |
| Embeddings | all-MiniLM-L6-v2 |
| Orchestration | LangChain |
| SQL Parsing | sqlglot |

---

### 🗄 Data Layer

| Component | Technology |
|------------|------------|
| Database | MySQL |
| ORM | SQLAlchemy |
| Vector Store | ChromaDB |

---

### 🖥 Backend

| Component | Technology |
|------------|------------|
| Web UI | Streamlit |
| Visualization | Plotly |
| Config Management | python-dotenv |
| Data Processing | Pandas |
------------------------------------------------------------------------

# 🔐 Security & Hardening

-   AST-level SQL parsing\
-   DDL/DML blocking\
-   Auto LIMIT injection\
-   Query timeout protection\
-   Read-only DB credentials\
-   Memory approval gating

Designed to prevent SQL injection, runaway queries, and hallucinated
SQL.

------------------------------------------------------------------------

# 📂 Project Structure

``` bash
QueryMind/
│
├── backend/
│   ├── database.py
│   ├── validator.py
│   ├── rag.py
│   ├── explainer.py
│   └── report.py
│
├── prompts/
│   └── sql_prompt.py
│
├── config/
│   └── settings.py
│
├── create_db.py
├── app.py
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

# ⚙️ Setup

## 1️⃣ Install Dependencies

``` bash
pip install -r requirements.txt
```

## 2️⃣ Create .env

    DB_USER=readonly_user
    DB_PASSWORD=your_password
    DB_HOST=localhost
    DB_PORT=3306
    DB_NAME=ecommerce_db
    GROQ_API_KEY=your_groq_api_key

## 3️⃣ Run Application

``` bash
streamlit run app.py
```

------------------------------------------------------------------------

# 📈 Engineering Highlights

-   Multi-layer prompt injection\
-   Human-in-the-loop query learning\
-   Production-safe SQL execution\
-   Intelligent visualization logic\
-   Modular backend architecture

------------------------------------------------------------------------

# 🔮 Future Enhancements

-   Query cost estimation via EXPLAIN\
-   Role-based access control\
-   Redis caching\
-   Docker deployment\
-   REST API version

------------------------------------------------------------------------

# 👨‍💻 Author

Applied AI Engineering project demonstrating secure Text-to-SQL system
design with real-world production guardrails.
