import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from config.settings import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def explain_result(question: str, sql: str, df_summary: str) -> str:
    """
    Takes the question, SQL, and result summary
    Returns a plain English business explanation
    """
    prompt = f"""
You are a senior business analyst explaining data insights to a non-technical manager.

The user asked: "{question}"

The SQL query used was:
{sql}

The result summary is:
{df_summary}

Your job:
1. Explain what the result means in plain English (2-3 sentences)
2. Point out the most important insight from the data
3. Give ONE actionable business recommendation based on this data

Keep it concise, professional, and avoid technical jargon.
Format your response as:

📊 *Insight: [what the data shows]
💡 **Recommendation:** [what the business should do]
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content


def error_recovery(question: str, error: str, schema: str) -> str:
    """
    When SQL fails, explain why in plain English
    and suggest a better question
    """
    prompt = f"""
You are a helpful AI assistant for a business intelligence tool.

The user asked: "{question}"

This caused an error: {error}

The database schema is:
{schema}

Your job:
1. Explain in simple terms why this query failed (1 sentence, no technical jargon)
2. Suggest 2-3 better ways to ask the same question that would work

Format your response as:
❌ **Why it failed:** [simple explanation]
✅ **Try asking instead:**
- [suggestion 1]
- [suggestion 2]
- [suggestion 3]
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content


def detect_anomalies(question: str, df_summary: str) -> str:
    """
    Automatically detects anomalies or unusual patterns in results
    """
    prompt = f"""
You are a senior data analyst with expertise in anomaly detection.

The user asked: "{question}"

The data result is:
{df_summary}

Your job:
- Look for unusual patterns, outliers, or anomalies in this data
- If you find anomalies, explain them clearly and why they matter
- If everything looks normal, say so briefly
- Give a business impact assessment if anomalies exist

Format your response as:
🔍 *Anomaly Check: [what you found or "No anomalies detected"]
⚠️ *Business Impact: [why this matters or "Data looks healthy"]
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=250
    )

    return response.choices[0].message.content