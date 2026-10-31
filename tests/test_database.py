import pytest
from sqlalchemy import text
from app.database.session import SessionLocal, ReadonlySessionLocal
from app.database.models import Country, RankingSystem, RankingCriteria, University, UniversityRankingYear, UniversityYear

def test_database_connection():
    """Verify primary database connection and simple query execution."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1;")).scalar()
        assert result == 1
    finally:
        db.close()

def test_readonly_database_connection():
    """Verify read-only role can connect and execute SELECT queries."""
    db = ReadonlySessionLocal()
    try:
        result = db.execute(text("SELECT 1;")).scalar()
        assert result == 1
    finally:
        db.close()

def test_readonly_security_enforcement():
    """Verify read-only role is strictly forbidden from executing DML/DDL."""
    db = ReadonlySessionLocal()
    try:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("INSERT INTO country (id, country_name) VALUES (9999, 'TestCountry');"))
            db.commit()
        # Verify permission denied error
        assert "permission denied" in str(exc_info.value).lower()
    finally:
        db.rollback()
        db.close()

def test_table_row_counts_reconciliation():
    """Reconcile all table row counts against authoritative CSV metrics."""
    db = SessionLocal()
    try:
        assert db.query(Country).count() == 74
        assert db.query(RankingSystem).count() == 3
        assert db.query(RankingCriteria).count() == 21
        assert db.query(University).count() == 1247
        assert db.query(UniversityRankingYear).count() == 29612
        assert db.query(UniversityYear).count() == 1085
    finally:
        db.close()

def test_null_value_distribution():
    """Verify domain-specific NULL values are precisely located."""
    db = SessionLocal()
    try:
        # Check that NULL scores are exclusively in Criterion 5 (Income)
        null_scores = db.query(UniversityRankingYear).filter(UniversityRankingYear.score.is_(None)).all()
        assert len(null_scores) == 130
        for record in null_scores:
            assert record.ranking_criteria_id == 5

        # Check that NULL female percentages are exactly 96
        null_female = db.query(UniversityYear).filter(UniversityYear.pct_female_students.is_(None)).count()
        assert null_female == 96
    finally:
        db.close()

def test_foreign_key_relationships():
    """Verify ORM relationships and referential integrity."""
    db = SessionLocal()
    try:
        # Harvard University (ID: 1, Country: USA)
        harvard = db.query(University).filter(University.id == 1).first()
        assert harvard is not None
        assert harvard.university_name == "Harvard University"
        assert harvard.country.country_name == "United States of America"

        # Criteria check (Teaching belongs to THE)
        teaching = db.query(RankingCriteria).filter(RankingCriteria.id == 1).first()
        assert teaching is not None
        assert teaching.criteria_name == "Teaching"
        assert teaching.ranking_system.system_name == "Times Higher Education World University Ranking"
        assert teaching.metric_type == "score"

        # CWUR Rank criteria check (ID 14 is a rank)
        quality_of_edu = db.query(RankingCriteria).filter(RankingCriteria.id == 14).first()
        assert quality_of_edu.metric_type == "rank"
        assert quality_of_edu.is_rank is True
    finally:
        db.close()

def test_database_views():
    """Verify that helper views for analytics and GenAI operate properly."""
    db = SessionLocal()
    try:
        res1 = db.execute(text("SELECT COUNT(*) FROM v_university_overview;")).scalar()
        assert res1 == 1247

        res2 = db.execute(text("SELECT COUNT(*) FROM v_criteria_overview;")).scalar()
        assert res2 == 21

        res3 = db.execute(text("SELECT COUNT(*) FROM v_ranked_universities;")).scalar()
        assert res3 == 29612
    finally:
        db.close()
