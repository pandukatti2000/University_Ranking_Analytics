from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    Typed state representation for the LangGraph analytical agent workflow.
    """
    thread_id: str
    user_question: str
    messages: List[Dict[str, str]]
    intent: str  # 'sql_query', 'deterministic_tool', 'general_info', 'clarification'
    query_plan: str
    generated_sql: Optional[str]
    sql_valid: bool
    sql_error: Optional[str]
    query_results: Optional[List[Dict[str, Any]]]
    final_answer: str
    visualization_recommendation: Optional[Dict[str, Any]]
    execution_time_ms: float
