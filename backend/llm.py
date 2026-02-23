import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from config.settings import GROQ_API_KEY
from prompts.sql_prompt import sql_prompt, get_prompt_inputs
from backend.validator import clean_sql, is_safe_query
from backend.database import get_schema
from backend.rag import save_pending_query, get_similar_queries

# Initialize Groq LLM
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Build the chain
sql_chain = sql_prompt | llm | StrOutputParser()


def generate_sql(question: str, context: str = "") -> tuple[str, bool, str]:
    try:
        schema = get_schema()
        rag_examples = get_similar_queries(question)

        # Add conversation context to question if exists
        full_question = question
        if context:
            full_question = f"{context}Current Question: {question}"

        inputs = get_prompt_inputs(
            schema=schema,
            question=full_question,
            rag_examples=rag_examples
        )

        raw_sql = sql_chain.invoke(inputs)
        cleaned_sql = clean_sql(raw_sql)
        is_safe, reason = is_safe_query(cleaned_sql)

        # inside generate_sql function, change this line:
        if is_safe:
            save_pending_query(question, cleaned_sql)
        return cleaned_sql, is_safe, reason

    except Exception as e:
        return "", False, f"❌ LLM Error: {str(e)}"