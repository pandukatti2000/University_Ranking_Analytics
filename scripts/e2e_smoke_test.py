import sys
import os
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        from app.core import orjson_shim
        sys.modules["orjson"] = orjson_shim
        from app.core import ormsgpack_shim
        sys.modules["ormsgpack"] = ormsgpack_shim
        sys.modules["xarray"] = None
        sys.modules["statsmodels"] = None
    except Exception:
        pass

def print_step(title: str):
    print(f"\n{'='*70}\n[SMOKE TEST] {title}\n{'='*70}")

def run_smoke_test():
    start_time = time.time()
    checks = []

    # 1. Database Connectivity & Row Counts
    print_step("1. Checking PostgreSQL Connection & Row Counts")
    try:
        from app.database.session import engine, readonly_engine
        from sqlalchemy import text
        with engine.connect() as conn:
            unis = conn.execute(text("SELECT COUNT(*) FROM university")).scalar()
            rankings = conn.execute(text("SELECT COUNT(*) FROM university_ranking_year")).scalar()
            demos = conn.execute(text("SELECT COUNT(*) FROM university_year")).scalar()
            print(f"  [PASS] Connected to PostgreSQL: {unis} universities, {rankings} ranking rows, {demos} demographic rows.")
            assert unis == 1247
            assert rankings == 29612
            assert demos == 1085
        checks.append(("PostgreSQL Database & Row Counts", "PASSED"))
    except Exception as e:
        print(f"  [FAIL] Database check failed: {e}")
        checks.append(("PostgreSQL Database & Row Counts", f"FAILED: {e}"))

    # 2. Readonly Security Enforcement
    print_step("2. Checking Read-Only Security Policy")
    try:
        from sqlalchemy.exc import DBAPIError
        with readonly_engine.connect() as conn:
            try:
                conn.execute(text("CREATE TABLE evil_table (id INT)"))
                print("  [FAIL] Read-only violation! CREATE TABLE succeeded.")
                checks.append(("Read-Only Role Enforcement", "FAILED"))
            except DBAPIError:
                print("  [PASS] Read-only policy enforced: DDL blocked as expected.")
                checks.append(("Read-Only Role Enforcement", "PASSED"))
    except Exception as e:
        print(f"  [FAIL] Security check failed: {e}")
        checks.append(("Read-Only Role Enforcement", f"FAILED: {e}"))

    # 3. Deterministic Analytics Services
    print_step("3. Testing Analytics Services")
    try:
        from app.database.session import SessionLocal
        from app.services.overview_service import OverviewService
        from app.services.comparison_service import ComparisonService
        from app.services.trends_service import TrendsService
        from app.services.demographics_service import DemographicsService

        with SessionLocal() as db:
            kpis = OverviewService.get_overview_kpis(db)
            print(f"  [PASS] OverviewService: {kpis.total_universities} universities, {kpis.total_countries} countries.")
            
            comp = ComparisonService.compare_universities(db, university_ids=[1, 2], system_id=1)
            print(f"  [PASS] ComparisonService: {len(comp.universities)} universities compared under THE.")
            
            trends = TrendsService.get_university_trends(db, university_ids=[1, 2], criteria_id=1)
            print(f"  [PASS] TrendsService: {len(trends.trends)} trend series loaded.")
            
            demo = DemographicsService.get_demographics_overview(db)
            print(f"  [PASS] DemographicsService: {demo.total_observations} records analyzed.")
            
        checks.append(("Analytics Services Engine", "PASSED"))
    except Exception as e:
        print(f"  [FAIL] Analytics services check failed: {e}")
        checks.append(("Analytics Services Engine", f"FAILED: {e}"))

    # 4. FastAPI Endpoints via TestClient
    print_step("4. Testing FastAPI Endpoints")
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        r_health = client.get("/health")
        assert r_health.status_code == 200 and r_health.json()["status"] == "healthy"
        
        r_over = client.get("/overview")
        assert r_over.status_code == 200 and r_over.json()["total_universities"] == 1247
        
        r_unis = client.get("/universities?limit=5")
        assert r_unis.status_code == 200 and len(r_unis.json()) == 5
        
        print(f"  [PASS] FastAPI Endpoints responding with status 200 OK.")
        checks.append(("FastAPI Endpoints", "PASSED"))
    except Exception as e:
        print(f"  [FAIL] FastAPI check failed: {e}")
        checks.append(("FastAPI Endpoints", f"FAILED: {e}"))

    # 5. LangGraph AI Assistant & SQL Safety Validator
    print_step("5. Testing LangGraph Copilot & SQL Safety AST Validator")
    try:
        from app.llm.sql_safety import SQLSafetyValidator
        from app.agents.workflow import run_copilot

        # Safety check: multi-statement injection
        valid, _, err = SQLSafetyValidator.validate_and_sanitize("SELECT * FROM university; DROP TABLE university;")
        assert valid is False
        print(f"  [PASS] SQL Safety AST Validator correctly blocked SQL injection attack.")

        # Workflow check
        state = run_copilot("Which countries have the most universities represented?", thread_id="smoke-test-thread")
        assert state["sql_valid"] is True
        assert len(state["query_results"]) > 0
        assert "final_answer" in state and len(state["final_answer"]) > 10
        print(f"  [PASS] LangGraph Copilot workflow executed successfully (retrieved {len(state['query_results'])} rows).")
        checks.append(("LangGraph AI Copilot & SQL Safety", "PASSED"))
    except Exception as e:
        print(f"  [FAIL] AI copilot check failed: {e}")
        checks.append(("LangGraph AI Copilot & SQL Safety", f"FAILED: {e}"))

    # 6. Streamlit Frontend Components & Charts
    print_step("6. Testing Streamlit Frontend Views & Chart Generators")
    try:
        from frontend.views.overview import render_overview
        from frontend.views.comparison import render_comparison
        from frontend.views.ai_copilot import render_ai_copilot
        import pandas as pd
        from frontend.components.charts import create_radar_chart, create_bar_chart

        df_sample = pd.DataFrame([
            {"category": "Teaching", "score": 85.0, "group": "Uni A"},
            {"category": "Research", "score": 90.0, "group": "Uni A"}
        ])
        fig1 = create_radar_chart(df_sample, "category", "score", "group", "Smoke Radar")
        fig2 = create_bar_chart(df_sample, "category", "score", "group", "Smoke Bar")
        assert fig1 is not None and fig2 is not None
        print(f"  [PASS] Streamlit components and Plotly charts generated cleanly.")
        checks.append(("Streamlit Frontend & Plotly Suite", "PASSED"))
    except Exception as e:
        print(f"  [FAIL] Frontend check failed: {e}")
        checks.append(("Streamlit Frontend & Plotly Suite", f"FAILED: {e}"))

    # Summary Table
    total_elapsed = time.time() - start_time
    print(f"\n{'='*70}\nSMOKE TEST SUMMARY RESULTS (Completed in {total_elapsed:.2f}s)\n{'='*70}")
    all_passed = True
    for component, result in checks:
        status_tag = "[PASS]" if result == "PASSED" else "[FAIL]"
        print(f"  {status_tag:<8} {component:<38} : {result}")
        if result != "PASSED":
            all_passed = False

    print("="*70)
    if all_passed:
        print("ALL SYSTEMS OPERATIONAL: End-to-End Platform is Healthy & Verified!")
        sys.exit(0)
    else:
        print("SOME CHECKS FAILED. See above output for error details.")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test()
