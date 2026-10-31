import time
import re
from typing import Dict, Any, List
from sqlalchemy import text
from app.agents.state import AgentState
from app.llm.client import llm_client
from app.llm.sql_safety import SQLSafetyValidator
from app.llm.prompts import SYSTEM_SQL_PROMPT, SYSTEM_ANSWER_PROMPT
from app.database.session import readonly_engine
from app.core.tracing import traceable

@traceable(name="intake_and_classify")
def intake_and_classify(state: AgentState) -> Dict[str, Any]:
    """Intake user question and classify intent."""
    question = state.get("user_question", "").strip()
    q_lower = question.lower()

    # Rule-based / keyword classification for robust routing
    if any(k in q_lower for k in ["how do the three ranking systems differ", "methodology", "explain cwur", "explain arwu", "what is pcp", "what is hici"]):
        intent = "general_info"
        plan = "Provide methodological explanation of ranking criteria and system structures."
    else:
        intent = "sql_query"
        plan = "Generate a safe, read-only SQL query to extract empirical ranking/demographic facts."

    return {
        "intent": intent,
        "query_plan": plan
    }

def plan_and_retrieve_context(state: AgentState) -> Dict[str, Any]:
    """Retrieve domain schema context and build detailed execution plan."""
    return {
        "query_plan": f"Executing safe SQL generation for question: '{state.get('user_question')}'"
    }

@traceable(name="generate_sql", run_type="chain")
def generate_sql_node(state: AgentState) -> Dict[str, Any]:
    """Generate PostgreSQL query using LLM client."""
    messages = [
        {"role": "system", "content": SYSTEM_SQL_PROMPT},
        {"role": "user", "content": state.get("user_question", "")}
    ]
    raw_sql = llm_client.generate(messages, temperature=0.0)

    # Clean markdown fences if present
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", raw_sql, re.DOTALL | re.IGNORECASE)
    cleaned_sql = match.group(1).strip() if match else raw_sql.strip()

    return {
        "generated_sql": cleaned_sql
    }

@traceable(name="validate_sql", run_type="chain")
def validate_sql_node(state: AgentState) -> Dict[str, Any]:
    """Validate query using AST-based SQLGlot safety guard."""
    sql = state.get("generated_sql") or ""
    is_valid, sanitized_sql, error_msg = SQLSafetyValidator.validate_and_sanitize(sql, max_limit=100)

    return {
        "sql_valid": is_valid,
        "generated_sql": sanitized_sql if is_valid else sql,
        "sql_error": error_msg
    }

@traceable(name="execute_query", run_type="tool")
def execute_query_node(state: AgentState) -> Dict[str, Any]:
    """Execute validated query against PostgreSQL using read-only credentials and statement timeout."""
    if not state.get("sql_valid"):
        return {
            "query_results": [],
            "sql_error": state.get("sql_error") or "Query rejected by SQL safety validator."
        }

    sql = state.get("generated_sql")
    try:
        with readonly_engine.connect() as conn:
            # Enforce 5-second query timeout
            conn.execute(text("SET statement_timeout = 5000;"))
            result = conn.execute(text(sql))
            rows = [dict(row._mapping) for row in result.fetchall()]
            return {
                "query_results": rows,
                "sql_error": None
            }
    except Exception as e:
        return {
            "query_results": [],
            "sql_error": f"Database execution error: {str(e)}"
        }

