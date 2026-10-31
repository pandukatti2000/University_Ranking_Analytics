import pytest
from app.database.session import SessionLocal
from app.services.overview_service import OverviewService
from app.services.comparison_service import ComparisonService
from app.services.country_service import CountryService
from app.services.trends_service import TrendsService
from app.services.criteria_service import CriteriaService
from app.services.demographics_service import DemographicsService

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_overview_service_kpis(db):
    """Test overview service returns authoritative counts and coverage metrics."""
    kpis = OverviewService.get_overview_kpis(db)
    assert kpis.total_universities == 1247
    assert kpis.total_countries == 74
    assert kpis.total_ranking_systems == 3
    assert kpis.total_ranking_records == 29612
    assert kpis.total_demographic_records == 1085
    assert kpis.min_year == 2005
    assert kpis.max_year == 2016

    # Verify ranking system coverage counts
    sys_map = {s.system_id: s for s in kpis.ranking_systems}
    assert sys_map[1].total_institutions == 245
    assert sys_map[1].min_year == 2011 and sys_map[1].max_year == 2016
    assert sys_map[2].total_institutions == 93
    assert sys_map[2].min_year == 2005 and sys_map[2].max_year == 2015
    assert sys_map[3].total_institutions == 1024
    assert sys_map[3].min_year == 2012 and sys_map[3].max_year == 2015

    # Top country
    assert kpis.top_countries[0].country_name == "United States of America"
    assert kpis.top_countries[0].university_count == 273

    # Universities in all 3 systems
    assert kpis.universities_in_all_systems == 75

def test_multi_system_universities(db):
    """Verify universities appearing in multiple ranking systems."""
    multi_3 = OverviewService.get_multi_system_universities(db, min_systems=3)
    assert len(multi_3) == 75
    names_3 = [u.university_name for u in multi_3]
    assert "Harvard University" in names_3
    assert "Stanford University" in names_3
    assert "California Institute of Technology" in names_3
    assert "University of Cambridge" in names_3
    assert "University of Oxford" in names_3

    # MIT appears in 2 systems (THE and CWUR)
    multi_2 = OverviewService.get_multi_system_universities(db, min_systems=2)
    names_2 = [u.university_name for u in multi_2]
    assert "Massachusetts Institute of Technology" in names_2

def test_comparison_service_scale_isolation(db):
    """Verify comparison service enforces system isolation and returns proper metrics."""
    # Compare Harvard (1) and MIT (2) in THE (System 1)
    res_the = ComparisonService.compare_universities(
        db, university_ids=[1, 2], system_id=1, start_year=2014, end_year=2015
    )
    assert res_the.system_id == 1
    assert len(res_the.universities) == 2

    # Check that Harvard has Teaching, Citations, etc.
    harvard = next(u for u in res_the.universities if u.university_id == 1)
    crit_names = {s.criteria_name for s in harvard.scores}
    assert "Teaching" in crit_names
    assert "Citations" in crit_names
    assert "Alumni" not in crit_names  # Shanghai criterion must NOT appear in THE!

    # Check demographics present for Harvard
    assert len(harvard.demographics) >= 2
    assert harvard.demographics[0].num_students > 0

    # Compare in Shanghai (System 2)
    res_shanghai = ComparisonService.compare_universities(
        db, university_ids=[1, 2], system_id=2, start_year=2014, end_year=2015
    )
    assert res_shanghai.system_id == 2
    harvard_shanghai = next(u for u in res_shanghai.universities if u.university_id == 1)
    shanghai_crits = {s.criteria_name for s in harvard_shanghai.scores}
    assert "Alumni" in shanghai_crits
    assert "Teaching" not in shanghai_crits

def test_country_service(db):
    """Verify country details and country criteria comparisons."""
    # USA ID is 73
    usa_detail = CountryService.get_country_detail(db, country_id=73)
    assert usa_detail.country_name == "United States of America"
    assert usa_detail.total_universities == 273
    assert len(usa_detail.system_representation) == 3

    # Compare countries by Teaching score in 2015
    country_comp = CountryService.compare_countries_by_criteria(
        db, criteria_id=1, year=2015, min_universities=3
    )
    assert len(country_comp) > 0
    top_country = country_comp[0]
    assert "mean_score" in top_country
    assert top_country["mean_score"] > 0

def test_trends_service_and_movers(db):
    """Verify longitudinal trends and dynamic rank positioning."""
    # Harvard (ID 1) on Criterion 1 (Teaching)
    trends = TrendsService.get_university_trends(db, university_ids=[1], criteria_id=1)
    assert trends.criteria_id == 1
    assert len(trends.trends) == 1
    h_series = trends.trends[0]
    assert len(h_series.data_points) == 6  # 2011 to 2016

    # Harvard is world top 10 in Teaching in THE
    for pt in h_series.data_points:
        assert pt.rank_in_system is not None
        assert pt.rank_in_system <= 10

    # Check top movers
    assert len(trends.strongest_improvements) > 0
    assert len(trends.strongest_declines) > 0

def test_criteria_service_correlations_and_safety(db):
    """Verify pairwise correlations, non-causal phrasing, and cross-system blocking."""
    # Correlation between Teaching (1) and Research (3) in THE
    corr = CriteriaService.get_criteria_correlation(db, crit_1_id=1, crit_2_id=3)
    assert corr.system_id == 1
    assert corr.pearson_r > 0.8  # Strong positive correlation
    assert "not causal" in corr.interpretation.lower() or "not imply" in corr.interpretation.lower() or "not" in corr.interpretation.lower()

    # Attempt cross-system correlation: Teaching (1) in THE vs. Alumni (7) in Shanghai
    with pytest.raises(ValueError) as exc:
        CriteriaService.get_criteria_correlation(db, crit_1_id=1, crit_2_id=7)
    assert "distinct ranking systems" in str(exc.value)

    # Test distribution stats
    dists = CriteriaService.get_criteria_distributions(db, system_id=1)
    assert len(dists) == 6
    for d in dists:
        assert d.min <= d.median <= d.max
        assert d.std_dev >= 0

def test_demographics_service(db):
    """Verify demographic distributions and associations with ranking indicators."""
    demo = DemographicsService.get_demographics_overview(db)
    assert demo.total_observations == 1085
    assert demo.unique_universities == 245
    assert len(demo.distributions) == 4

    # Check correlation between International % and THE International Outlook (Criterion 2)
    intl_corr = next(c for c in demo.correlations if c.criteria_id == 2)
    assert intl_corr.pearson_r >= 0.75  # Verified earlier at 0.786
    assert "does not establish a causal relationship" in intl_corr.interpretation

    # Check correlation between Student-Staff ratio and Teaching (Criterion 1)
    ratio_corr = next(c for c in demo.correlations if c.criteria_id == 1)
    assert ratio_corr.pearson_r < 0  # Inverse relationship (-0.311)
