import os
import functools
from typing import Callable, Any, Optional
from app.core.config import settings

def setup_langsmith_tracing():
    """Configure LangSmith tracing environment variables securely."""
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT or "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "university-ranking-analytics"
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

def traceable(name: Optional[str] = None, run_type: str = "chain"):
    """
    Tracing decorator: uses LangSmith's @traceable if enabled and configured,
    otherwise acts as a zero-overhead pass-through decorator.
    """
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
        try:
            from langsmith import traceable as ls_traceable
            return ls_traceable(name=name, run_type=run_type)
        except Exception:
            pass

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)
        return wrapper

    return decorator

# Initialize on module load
setup_langsmith_tracing()