@traceable(name="generate_answer", run_type="chain")
def generate_answer_node(state: AgentState) -> Dict[str, Any]:
    """Synthesize evidence-based answer strictly grounded in database results."""
    question = state.get("user_question", "")
    results = state.get("query_results", [])
    sql_error = state.get("sql_error")

    if sql_error:
        final_answer = (
            f"I encountered a query limitation while processing your request:\n\n"
            f"> **Safety/Execution Notice:** {sql_error}\n\n"
            f"Please refine your question or specify the university, country, or ranking system."
        )
        return {"final_answer": final_answer}

    if not results:
        final_answer = (
            f"The database returned no matching records for: **'{question}'**.\n\n"
            f"**Data Limitations to consider:**\n"
            f"- Times Higher Education (THE) covers 2011–2016 (245 universities)\n"
            f"- Shanghai Ranking (ARWU) covers 2005–2015 (93 research universities)\n"
            f"- CWUR covers 2012–2015 (1,024 universities)\n"
            f"- Demographics are available exclusively for THE institutions (2011–2016)"
        )
        return {"final_answer": final_answer}

    # Format grounded summary
    if llm_client.is_live:
        context_str = f"User Question: {question}\n\nSQL Results ({len(results)} rows total, showing up to 75):\n"
        for r in results[:75]:
            context_str += f"- {r}\n"

        messages = [
            {"role": "system", "content": SYSTEM_ANSWER_PROMPT},
            {"role": "user", "content": context_str}
        ]
        final_answer = llm_client.generate(messages, temperature=0.1)
    else:
        # High quality offline deterministic template
        final_answer = f"### Evidence-Based Analytics Answer\n\n"
        final_answer += f"Query returned **{len(results)} records** for *'{question}'*:\n\n"
        
        # Display sample table of results
        keys = list(results[0].keys())
        header = " | ".join(keys)
        separator = " | ".join(["---"] * len(keys))
        final_answer += f"| {header} |\n| {separator} |\n"
        for r in results[:10]:
            vals = [str(r.get(k, "")) for k in keys]
            final_answer += f"| {' | '.join(vals)} |\n"
        
        final_answer += f"\n*All results are directly extracted from PostgreSQL `university_ranking_db`.*"

    return {"final_answer": final_answer}

@traceable(name="recommend_visualization", run_type="chain")
def recommend_visualization_node(state: AgentState) -> Dict[str, Any]:
    """Recommend optimal visualization format based on the structure of the retrieved data."""
    results = state.get("query_results", [])
    if not results:
        return {"visualization_recommendation": None}

    sample = results[0]
    keys = list(sample.keys())

    has_year = any("year" in k.lower() for k in keys)
    has_score = any("score" in k.lower() or "rank" in k.lower() or "count" in k.lower() for k in keys)
    has_name = any("name" in k.lower() or "country" in k.lower() or "criteria" in k.lower() for k in keys)

    if has_year and has_score and len(results) > 1:
        rec = {
            "chart_type": "line",
            "x_axis": "year",
            "y_axis": next(k for k in keys if "score" in k.lower() or "rank" in k.lower() or "count" in k.lower()),
            "color_by": next((k for k in keys if "name" in k.lower() or "university" in k.lower()), None),
            "title": "Historical Trend"
        }
    elif has_name and has_score:
        rec = {
            "chart_type": "bar",
            "x_axis": next(k for k in keys if "name" in k.lower() or "country" in k.lower() or "university" in k.lower()),
            "y_axis": next(k for k in keys if "score" in k.lower() or "rank" in k.lower() or "count" in k.lower()),
            "title": "Performance Comparison"
        }
    else:
        rec = {
            "chart_type": "table",
            "columns": keys,
            "title": "Data Records Table"
        }

    return {"visualization_recommendation": rec}

def general_explanation_node(state: AgentState) -> Dict[str, Any]:
    """Handle general methodology and system comparison questions."""
    question = state.get("user_question", "")
    answer = (
        "### World University Ranking Systems Methodology Overview\n\n"
        "The platform unifies three global ranking systems with distinct evaluation frameworks:\n\n"
        "1. **Times Higher Education (THE)** (2011–2016):\n"
        "   - Evaluates: *Teaching* (30%), *Research* (30%), *Citations* (30%), *International Outlook* (7.5%), and *Industry Income* (2.5%).\n"
        "   - Nature: All criteria are normalized **scores (0–100)** where higher indicates superior performance.\n\n"
        "2. **Shanghai Ranking (ARWU)** (2005–2015):\n"
        "   - Evaluates: Elite research output (*Alumni* & *Staff Nobel/Fields Prizes*, *Highly Cited Researchers*, *Nature & Science papers*, *SCI/SSCI publications*, and *PCP*).\n"
        "   - Nature: Normalized **scores (0–100)** benchmarked to the top institution = 100.\n\n"
        "3. **Center for World University Rankings (CWUR)** (2012–2015):\n"
        "   - Evaluates: Education quality, alumni employment, faculty quality, publications, influence, citations, patents.\n"
        "   - **Important Distinction:** Criteria 14–20 are **ordinal ranks (1 to 1,000)** where **lower is better** (1 = world #1). Criterion 21 (`Total CWUR`) is a **score (43–100)** where higher is better.\n\n"
        "*Methodology Note: Because each system employs different indicators, normalizations, and weights, scores cannot be directly combined or compared across systems.*"
    )
    return {
        "final_answer": answer,
        "query_results": [],
        "generated_sql": None,
        "visualization_recommendation": None
    }
