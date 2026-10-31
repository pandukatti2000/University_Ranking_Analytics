from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from datetime import datetime
from app.agents.workflow import run_copilot

router = APIRouter()

# Active threads registry with multi-turn message history
ACTIVE_THREADS: Dict[str, Dict[str, Any]] = {
    "default-thread": {
        "thread_id": "default-thread",
        "title": "Welcome Session",
        "created_at": datetime.now().isoformat(),
        "messages": [
            {
                "role": "assistant",
                "content": "Welcome to University Ranking Analytics Copilot! You can ask questions about world university performance, rankings, trends, and demographics."
            }
        ]
    }
}

class ChatRequest(BaseModel):
    question: str
    thread_id: Optional[str] = "default-thread"

class ChatResponse(BaseModel):
    thread_id: str
    question: str
    final_answer: str
    generated_sql: Optional[str]
    sql_valid: bool
    sql_error: Optional[str]
    row_count: int
    visualization_recommendation: Optional[Dict[str, Any]]
    execution_time_ms: float

class ConversationSummary(BaseModel):
    thread_id: str
    title: str
    created_at: str
    message_count: int

@router.get("", response_model=List[ConversationSummary], summary="List Conversation Threads")
def list_conversations():
    """Retrieve list of active and persisted conversation threads."""
    summaries = []
    for tid, data in ACTIVE_THREADS.items():
        summaries.append(ConversationSummary(
            thread_id=tid,
            title=data.get("title", f"Thread {tid}"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            message_count=len(data.get("messages", []))
        ))
    return summaries

@router.get("/{thread_id}", summary="Get Conversation Thread Detail")
def get_conversation_thread(
    thread_id: str = Path(..., description="Unique thread identifier")
):
    """Retrieve all messages and state for a specific conversation thread."""
    if thread_id not in ACTIVE_THREADS:
        raise HTTPException(status_code=404, detail=f"Conversation thread '{thread_id}' not found.")
    return ACTIVE_THREADS[thread_id]

@router.post("/chat", response_model=ChatResponse, summary="Send Message to AI Copilot")
def chat_with_copilot(payload: ChatRequest):
    """Execute LangGraph conversational workflow and return grounded analytical answer with SQL and visualization."""
    tid = payload.thread_id or "default-thread"
    if tid not in ACTIVE_THREADS:
        ACTIVE_THREADS[tid] = {
            "thread_id": tid,
            "title": payload.question[:40] + "..." if len(payload.question) > 40 else payload.question,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }

    # Record user message
    ACTIVE_THREADS[tid]["messages"].append({
        "role": "user",
        "content": payload.question,
        "timestamp": datetime.now().isoformat()
    })

    # Run LangGraph Agent workflow
    result = run_copilot(payload.question, thread_id=tid)

    # Record assistant answer
    ACTIVE_THREADS[tid]["messages"].append({
        "role": "assistant",
        "content": result.get("final_answer", ""),
        "generated_sql": result.get("generated_sql"),
        "timestamp": datetime.now().isoformat()
    })

    return ChatResponse(
        thread_id=tid,
        question=payload.question,
        final_answer=result.get("final_answer", ""),
        generated_sql=result.get("generated_sql"),
        sql_valid=result.get("sql_valid", False),
        sql_error=result.get("sql_error"),
        row_count=len(result.get("query_results") or []),
        visualization_recommendation=result.get("visualization_recommendation"),
        execution_time_ms=result.get("execution_time_ms", 0.0)
    )
