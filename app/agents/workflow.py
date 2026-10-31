import time
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes import (
    intake_and_classify,
    plan_and_retrieve_context,
    generate_sql_node,
    validate_sql_node,
    execute_query_node,
    generate_answer_node,
    recommend_visualization_node,
    general_explanation_node
)

def route_after_intake(state: AgentState) -> str:
    if state.get("intent") == "general_info":
        return "general_explanation"
    return "plan_and_retrieve_context"

def route_after_validation(state: AgentState) -> str:
    if state.get("sql_valid"):
        return "execute_query"
    return "generate_answer"

def build_workflow() -> Any:
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("intake_and_classify", intake_and_classify)
    workflow.add_node("general_explanation", general_explanation_node)
    workflow.add_node("plan_and_retrieve_context", plan_and_retrieve_context)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_query", execute_query_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("recommend_visualization", recommend_visualization_node)

    # Set Entry Point
    workflow.set_entry_point("intake_and_classify")

    # Conditional Routing
    workflow.add_conditional_edges(
        "intake_and_classify",
        route_after_intake,
        {
            "general_explanation": "general_explanation",
            "plan_and_retrieve_context": "plan_and_retrieve_context"
        }
    )

    workflow.add_edge("plan_and_retrieve_context", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")

    workflow.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "execute_query": "execute_query",
            "generate_answer": "generate_answer"
        }
    )

    workflow.add_edge("execute_query", "generate_answer")
    workflow.add_edge("generate_answer", "recommend_visualization")
    workflow.add_edge("recommend_visualization", END)
    workflow.add_edge("general_explanation", END)

    # Use persistent checkpointer for multi-turn conversation memory
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app

# Compiled graph singleton
agent_executor = build_workflow()

def run_copilot(question: str, thread_id: str = "default-thread") -> AgentState:
    """Execute conversational AI workflow for a user question."""
    start_time = time.time()
    initial_state: AgentState = {
        "thread_id": thread_id,
        "user_question": question,
        "messages": [{"role": "user", "content": question}],
        "intent": "sql_query",
        "query_plan": "",
        "generated_sql": None,
        "sql_valid": False,
        "sql_error": None,
        "query_results": None,
        "final_answer": "",
        "visualization_recommendation": None,
        "execution_time_ms": 0.0
    }

    config = {"configurable": {"thread_id": thread_id}}
    result = agent_executor.invoke(initial_state, config=config)
    result["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
    return result
