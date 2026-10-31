import sys
if sys.platform == "win32":
    try:
        from app.core import orjson_shim
        sys.modules["orjson"] = orjson_shim
        from app.core import ormsgpack_shim
        sys.modules["ormsgpack"] = ormsgpack_shim
    except Exception:
        pass

import pytest
from app.llm.sql_safety import SQLSafetyValidator
from app.agents.workflow import run_copilot
from fastapi.testclient import TestClient
from app.main import app

def test_sql_validator_valid_selects():
    """Verify approved SELECT queries pass validation and receive automatic LIMIT."""
    valid_query = "SELECT university_name FROM university WHERE country_id = 73"
    is_valid, sanitized, err = SQLSafetyValidator.validate_and_sanitize(valid_query, max_limit=50)
    assert is_valid is True
    assert err is None
    assert "LIMIT 50" in sanitized.upper()

    # Query with existing within-bound limit
    query_with_limit = "SELECT * FROM country LIMIT 10"
    is_valid, sanitized, err = SQLSafetyValidator.validate_and_sanitize(query_with_limit)
    assert is_valid is True
    assert "LIMIT 10" in sanitized.upper()

    # Query exceeding limit capped to 100
    query_excess_limit = "SELECT * FROM university LIMIT 500"
    is_valid, sanitized, err = SQLSafetyValidator.validate_and_sanitize(query_excess_limit, max_limit=100)
    assert is_valid is True
    assert "LIMIT 100" in sanitized.upper()

def test_sql_validator_reject_dml_and_ddl():
    """Verify destructive statements are strictly blocked by AST analysis."""
    bad_queries = [
        "INSERT INTO country (id, country_name) VALUES (999, 'Hackerland')",
        "UPDATE university SET university_name = 'Compromised' WHERE id = 1",
        "DELETE FROM country WHERE id = 1",
        "DROP TABLE university CASCADE",
        "ALTER TABLE country ADD COLUMN hacked TEXT",
        "TRUNCATE TABLE university_ranking_year",
        "CREATE TABLE backdoors (id INT)"
    ]

    for q in bad_queries:
        is_valid, sanitized, err = SQLSafetyValidator.validate_and_sanitize(q)
        assert is_valid is False
        assert err is not None
        assert any(term in err.lower() for term in ["forbidden", "must be a select", "detected"])

def test_sql_validator_reject_multi_statements():
    """Verify semicolon statement chaining is strictly rejected."""
    multi_stmt = "SELECT * FROM country; DROP TABLE country;"
    is_valid, sanitized, err = SQLSafetyValidator.validate_and_sanitize(multi_stmt)
    assert is_valid is False
    assert "multiple" in err.lower()

def test_sql_validator_reject_unapproved_tables_and_functions():
    """Verify attempts to probe system catalogs or unapproved tables are blocked."""
    probing_queries = [
        "SELECT * FROM pg_catalog.pg_tables",
        "SELECT * FROM information_schema.columns",
        "SELECT pg_sleep(5)",
        "SELECT * FROM non_existent_secret_table"
    ]

    for q in probing_queries:
        is_valid, sanitized, err = SQLSafetyValidator.validate_and_sanitize(q)
        assert is_valid is False
        assert err is not None

def test_langgraph_general_info_routing():
    """Verify general methodology questions route to explanation node without SQL generation."""
    state = run_copilot("How do the three ranking systems differ?", thread_id="test-methodology")
    assert state["intent"] == "general_info"
    assert state["generated_sql"] is None
    assert "Times Higher Education" in state["final_answer"]
    assert "Shanghai Ranking" in state["final_answer"]
    assert "CWUR" in state["final_answer"]

def test_langgraph_sql_query_execution():
    """Verify factual questions generate safe SQL, execute read-only, and ground answers."""
    state = run_copilot("Which universities have the highest research scores?", thread_id="test-research")
    assert state["intent"] == "sql_query"
    assert state["sql_valid"] is True
    assert state["generated_sql"] is not None
    assert state["query_results"] is not None
    assert len(state["query_results"]) > 0
    assert state["final_answer"] != ""
    assert state["visualization_recommendation"] is not None

def test_api_chat_endpoint():
    """Verify FastAPI /conversations/chat endpoint returns complete response payload."""
    client = TestClient(app)
    payload = {
        "question": "Which countries have the most universities represented?",
        "thread_id": "test-chat-thread"
    }
    res = client.post("/conversations/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["thread_id"] == "test-chat-thread"
    assert data["sql_valid"] is True
    assert data["row_count"] > 0
    assert "final_answer" in data
    assert data["execution_time_ms"] > 0
