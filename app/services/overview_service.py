from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc
from app.database.models import Country, RankingSystem, RankingCriteria, University, UniversityRankingYear, UniversityYear
from app.models.schemas import OverviewKPIs, SystemCoverage, CountryCount, MultiSystemUniversity

class OverviewService:

    @staticmethod
    def get_overview_kpis(db: Session) -> OverviewKPIs:
        total_unis = db.query(func.count(University.id)).scalar() or 0
        total_countries = db.query(func.count(Country.id)).scalar() or 0
        total_systems = db.query(func.count(RankingSystem.id)).scalar() or 0
        total_rankings = db.query(func.count(UniversityRankingYear.university_id)).scalar() or 0
        total_demographics = db.query(func.count(UniversityYear.university_id)).scalar() or 0

        # Overall year range
        min_year = db.query(func.min(UniversityRankingYear.year)).scalar() or 2005
        max_year = db.query(func.max(UniversityRankingYear.year)).scalar() or 2016

        # Systems coverage
        systems_coverage = []
        systems = db.query(RankingSystem).order_by(RankingSystem.id).all()
        for sys in systems:
            crit_ids = [c.id for c in sys.criteria]
            stat = db.query(
                func.min(UniversityRankingYear.year),
                func.max(UniversityRankingYear.year),
                func.count(distinct(UniversityRankingYear.university_id))
            ).filter(UniversityRankingYear.ranking_criteria_id.in_(crit_ids)).first()

            s_min, s_max, s_unis = stat if stat else (0, 0, 0)
            systems_coverage.append(SystemCoverage(
                system_id=sys.id,
                system_name=sys.system_name,
                min_year=s_min or 0,
                max_year=s_max or 0,
                total_institutions=s_unis or 0,
                total_criteria=len(crit_ids)
            ))

        # Top 10 Countries by university count
        top_countries_raw = db.query(
            Country.id,
            Country.country_name,
            func.count(University.id).label("cnt")
        ).join(University, Country.id == University.country_id)\
         .group_by(Country.id, Country.country_name)\
         .order_by(desc("cnt"))\
         .limit(10).all()

        top_countries = [
            CountryCount(country_id=cid, country_name=cname, university_count=cnt)
            for cid, cname, cnt in top_countries_raw
        ]

        # Overlapping universities
        multi_sys = OverviewService.get_multi_system_universities(db, min_systems=2)
        all_3_cnt = sum(1 for u in multi_sys if u.system_count == 3)
        multi_cnt = len(multi_sys)

        return OverviewKPIs(
            total_universities=total_unis,
            total_countries=total_countries,
            total_ranking_systems=total_systems,
            total_ranking_records=total_rankings,
            total_demographic_records=total_demographics,
            min_year=min_year,
            max_year=max_year,
            ranking_systems=systems_coverage,
            top_countries=top_countries,
            universities_in_all_systems=all_3_cnt,
            universities_in_multiple_systems=multi_cnt
        )

    @staticmethod
    def get_multi_system_universities(db: Session, min_systems: int = 2) -> List[MultiSystemUniversity]:
        """Find universities that appear in multiple ranking systems."""
        # Query distinct (university_id, ranking_system_id)
        subq = db.query(
            UniversityRankingYear.university_id,
            RankingCriteria.ranking_system_id,
            RankingSystem.system_name
        ).join(RankingCriteria, UniversityRankingYear.ranking_criteria_id == RankingCriteria.id)\
         .join(RankingSystem, RankingCriteria.ranking_system_id == RankingSystem.id)\
         .distinct().subquery()

        # Group by university_id
        res = db.query(
            subq.c.university_id,
            University.university_name,
            Country.country_name,
            func.count(subq.c.ranking_system_id).label("sys_cnt"),
            func.array_agg(subq.c.system_name).label("systems")
        ).join(University, subq.c.university_id == University.id)\
         .join(Country, University.country_id == Country.id)\
         .group_by(subq.c.university_id, University.university_name, Country.country_name)\
         .having(func.count(subq.c.ranking_system_id) >= min_systems)\
         .order_by(desc("sys_cnt"), University.university_name).all()

        results = []
        for uid, uname, cname, scnt, slist in res:
            results.append(MultiSystemUniversity(
                university_id=uid,
                university_name=uname,
                country_name=cname,
                system_count=scnt,
                systems=sorted(list(set(slist)))
            ))
        return results

    @staticmethod
    def list_countries(db: Session) -> List[Dict[str, Any]]:
        countries = db.query(Country).order_by(Country.country_name).all()
        return [{"id": c.id, "country_name": c.country_name} for c in countries]

    @staticmethod
    def list_universities(
        db: Session,
        country_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = db.query(University).join(Country, University.country_id == Country.id)
        if country_id:
            query = query.filter(University.country_id == country_id)
        if search:
            query = query.filter(University.university_name.ilike(f"%{search}%"))

        total = query.count()
        rows = query.order_by(University.university_name).offset(offset).limit(limit).all()

        return [
            {
                "id": u.id,
                "university_name": u.university_name,
                "country_id": u.country_id,
                "country_name": u.country.country_name
            }
            for u in rows
        ]

    @staticmethod
    def list_ranking_systems(db: Session) -> List[Dict[str, Any]]:
        systems = db.query(RankingSystem).order_by(RankingSystem.id).all()
        return [{"id": s.id, "system_name": s.system_name} for s in systems]

    @staticmethod
    def list_criteria(db: Session, system_id: Optional[int] = None) -> List[Dict[str, Any]]:
        query = db.query(RankingCriteria).join(RankingSystem, RankingCriteria.ranking_system_id == RankingSystem.id)
        if system_id:
            query = query.filter(RankingCriteria.ranking_system_id == system_id)

        rows = query.order_by(RankingCriteria.id).all()
        return [
            {
                "id": rc.id,
                "ranking_system_id": rc.ranking_system_id,
                "system_name": rc.ranking_system.system_name,
                "criteria_name": rc.criteria_name,
                "is_rank": rc.is_rank,
                "metric_type": rc.metric_type
            }
            for rc in rows
        ]
