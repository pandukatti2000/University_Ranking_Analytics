from typing import List, Optional, Tuple
import math
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database.models import RankingCriteria, RankingSystem, UniversityRankingYear
from app.models.schemas import CriteriaDistribution, CriteriaCorrelation, CriteriaAnalysisResponse

class CriteriaService:

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
    def interpret_correlation(r: float, name_1: str, name_2: str) -> str:
        abs_r = abs(r)
        strength = "negligible"
        if abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.4:
            strength = "moderate"
        elif abs_r >= 0.2:
            strength = "weak"

        direction = "positive" if r > 0 else ("negative" if r < 0 else "neutral")
        return f"{strength.capitalize()} {direction} correlation (r={r}). Note: Association indicates co-variation, not causal impact."

    @staticmethod
    def get_criteria_distributions(db: Session, system_id: Optional[int] = None) -> List[CriteriaDistribution]:
        query = db.query(RankingCriteria).join(RankingSystem, RankingCriteria.ranking_system_id == RankingSystem.id)
        if system_id:
            query = query.filter(RankingCriteria.ranking_system_id == system_id)

        criteria_list = query.order_by(RankingCriteria.id).all()
        distributions = []

        for crit in criteria_list:
            scores = db.query(UniversityRankingYear.score).filter(
                and_(
                    UniversityRankingYear.ranking_criteria_id == crit.id,
                    UniversityRankingYear.score.isnot(None)
                )
            ).all()

            vals = [float(s[0]) for s in scores]
            if not vals:
                continue

            sorted_vals = sorted(vals)
            cnt = len(sorted_vals)
            mean_v = statistics.mean(sorted_vals)
            std_v = statistics.stdev(sorted_vals) if cnt > 1 else 0.0
            min_v = sorted_vals[0]
            max_v = sorted_vals[-1]
            med_v = statistics.median(sorted_vals)
            
            # Percentiles
            q25_idx = int(0.25 * cnt)
            q75_idx = int(0.75 * cnt)
            q25_v = sorted_vals[q25_idx]
            q75_v = sorted_vals[q75_idx]

            distributions.append(CriteriaDistribution(
                criteria_id=crit.id,
                criteria_name=crit.criteria_name,
                system_id=crit.ranking_system_id,
                system_name=crit.ranking_system.system_name,
                metric_type=crit.metric_type,
                count=cnt,
                mean=round(mean_v, 2),
                std_dev=round(std_v, 2),
                min=round(min_v, 2),
                q25=round(q25_v, 2),
                median=round(med_v, 2),
                q75=round(q75_v, 2),
                max=round(max_v, 2)
            ))

        return distributions

    @staticmethod
    def get_criteria_correlation(
        db: Session,
        crit_1_id: int,
        crit_2_id: int,
        year: Optional[int] = None
    ) -> CriteriaCorrelation:
        c1 = db.query(RankingCriteria).filter(RankingCriteria.id == crit_1_id).first()
        c2 = db.query(RankingCriteria).filter(RankingCriteria.id == crit_2_id).first()

        if not c1 or not c2:
            raise ValueError("One or both criteria do not exist.")

        if c1.ranking_system_id != c2.ranking_system_id:
            raise ValueError(
                f"Criteria belong to distinct ranking systems ('{c1.ranking_system.system_name}' vs '{c2.ranking_system.system_name}'). "
                "Cross-system criteria correlation is prohibited due to disparate normalization methodologies."
            )

        # Query pairs joined on (university_id, year)
        # Aliasing fact table for criterion 1 and 2
        from sqlalchemy.orm import aliased
        ury1 = aliased(UniversityRankingYear)
        ury2 = aliased(UniversityRankingYear)

        query = db.query(ury1.score, ury2.score).join(
            ury2,
            and_(
                ury1.university_id == ury2.university_id,
                ury1.year == ury2.year
            )
        ).filter(
            and_(
                ury1.ranking_criteria_id == crit_1_id,
                ury2.ranking_criteria_id == crit_2_id,
                ury1.score.isnot(None),
                ury2.score.isnot(None)
            )
        )

        if year:
            query = query.filter(ury1.year == year)

        pairs = query.all()
        x_vals = [float(p[0]) for p in pairs]
        y_vals = [float(p[1]) for p in pairs]

        r = CriteriaService.calculate_pearson_r(x_vals, y_vals)
        interp = CriteriaService.interpret_correlation(r, c1.criteria_name, c2.criteria_name)

        return CriteriaCorrelation(
            criteria_1_id=c1.id,
            criteria_1_name=c1.criteria_name,
            criteria_2_id=c2.id,
            criteria_2_name=c2.criteria_name,
            system_id=c1.ranking_system_id,
            system_name=c1.ranking_system.system_name,
            year=year,
            sample_size=len(pairs),
            pearson_r=r,
            interpretation=interp
        )

    @staticmethod
    def get_system_correlations_matrix(
        db: Session,
        system_id: int,
        year: Optional[int] = None
    ) -> CriteriaAnalysisResponse:
        system = db.query(RankingSystem).filter(RankingSystem.id == system_id).first()
        if not system:
            raise ValueError(f"System with ID {system_id} not found.")

        criteria = db.query(RankingCriteria).filter(
            RankingCriteria.ranking_system_id == system_id
        ).order_by(RankingCriteria.id).all()

        correlations = []
        for i in range(len(criteria)):
            for j in range(i + 1, len(criteria)):
                try:
                    corr = CriteriaService.get_criteria_correlation(
                        db, criteria[i].id, criteria[j].id, year=year
                    )
                    correlations.append(corr)
                except Exception:
                    continue

        dists = CriteriaService.get_criteria_distributions(db, system_id=system_id)
        notes = [
            "Correlations reflect empirical co-variation within the same ranking system.",
            "All correlations are non-causal."
        ]
        if system_id == 3:
            notes.append("For CWUR: Criteria 14-20 are ranks (lower is better); Criterion 21 is a score (higher is better).")

        return CriteriaAnalysisResponse(
            distributions=dists,
            correlations=correlations,
            notes=notes
        )
