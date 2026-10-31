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
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_root_index(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["docs"] == "/docs"

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_overview_endpoint(client):
    res = client.get("/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_universities"] == 1247
    assert data["total_countries"] == 74
    assert data["total_ranking_systems"] == 3
    assert data["total_ranking_records"] == 29612
    assert len(data["ranking_systems"]) == 3

def test_multi_system_universities(client):
    res = client.get("/overview/multi-system?min_systems=3")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 75
    names = [u["university_name"] for u in data]
    assert "Harvard University" in names
    assert "University of Oxford" in names

def test_universities_catalog_search(client):
    res = client.get("/universities?search=harvard")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["university_name"] == "Harvard University"

def test_university_detail_endpoint(client):
    res = client.get("/universities/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["university_name"] == "Harvard University"
    assert data["country_name"] == "United States of America"
    assert len(data["ranking_systems"]) >= 2

def test_countries_endpoint(client):
    res = client.get("/countries")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 74
    # Top country is USA
    assert data[0]["country_name"] == "United States of America"
    assert data[0]["university_count"] == 273

def test_country_detail_endpoint(client):
    res = client.get("/countries/73")
    assert res.status_code == 200
    data = res.json()
    assert data["country_id"] == 73
    assert data["country_name"] == "United States of America"
    assert data["total_universities"] == 273

def test_ranking_systems_and_criteria(client):
    res_sys = client.get("/ranking-systems")
    assert res_sys.status_code == 200
    systems = res_sys.json()
    assert len(systems) == 3

    # Criteria for System 1 (THE)
    res_crit = client.get("/criteria?system_id=1")
    assert res_crit.status_code == 200
    criteria = res_crit.json()
    assert len(criteria) == 6
    crit_names = [c["criteria_name"] for c in criteria]
    assert "Teaching" in crit_names
    assert "Citations" in crit_names

def test_analytics_compare_endpoint(client):
    res = client.get("/analytics/compare?university_ids=1,2&system_id=1&start_year=2014&end_year=2015")
    assert res.status_code == 200
    data = res.json()
    assert data["system_id"] == 1
    assert len(data["universities"]) == 2
    # Verify scale isolation
    harvard = next(u for u in data["universities"] if u["university_id"] == 1)
    crit_names = {s["criteria_name"] for s in harvard["scores"]}
    assert "Teaching" in crit_names
    assert "Alumni" not in crit_names

def test_analytics_trends_endpoint(client):
    res = client.get("/analytics/trends?university_ids=1&criteria_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["criteria_id"] == 1
    assert len(data["trends"]) == 1
    pts = data["trends"][0]["data_points"]
    assert len(pts) == 6

def test_analytics_country_comparison_endpoint(client):
    res = client.get("/analytics/country-comparison?criteria_id=1&year=2015&min_universities=3")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert "mean_score" in data[0]

def test_analytics_criteria_endpoint(client):
    res = client.get("/analytics/criteria?system_id=1")
    assert res.status_code == 200
    data = res.json()
    assert len(data["distributions"]) == 6
    assert len(data["correlations"]) > 0

def test_analytics_demographics_endpoint(client):
    res = client.get("/analytics/demographics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_observations"] == 1085
    assert len(data["distributions"]) == 4
    assert len(data["correlations"]) == 4

def test_analytics_post_analyze_endpoint(client):
    payload = {
        "analysis_type": "compare",
        "university_ids": [1, 2],
        "system_id": 1
    }
    res = client.post("/analytics/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["system_id"] == 1
    assert len(data["universities"]) == 2

def test_conversations_endpoint(client):
    res = client.get("/conversations")
    assert res.status_code == 200
    threads = res.json()
    assert len(threads) >= 1
    assert threads[0]["thread_id"] == "default-thread"

    res_detail = client.get("/conversations/default-thread")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["thread_id"] == "default-thread"
    assert len(detail["messages"]) >= 1
