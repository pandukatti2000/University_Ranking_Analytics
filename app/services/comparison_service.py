from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database.models import RankingSystem, RankingCriteria, University, UniversityRankingYear, UniversityYear
from app.models.schemas import (
    UniversityComparisonResponse,
    UniversityComparisonItem,
    CriterionScorePoint,
    UniversityDemographicPoint
)

class ComparisonService:

    @staticmethod
    def compare_universities(
        db: Session,
        university_ids: List[int],
        system_id: int,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> UniversityComparisonResponse:
        """
        Compare multiple universities within a specific ranking system.
        Enforces system isolation to prevent combining incompatible scales.
        """
        system = db.query(RankingSystem).filter(RankingSystem.id == system_id).first()
        if not system:
            raise ValueError(f"Ranking system with id {system_id} does not exist.")

        criteria_list = db.query(RankingCriteria).filter(
            RankingCriteria.ranking_system_id == system_id
        ).order_by(RankingCriteria.id).all()
        criteria_ids = [c.id for c in criteria_list]
        criteria_map = {c.id: c for c in criteria_list}

        warnings = []
        comparison_items = []

        for uid in university_ids:
            uni = db.query(University).filter(University.id == uid).first()
            if not uni:
                warnings.append(f"University with ID {uid} was not found.")
                continue

            # Query ranking scores for this university within this system
            score_query = db.query(UniversityRankingYear).filter(
                and_(
                    UniversityRankingYear.university_id == uid,
                    UniversityRankingYear.ranking_criteria_id.in_(criteria_ids)
                )
            )
            if start_year:
                score_query = score_query.filter(UniversityRankingYear.year >= start_year)
            if end_year:
                score_query = score_query.filter(UniversityRankingYear.year <= end_year)

            scores_rows = score_query.order_by(
                UniversityRankingYear.year,
                UniversityRankingYear.ranking_criteria_id
            ).all()

            if not scores_rows:
                warnings.append(f"'{uni.university_name}' has no recorded metrics in {system.system_name}.")

            score_points = [
                CriterionScorePoint(
                    criteria_id=s.ranking_criteria_id,
                    criteria_name=criteria_map[s.ranking_criteria_id].criteria_name,
                    metric_type=criteria_map[s.ranking_criteria_id].metric_type,
                    year=s.year,
                    value=float(s.score) if s.score is not None else None
                )
                for s in scores_rows
            ]

            # Query demographics
            demo_query = db.query(UniversityYear).filter(UniversityYear.university_id == uid)
            if start_year:
                demo_query = demo_query.filter(UniversityYear.year >= start_year)
            if end_year:
                demo_query = demo_query.filter(UniversityYear.year <= end_year)

            demo_rows = demo_query.order_by(UniversityYear.year).all()

            demo_points = [
                UniversityDemographicPoint(
                    year=d.year,
                    num_students=d.num_students,
                    student_staff_ratio=float(d.student_staff_ratio) if d.student_staff_ratio is not None else None,
                    pct_international_students=d.pct_international_students,
                    pct_female_students=float(d.pct_female_students) if d.pct_female_students is not None else None
                )
                for d in demo_rows
            ]

            if not demo_points and system_id != 1:
                warnings.append(f"Demographic data for '{uni.university_name}' is not recorded under {system.system_name} (demographics are collected via Times Higher Education).")

            comparison_items.append(UniversityComparisonItem(
                university_id=uni.id,
                university_name=uni.university_name,
                country_name=uni.country.country_name,
                scores=score_points,
                demographics=demo_points
            ))

        return UniversityComparisonResponse(
            system_id=system.id,
            system_name=system.system_name,
            universities=comparison_items,
            warnings=list(set(warnings))
        )
