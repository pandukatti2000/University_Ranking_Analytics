from typing import List, Optional, Dict, Any
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc, and_
from app.database.models import Country, RankingSystem, RankingCriteria, University, UniversityRankingYear
from app.models.schemas import CountryDetailResponse, CountryRepresentation, CountryScoreMetric, CountryCount

class CountryService:

    @staticmethod
    def get_country_university_distribution(db: Session) -> List[CountryCount]:
        rows = db.query(
            Country.id,
            Country.country_name,
            func.count(University.id).label("cnt")
        ).join(University, Country.id == University.country_id)\
         .group_by(Country.id, Country.country_name)\
         .order_by(desc("cnt"), Country.country_name).all()

        return [
            CountryCount(country_id=cid, country_name=cname, university_count=cnt)
            for cid, cname, cnt in rows
        ]

    @staticmethod
    def get_country_detail(db: Session, country_id: int) -> CountryDetailResponse:
        country = db.query(Country).filter(Country.id == country_id).first()
        if not country:
            raise ValueError(f"Country with ID {country_id} does not exist.")

        total_unis = db.query(func.count(University.id)).filter(University.country_id == country_id).scalar() or 0

        # System representation
        sys_rep = []
        systems = db.query(RankingSystem).order_by(RankingSystem.id).all()
        for s in systems:
            crit_ids = [c.id for c in s.criteria]
            count = db.query(func.count(distinct(UniversityRankingYear.university_id)))\
                      .join(University, UniversityRankingYear.university_id == University.id)\
                      .filter(
                          and_(
                              University.country_id == country_id,
                              UniversityRankingYear.ranking_criteria_id.in_(crit_ids)
                          )
                      ).scalar() or 0
            sys_rep.append(CountryRepresentation(
                system_id=s.id,
                system_name=s.system_name,
                university_count=count
            ))

        # Score metrics for composite criteria (Criteria 6: Total Times, Criteria 13: Total Shanghai, Criteria 21: Total CWUR)
        composite_crit_ids = [6, 13, 21]
        score_rows = db.query(
            UniversityRankingYear.ranking_criteria_id,
            RankingCriteria.criteria_name,
            UniversityRankingYear.year,
            UniversityRankingYear.score
        ).join(University, UniversityRankingYear.university_id == University.id)\
         .join(RankingCriteria, UniversityRankingYear.ranking_criteria_id == RankingCriteria.id)\
         .filter(
             and_(
                 University.country_id == country_id,
                 UniversityRankingYear.ranking_criteria_id.in_(composite_crit_ids),
                 UniversityRankingYear.score.isnot(None)
             )
         ).order_by(UniversityRankingYear.ranking_criteria_id, UniversityRankingYear.year).all()

        from collections import defaultdict
        grouped = defaultdict(list)
        crit_names = {}
        for cid, cname, yr, sc in score_rows:
            grouped[(cid, yr)].append(float(sc))
            crit_names[cid] = cname

        score_metrics = []
        for (cid, yr), vals in sorted(grouped.items()):
            if vals:
                score_metrics.append(CountryScoreMetric(
                    criteria_id=cid,
                    criteria_name=crit_names[cid],
                    metric_type="score",
                    year=yr,
                    count=len(vals),
                    mean=round(statistics.mean(vals), 2),
                    min=round(min(vals), 2),
                    max=round(max(vals), 2),
                    median=round(statistics.median(vals), 2)
                ))

        return CountryDetailResponse(
            country_id=country.id,
            country_name=country.country_name,
            total_universities=total_unis,
            system_representation=sys_rep,
            score_metrics=score_metrics
        )

    @staticmethod
    def compare_countries_by_criteria(
        db: Session,
        criteria_id: int,
        year: int,
        min_universities: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Compare countries by an explicit criterion and year.
        Excludes countries with fewer than `min_universities` to ensure statistical relevance.
        """
        criterion = db.query(RankingCriteria).filter(RankingCriteria.id == criteria_id).first()
        if not criterion:
            raise ValueError(f"Criteria with ID {criteria_id} does not exist.")

        rows = db.query(
            Country.id,
            Country.country_name,
            func.count(UniversityRankingYear.university_id).label("uni_count"),
            func.avg(UniversityRankingYear.score).label("avg_score"),
            func.min(UniversityRankingYear.score).label("min_score"),
            func.max(UniversityRankingYear.score).label("max_score")
        ).join(University, Country.id == University.country_id)\
         .join(UniversityRankingYear, University.id == UniversityRankingYear.university_id)\
         .filter(
             and_(
                 UniversityRankingYear.ranking_criteria_id == criteria_id,
                 UniversityRankingYear.year == year,
                 UniversityRankingYear.score.isnot(None)
             )
         )\
         .group_by(Country.id, Country.country_name)\
         .having(func.count(UniversityRankingYear.university_id) >= min_universities)\
         .order_by(asc("avg_score") if criterion.is_rank else desc("avg_score")).all()

        from sqlalchemy import asc
        return [
            {
                "country_id": cid,
                "country_name": cname,
                "year": year,
                "criteria_name": criterion.criteria_name,
                "metric_type": criterion.metric_type,
                "university_count": count,
                "mean_score": round(float(avg_sc), 2),
                "min_score": round(float(min_sc), 2),
                "max_score": round(float(max_sc), 2)
            }
            for cid, cname, count, avg_sc, min_sc, max_sc in rows
        ]
