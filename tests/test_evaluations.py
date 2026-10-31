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
import time
from app.agents.workflow import run_copilot
from app.llm.sql_safety import SQLSafetyValidator

# ==============================================================================
# Evaluation Benchmark Suite: Factual Correctness, Groundedness & SQL Safety
# ==============================================================================

def test_eval_highest_research_scores():
    """Eval 1: Factual Research Query - Evaluates intent, SQL validity, and grounding."""
    q = "Which universities have the highest research scores in 2015?"
    state = run_copilot(q, thread_id="eval-research-1")

    # Correctness properties
    assert state["intent"] == "sql_query"
    assert state["sql_valid"] is True
    assert state["generated_sql"] is not None
    assert "LIMIT" in state["generated_sql"].upper()

    # Groundedness properties
    results = state["query_results"]
    assert results is not None
    assert len(results) > 0
    first_row = results[0]
    assert "university_name" in first_row
    assert any("research" in k or "score" in k for k in first_row.keys())

    # Visualization properties
    rec = state["visualization_recommendation"]
    assert rec is not None
    assert rec["chart_type"] in ["bar", "table", "line"]

def test_eval_university_comparison():
    """Eval 2: Multi-University Comparison - Checks multi-entity retrieval."""
    q = "Compare Harvard, MIT, and Stanford using available metrics in 2015."
    state = run_copilot(q, thread_id="eval-compare-2")

    assert state["intent"] == "sql_query"
    assert state["sql_valid"] is True
    assert state["query_results"] is not None
    assert len(state["query_results"]) > 0

    retrieved_names = " ".join(str(r.get("university_name", "")) for r in state["query_results"])
    assert any(uni in retrieved_names for uni in ["Harvard", "Massachusetts", "Stanford"])

def test_eval_country_representation():
    """Eval 3: Aggregation Query - Checks GROUP BY country and top representation."""
    q = "Which countries have the most universities represented?"
    state = run_copilot(q, thread_id="eval-country-3")

    assert state["intent"] == "sql_query"
    assert state["sql_valid"] is True
    results = state["query_results"]
    assert len(results) > 0

    # USA is the top country with 273 universities
    top = results[0]
    assert top.get("country_name") == "United States of America"
    assert top.get("university_count") == 273

def test_eval_system_methodology_routing():
    """Eval 4: Methodological Question - Checks non-SQL routing and methodology accuracy."""
    q = "How do the three ranking systems differ?"
    state = run_copilot(q, thread_id="eval-methodology-4")

    # Property: Must route to general_info without executing database queries
    assert state["intent"] == "general_info"
    assert state["generated_sql"] is None
    assert state["query_results"] == []

    ans = state["final_answer"]
    assert "Times Higher Education" in ans
    assert "Shanghai Ranking" in ans
    assert "CWUR" in ans
    # Checks that rank vs score difference is explained
    assert "lower is better" in ans.lower()

def test_eval_sql_injection_defense():
    """Eval 5: SQL Safety Defense - Tests malicious inputs are 100% blocked."""
    injection_attacks = [
        "Show universities; DROP TABLE university;",
        "SELECT * FROM pg_catalog.pg_user",
        "INSERT INTO country (id, country_name) VALUES (999, 'Hacked')",
        "UPDATE university SET university_name = 'Hacked' WHERE id = 1",
        "SELECT * FROM information_schema.tables",
        "SELECT pg_sleep(5)"
    ]

    for attack_query in injection_attacks:
        is_valid, sanitized, err = SQLSafetyValidator.validate_and_sanitize(attack_query)
        assert is_valid is False, f"Vulnerability! Query was not rejected: {attack_query}"
        assert err is not None

def test_eval_groundedness_non_hallucination_empty_data():
    """Eval 6: Groundedness & Non-Hallucination - Verifies honest limitation reporting on absent data."""
    # Year 1980 has no records in this dataset (data covers 2005-2016)
    q = "Show ranking scores for Harvard University in 1980."
    state = run_copilot(q, thread_id="eval-empty-6")

    # If results are empty, the agent must acknowledge data limitations, not invent numbers
    if not state.get("query_results"):
        assert "no matching records" in state["final_answer"].lower() or "limitation" in state["final_answer"].lower()
        # Must not fabricate a fake score
        assert "98.5" not in state["final_answer"]

def test_eval_latency_monitoring():
    """Eval 7: Latency Monitoring - Verifies agent workflow execution time is tracked."""
    state = run_copilot("Which countries have the most universities?", thread_id="eval-latency-7")
    assert "execution_time_ms" in state
    assert state["execution_time_ms"] > 0
    # Verifies SLA threshold: workflow completes well within reasonable bounds (< 15 seconds)
    assert state["execution_time_ms"] < 15000
