import os
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from dotenv import load_dotenv

load_dotenv()


def run_sql_agent(question: str, db_url: str = None) -> str:
    """
    Takes a natural language question, converts to SQL, runs it,
    and returns a plain English answer.
    """
    if db_url is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///./data/bizintel.db")

    # Fix SQLAlchemy URL format for SQLite
    if db_url.startswith("sqlite:///./"):
        db_url = db_url  # already correct

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )

    db = SQLDatabase.from_uri(db_url)

    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=False,
        handle_parsing_errors=True,
    )

    system_context = """
    You are a business intelligence analyst. When answering questions:
    - Always give specific numbers from the data
    - Mention top/bottom performers
    - Give actionable business insights
    - Keep answers concise but informative
    """

    try:
        result = agent.invoke({"input": system_context + "\n\nQuestion: " + question})
        return result["output"]
    except Exception as e:
        return f"I couldn't answer that question. Error: {str(e)}"