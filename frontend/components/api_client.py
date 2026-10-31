import os
import requests
import streamlit as st
from typing import Dict, Any, List, Optional
import pandas as pd

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def is_backend_online() -> bool:
    """Check if FastAPI backend service is reachable."""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False

# ==============================================================================
# Cached Catalog & Lookup Methods
# ==============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def get_overview_data() -> Dict[str, Any]:
    """Retrieve system overview and high-level KPIs."""
    if is_backend_online():
        try:
            r = requests.get(f"{API_BASE_URL}/overview", timeout=5.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

    # Direct Service Fallback
    from app.database.session import SessionLocal
    from app.services.overview_service import OverviewService
    with SessionLocal() as db:
        return OverviewService.get_overview_kpis(db).model_dump()

@st.cache_data(ttl=600, show_spinner=False)
def get_universities_list(limit: int = 1500) -> List[Dict[str, Any]]:
    """Retrieve list of universities with IDs, names, and country names."""
    if is_backend_online():
        try:
            r = requests.get(f"{API_BASE_URL}/universities?limit={limit}", timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get("items", [])
        except Exception:
            pass

    from app.database.session import readonly_engine
    from sqlalchemy import text
    with readonly_engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT u.id, u.university_name, c.country_name
            FROM university u
            LEFT JOIN country c ON u.country_id = c.id
            ORDER BY u.university_name ASC
            LIMIT :lim
        """), {"lim": limit}).fetchall()
        return [{"id": r[0], "university_name": r[1], "country_name": r[2]} for r in rows]

@st.cache_data(ttl=600, show_spinner=False)
def get_countries_list() -> List[Dict[str, Any]]:
    """Retrieve all countries."""
    if is_backend_online():
        try:
            r = requests.get(f"{API_BASE_URL}/countries", timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                return [
                    {
                        "id": c.get("country_id") or c.get("id"),
                        "country_id": c.get("country_id") or c.get("id"),
                        "country_name": c.get("country_name"),
                        "university_count": c.get("university_count", 0)
                    }
                    for c in data
                ]
        except Exception:
            pass

    from app.database.session import readonly_engine
    from sqlalchemy import text
    with readonly_engine.connect() as conn:
        rows = conn.execute(text("SELECT id, country_name FROM country ORDER BY country_name ASC")).fetchall()
        return [{"id": r[0], "country_id": r[0], "country_name": r[1], "university_count": 0} for r in rows]

@st.cache_data(ttl=600, show_spinner=False)
def get_ranking_systems_and_criteria() -> List[Dict[str, Any]]:
    """Retrieve ranking systems and criteria catalog with nested criteria."""
    if is_backend_online():
        try:
            r_sys = requests.get(f"{API_BASE_URL}/ranking-systems", timeout=5.0)
            r_crit = requests.get(f"{API_BASE_URL}/criteria", timeout=5.0)
            if r_sys.status_code == 200 and r_crit.status_code == 200:
                systems = r_sys.json()
                criteria = r_crit.json()
                sys_map = {s["id"]: {"id": s["id"], "system_name": s["system_name"], "criteria": []} for s in systems}
                for c in criteria:
                    sys_id = c.get("ranking_system_id")
                    if sys_id in sys_map:
                        sys_map[sys_id]["criteria"].append({
                            "id": c["id"],
                            "criteria_name": c["criteria_name"],
                            "metric_type": c.get("metric_type", "score")
                        })
                return list(sys_map.values())
        except Exception:
            pass

    from app.database.session import readonly_engine
    from sqlalchemy import text
    with readonly_engine.connect() as conn:
        systems = conn.execute(text("SELECT id, system_name FROM ranking_system ORDER BY id ASC")).fetchall()
        criteria = conn.execute(text("SELECT id, ranking_system_id, criteria_name FROM ranking_criteria ORDER BY id ASC")).fetchall()

        sys_map = {s[0]: {"id": s[0], "system_name": s[1], "criteria": []} for s in systems}
        for c in criteria:
            if c[1] in sys_map:
                sys_map[c[1]]["criteria"].append({"id": c[0], "criteria_name": c[2]})
        return list(sys_map.values())

# ==============================================================================
# Analytics Endpoints
# ==============================================================================

def get_comparison_data(university_ids: List[int], system_id: int, start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict[str, Any]:
    """Retrieve side-by-side comparison across institutions."""
    if is_backend_online():
        try:
            ids_param = ",".join(map(str, university_ids))
            url = f"{API_BASE_URL}/analytics/compare?university_ids={ids_param}&system_id={system_id}"
            if start_year:
                url += f"&start_year={start_year}"
            if end_year:
                url += f"&end_year={end_year}"
            r = requests.get(url, timeout=5.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

    from app.database.session import SessionLocal
    from app.services.comparison_service import ComparisonService
    with SessionLocal() as db:
        res = ComparisonService.compare_universities(
            db,
            university_ids=university_ids,
            system_id=system_id,
            start_year=start_year,
            end_year=end_year
        )
        return res.model_dump()

def get_historical_trends(university_ids: List[int], ranking_criteria_id: int) -> Dict[str, Any]:
    """Retrieve historical score trajectories across available years."""
    if is_backend_online():
        try:
            ids_param = ",".join(map(str, university_ids))
            r = requests.get(
                f"{API_BASE_URL}/analytics/trends?university_ids={ids_param}&criteria_id={ranking_criteria_id}",
                timeout=5.0
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

    from app.database.session import SessionLocal
    from app.services.trends_service import TrendsService
    with SessionLocal() as db:
        res = TrendsService.get_university_trends(
            db,
            university_ids=university_ids,
            criteria_id=ranking_criteria_id
        )
        return res.model_dump()

def get_country_analytics(country_id: Optional[int] = None) -> Any:
    """Retrieve country analytics and comparative distributions."""
    if is_backend_online():
        try:
            if country_id:
                url = f"{API_BASE_URL}/countries/{country_id}"
            else:
                url = f"{API_BASE_URL}/countries"
            r = requests.get(url, timeout=5.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

    from app.database.session import SessionLocal
    from app.services.country_service import CountryService
    with SessionLocal() as db:
        if country_id:
            res = CountryService.get_country_detail(db, country_id=country_id)
            return res.model_dump()
        else:
            res = CountryService.get_country_university_distribution(db)
            return [c.model_dump() for c in res]

def get_criteria_analytics(ranking_system_id: int) -> List[Dict[str, Any]]:
    """Retrieve criteria distribution and correlations."""
    if is_backend_online():
        try:
            r = requests.get(f"{API_BASE_URL}/analytics/criteria?system_id={ranking_system_id}", timeout=5.0)
            if r.status_code == 200:
                raw = r.json()
                data = raw.get("distributions", []) if isinstance(raw, dict) else raw
                for item in data:
                    s = item.get("std_dev") if item.get("std_dev") is not None else item.get("std", 0.0)
                    item["std"] = s
                    item["std_dev"] = s
                return data
        except Exception:
            pass

    from app.database.session import SessionLocal
    from app.services.criteria_service import CriteriaService
    with SessionLocal() as db:
        dists = CriteriaService.get_criteria_distributions(db, system_id=ranking_system_id)
        data = [d.model_dump() for d in dists]
        for item in data:
            s = item.get("std_dev") if item.get("std_dev") is not None else item.get("std", 0.0)
            item["std"] = s
            item["std_dev"] = s
        return data

def get_demographics_analytics() -> Dict[str, Any]:
    """Retrieve student demographics analysis."""
    if is_backend_online():
        try:
            r = requests.get(f"{API_BASE_URL}/analytics/demographics", timeout=5.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

    from app.database.session import SessionLocal
    from app.services.demographics_service import DemographicsService
    with SessionLocal() as db:
        res = DemographicsService.get_demographics_overview(db)
        return res.model_dump()

# ==============================================================================
# AI Conversational Copilot
# ==============================================================================

def send_chat_message(question: str, thread_id: str = "streamlit-session") -> Dict[str, Any]:
    """Send natural language query to LangGraph AI assistant."""
    if is_backend_online():
        try:
            r = requests.post(
                f"{API_BASE_URL}/conversations/chat",
                json={"question": question, "thread_id": thread_id},
                timeout=45.0
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

    from app.agents.workflow import run_copilot
    state = run_copilot(question, thread_id=thread_id)
    return {
        "thread_id": state.get("thread_id", thread_id),
        "user_question": state.get("user_question", question),
        "intent": state.get("intent", "sql_query"),
        "query_plan": state.get("query_plan"),
        "generated_sql": state.get("generated_sql"),
        "sql_valid": state.get("sql_valid", False),
        "validation_error": state.get("validation_error"),
        "row_count": len(state.get("query_results", [])),
        "query_results": state.get("query_results", []),
        "final_answer": state.get("final_answer", ""),
        "visualization_recommendation": state.get("visualization_recommendation"),
        "execution_time_ms": state.get("execution_time_ms", 0.0)
    }
