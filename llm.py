"""LLM setup for the Job Hunter app: connects to a local Ollama model."""

from langchain_ollama import ChatOllama


def get_llm():
    """
    Returns a LangChain chat model instance, or None if it cannot be created
    (e.g. Ollama is not installed/running). Callers should handle the None
    case with a non-LLM fallback so the app still works.
    """
    try:
        return ChatOllama(
            model="qwen2.5:7b",
            temperature=0,
        )
    except (ImportError, ConnectionError, OSError):
        return None