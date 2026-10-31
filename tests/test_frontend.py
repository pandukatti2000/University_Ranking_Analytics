import sys
import os

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

import pytest
import pandas as pd
from frontend.components.charts import (
    create_radar_chart,
    create_trend_line_chart,
    create_bar_chart,
    create_scatter_plot,
    create_box_plot,
    create_treemap,
    create_choropleth_map
)
from frontend.components.api_client import (
    get_overview_data,
    get_universities_list,
    get_countries_list,
    get_ranking_systems_and_criteria,
    get_comparison_data,
    get_historical_trends,
    get_country_analytics,
    get_criteria_analytics,
    get_demographics_analytics
)

def test_api_client_fallbacks():
    """Verify that frontend API client loads data from services cleanly."""
    overview = get_overview_data()
    assert "total_universities" in overview
    assert overview["total_universities"] > 1000
    
    unis = get_universities_list(limit=10)
    assert len(unis) == 10
    assert "university_name" in unis[0]
    
    countries = get_countries_list()
    assert len(countries) > 50
    
    systems = get_ranking_systems_and_criteria()
    assert len(systems) == 3
    
    comp = get_comparison_data(university_ids=[1, 2], system_id=1)
    assert "universities" in comp
    
    trends = get_historical_trends(university_ids=[1, 2], ranking_criteria_id=1)
    assert "trends" in trends
    
    country_data = get_country_analytics()
    assert len(country_data) > 50
    
    criteria_data = get_criteria_analytics(ranking_system_id=1)
    assert len(criteria_data) > 0
    
    demo_data = get_demographics_analytics()
    assert "total_observations" in demo_data

def test_chart_generators():
    """Verify all chart generators construct valid Plotly figures without error."""
    df_sample = pd.DataFrame([
        {"category": "Teaching", "score": 85.0, "group": "Uni A", "year": 2014, "country": "USA", "count": 10},
        {"category": "Research", "score": 90.0, "group": "Uni A", "year": 2015, "country": "USA", "count": 15},
        {"category": "Teaching", "score": 75.0, "group": "Uni B", "year": 2014, "country": "UK", "count": 8},
        {"category": "Research", "score": 80.0, "group": "Uni B", "year": 2015, "country": "UK", "count": 12},
    ])
    
    # Radar chart
    fig_radar = create_radar_chart(df_sample, "category", "score", "group", "Radar Test")
    assert fig_radar is not None
    
    # Line chart
    fig_line = create_trend_line_chart(df_sample, "year", "score", "group", "Line Test")
    assert fig_line is not None
    
    # Inverted Line chart (for ranks)
    fig_line_inv = create_trend_line_chart(df_sample, "year", "score", "group", "Rank Test", inverted_y=True)
    assert fig_line_inv is not None
    
    # Bar chart
    fig_bar = create_bar_chart(df_sample, "category", "score", "group", "Bar Test")
    assert fig_bar is not None
    
    # Scatter plot with trendline
    fig_scatter = create_scatter_plot(df_sample, "score", "count", "country", title="Scatter Test", trendline="ols")
    assert fig_scatter is not None
    
    # Box plot
    fig_box = create_box_plot(df_sample, "category", "score", "group", "Box Test")
    assert fig_box is not None
    
    # Treemap
    fig_tree = create_treemap(df_sample, ["country", "group"], "count", "Tree Test")
    assert fig_tree is not None
    
    # Choropleth
    fig_choro = create_choropleth_map(df_sample, "country", "count", "Choropleth Test")
    assert fig_choro is not None

def test_view_imports():
    """Verify all view modules import correctly without module/syntax issues."""
    from frontend.views.overview import render_overview
    from frontend.views.comparison import render_comparison
    from frontend.views.country_analysis import render_country_analysis
    from frontend.views.trends import render_trends
    from frontend.views.criteria_analysis import render_criteria_analysis
    from frontend.views.demographics import render_demographics
    from frontend.views.ai_copilot import render_ai_copilot
    
    assert callable(render_overview)
    assert callable(render_comparison)
    assert callable(render_country_analysis)
    assert callable(render_trends)
    assert callable(render_criteria_analysis)
    assert callable(render_demographics)
    assert callable(render_ai_copilot)
