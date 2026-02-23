import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path=".chromadb")

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Two separate collections — trusted vs pending
trusted_collection = client.get_or_create_collection(
    name="trusted_queries",
    embedding_function=embedding_fn
)

pending_collection = client.get_or_create_collection(
    name="pending_queries",
    embedding_function=embedding_fn
)


def save_pending_query(question: str, sql: str):
    """
    Saves query as pending — waiting for user feedback
    """
    try:
        pending_collection.add(
            documents=[question],
            metadatas=[{"sql": sql}],
            ids=[str(abs(hash(question)))]
        )
    except Exception as e:
        print(f"⚠️ Pending save error: {e}")


def approve_query(question: str, sql: str):
    """
    User gave thumbs up — move to trusted collection
    """
    try:
        trusted_collection.add(
            documents=[question],
            metadatas=[{"sql": sql}],
            ids=[str(abs(hash(question)))]
        )
        print(f"✅ Approved and saved to RAG: {question}")
    except Exception as e:
        print(f"⚠️ Approve error: {e}")


def reject_query(question: str):
    """
    User gave thumbs down — delete from pending
    """
    try:
        pending_collection.delete(
            ids=[str(abs(hash(question)))]
        )
        print(f"🗑️ Rejected query removed: {question}")
    except Exception as e:
        print(f"⚠️ Reject error: {e}")


def get_similar_queries(question: str, n_results: int = 3) -> str:
    """
    Only retrieves from TRUSTED collection
    """
    try:
        if trusted_collection.count() == 0:
            return ""

        results = trusted_collection.query(
            query_texts=[question],
            n_results=min(n_results, trusted_collection.count())
        )

        if not results["documents"][0]:
            return ""

        examples = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            examples.append(f"Question: {doc}\nSQL: {meta['sql']}")

        return "\n\n".join(examples)

    except Exception as e:
        print(f"⚠️ RAG retrieval error: {e}")
        return ""


def get_query_count() -> int:
    try:
        return trusted_collection.count()
    except:
        return 0