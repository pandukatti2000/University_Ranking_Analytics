from typing import List, Optional, Dict, Any
import statistics
import math
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, and_
from app.database.models import UniversityYear, UniversityRankingYear, RankingCriteria
from app.models.schemas import (
    DemographicsResponse,
    DemographicDistribution,
    DemographicCorrelation
)

class DemographicsService:

    @staticmethod
    def calculate_pearson_r(x_vals: List[float], y_vals: List[float]) -> float:
        n = len(x_vals)
        if n < 3:
            return 0.0
        mx = statistics.mean(x_vals)
        my = statistics.mean(y_vals)
        num = sum((x - mx) * (y - my) for x, y in zip(x_vals, y_vals))
        den = math.sqrt(sum((x - mx)**2 for x in x_vals) * sum((y - my)**2 for y in y_vals))
        return round(num / den, 3) if den != 0 else 0.0

    @staticmethod
    def interpret_demographic_correlation(r: float, demo_name: str, crit_name: str) -> str:
        abs_r = abs(r)
        strength = "negligible"
        if abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.4:
            strength = "moderate"
        elif abs_r >= 0.2:
            strength = "weak"

        direction = "positive" if r > 0 else ("negative" if r < 0 else "neutral")
        return (
            f"{strength.capitalize()} {direction} association (r={r}). "
            f"Observed statistical correlation does not establish a causal relationship between {demo_name} and {crit_name}."
        )

    @staticmethod
    def get_demographics_overview(db: Session) -> DemographicsResponse:
        total_obs = db.query(func.count(UniversityYear.university_id)).scalar() or 0
        unique_unis = db.query(func.count(distinct(UniversityYear.university_id))).scalar() or 0
        years = db.query(distinct(UniversityYear.year)).order_by(UniversityYear.year).all()
        years_covered = [y[0] for y in years]

        # Metric distributions
        distributions = []
        metrics_meta = [
            ("num_students", "Total Enrolled Students", "headcount", False),
            ("student_staff_ratio", "Student to Staff Ratio", "ratio", True),
            ("pct_international_students", "International Students Percentage", "%", True),
            ("pct_female_students", "Female Students Percentage", "%", True),
        ]

        all_records = db.query(UniversityYear).all()

        for attr, label, unit, is_float in metrics_meta:
            raw_vals = [getattr(r, attr) for r in all_records if getattr(r, attr) is not None]
            vals = [float(v) for v in raw_vals]
            if not vals:
                continue
            sorted_vals = sorted(vals)
            cnt = len(sorted_vals)
            distributions.append(DemographicDistribution(
                metric_name=label,
                count=cnt,
                mean=round(statistics.mean(sorted_vals), 2),
                min=round(sorted_vals[0], 2),
                median=round(statistics.median(sorted_vals), 2),
                max=round(sorted_vals[-1], 2),
                unit=unit
            ))

        # Demographic to ranking criteria associations
        correlations = []
        pairs_to_evaluate = [
            ("pct_international_students", 2, "International Students %", "THE International Outlook"),
            ("student_staff_ratio", 1, "Student-to-Staff Ratio", "THE Teaching Score"),
            ("pct_female_students", 6, "Female Students %", "THE Total Composite Score"),
            ("num_students", 3, "Total Students Count", "THE Research Score"),
        ]

        for demo_attr, crit_id, demo_label, crit_label in pairs_to_evaluate:
            rows = db.query(
                getattr(UniversityYear, demo_attr),
                UniversityRankingYear.score
            ).join(
                UniversityRankingYear,
                and_(
                    UniversityYear.university_id == UniversityRankingYear.university_id,
                    UniversityYear.year == UniversityRankingYear.year
                )
            ).filter(
                and_(
                    UniversityRankingYear.ranking_criteria_id == crit_id,
                    getattr(UniversityYear, demo_attr).isnot(None),
                    UniversityRankingYear.score.isnot(None)
                )
            ).all()

            x_vals = [float(r[0]) for r in rows]
            y_vals = [float(r[1]) for r in rows]

            r_val = DemographicsService.calculate_pearson_r(x_vals, y_vals)
            interp = DemographicsService.interpret_demographic_correlation(r_val, demo_label, crit_label)

            correlations.append(DemographicCorrelation(
                demographic_field=demo_label,
                criteria_id=crit_id,
                criteria_name=crit_label,
                sample_size=len(rows),
                pearson_r=r_val,
                interpretation=interp
            ))

        methodology_note = (
            "Demographics are recorded exclusively for institutions evaluated in the Times Higher Education "
            "World University Rankings (2011–2016). 1,002 institutions in the broader registry have no demographic data. "
            "Correlation coefficients indicate empirical association and must not be construed as causal mechanisms."
        )

        return DemographicsResponse(
            total_observations=total_obs,
            unique_universities=unique_unis,
            years_covered=years_covered,
            distributions=distributions,
            correlations=correlations,
            methodology_note=methodology_note
        )
