from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, asc
from app.database.models import RankingCriteria, University, UniversityRankingYear, Country
from app.models.schemas import TrendsResponse, UniversityTrendSeries, TrendDataPoint, TopMover

class TrendsService:

    @staticmethod
    def get_university_trends(
        db: Session,
        university_ids: List[int],
        criteria_id: int,
        compute_movers: bool = True
    ) -> TrendsResponse:
        criterion = db.query(RankingCriteria).filter(RankingCriteria.id == criteria_id).first()
        if not criterion:
            raise ValueError(f"Criteria with ID {criteria_id} does not exist.")

        system = criterion.ranking_system

        # Fetch ranks for all universities in this criteria across years to compute relative position
        # Using a subquery with DENSE_RANK() window function
        rank_order = asc(UniversityRankingYear.score) if criterion.is_rank else desc(UniversityRankingYear.score)
        
        # Query score data for the specific universities
        score_rows = db.query(
            UniversityRankingYear.university_id,
            University.university_name,
            UniversityRankingYear.year,
            UniversityRankingYear.score
        ).join(University, UniversityRankingYear.university_id == University.id)\
         .filter(
             and_(
                 UniversityRankingYear.university_id.in_(university_ids),
                 UniversityRankingYear.ranking_criteria_id == criteria_id
             )
         ).order_by(UniversityRankingYear.university_id, UniversityRankingYear.year).all()

        # Compute ranks per year across ALL universities in that criterion
        all_year_scores = db.query(
            UniversityRankingYear.university_id,
            UniversityRankingYear.year,
            func.dense_rank().over(
                partition_by=UniversityRankingYear.year,
                order_by=rank_order
            ).label("rank_pos")
        ).filter(
            and_(
                UniversityRankingYear.ranking_criteria_id == criteria_id,
                UniversityRankingYear.score.isnot(None)
            )
        ).all()

        rank_lookup = {(r[0], r[1]): r[2] for r in all_year_scores}

        from collections import defaultdict
        grouped_unis = defaultdict(list)
        uni_names = {}
        for uid, uname, yr, sc in score_rows:
            grouped_unis[uid].append((yr, float(sc) if sc is not None else None))
            uni_names[uid] = uname

        series_list = []
        for uid in university_ids:
            if uid in grouped_unis:
                pts = [
                    TrendDataPoint(
                        year=yr,
                        score=sc,
                        rank_in_system=rank_lookup.get((uid, yr))
                    )
                    for yr, sc in grouped_unis[uid]
                ]
                series_list.append(UniversityTrendSeries(
                    university_id=uid,
                    university_name=uni_names[uid],
                    criteria_id=criterion.id,
                    criteria_name=criterion.criteria_name,
                    metric_type=criterion.metric_type,
                    data_points=pts
                ))

        strongest_improvements: List[TopMover] = []
        strongest_declines: List[TopMover] = []

        if compute_movers:
            # Determine available years for this criterion
            years_avail = db.query(func.min(UniversityRankingYear.year), func.max(UniversityRankingYear.year))\
                            .filter(UniversityRankingYear.ranking_criteria_id == criteria_id).first()
            if years_avail and years_avail[0] and years_avail[1] and years_avail[0] != years_avail[1]:
                min_y, max_y = years_avail[0], years_avail[1]
                strongest_improvements, strongest_declines = TrendsService.get_top_movers(
                    db, criteria_id, min_y, max_y, limit=5
                )

        return TrendsResponse(
            system_id=system.id,
            system_name=system.system_name,
            criteria_id=criterion.id,
            criteria_name=criterion.criteria_name,
            metric_type=criterion.metric_type,
            trends=series_list,
            strongest_improvements=strongest_improvements,
            strongest_declines=strongest_declines
        )

    @staticmethod
    def get_top_movers(
        db: Session,
        criteria_id: int,
        start_year: int,
        end_year: int,
        limit: int = 5
    ) -> Tuple[List[TopMover], List[TopMover]]:
        """Identify institutions with the strongest score improvements and declines between two years."""
        criterion = db.query(RankingCriteria).filter(RankingCriteria.id == criteria_id).first()
        if not criterion:
            return [], []

        # Subquery for start year
        start_scores = db.query(
            UniversityRankingYear.university_id,
            UniversityRankingYear.score.label("start_score")
        ).filter(
            and_(
                UniversityRankingYear.ranking_criteria_id == criteria_id,
                UniversityRankingYear.year == start_year,
                UniversityRankingYear.score.isnot(None)
            )
        ).subquery()

        # Subquery for end year
        end_scores = db.query(
            UniversityRankingYear.university_id,
            UniversityRankingYear.score.label("end_score")
        ).filter(
            and_(
                UniversityRankingYear.ranking_criteria_id == criteria_id,
                UniversityRankingYear.year == end_year,
                UniversityRankingYear.score.isnot(None)
            )
        ).subquery()

        # Join both on university_id
        paired = db.query(
            University.id,
            University.university_name,
            Country.country_name,
            start_scores.c.start_score,
            end_scores.c.end_score
        ).join(start_scores, University.id == start_scores.c.university_id)\
         .join(end_scores, University.id == end_scores.c.university_id)\
         .join(Country, University.country_id == Country.id).all()

        movers = []
        for uid, uname, cname, s_sc, e_sc in paired:
            s_val = float(s_sc)
            e_val = float(e_sc)
            diff = e_val - s_val
            pct = ((e_val - s_val) / s_val * 100.0) if s_val != 0 else 0.0

            movers.append(TopMover(
                university_id=uid,
                university_name=uname,
                country_name=cname,
                start_year=start_year,
                end_year=end_year,
                start_score=round(s_val, 2),
                end_score=round(e_val, 2),
                absolute_change=round(diff, 2),
                percent_change=round(pct, 2)
            ))

        if criterion.is_rank:
            # For ranks: lower is better! Negative change (e.g. 50 -> 10 = -40) is an improvement!
            improvements = sorted(movers, key=lambda m: m.absolute_change)[:limit]
            declines = sorted(movers, key=lambda m: m.absolute_change, reverse=True)[:limit]
        else:
            # For scores: higher is better! Positive change is an improvement!
            improvements = sorted(movers, key=lambda m: m.absolute_change, reverse=True)[:limit]
            declines = sorted(movers, key=lambda m: m.absolute_change)[:limit]

        return improvements, declines
