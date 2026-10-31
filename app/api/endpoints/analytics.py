from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.comparison_service import ComparisonService
from app.services.trends_service import TrendsService
from app.services.country_service import CountryService
from app.services.criteria_service import CriteriaService
from app.services.demographics_service import DemographicsService
from app.models.schemas import (
    UniversityComparisonResponse,
    TrendsResponse,
    CriteriaAnalysisResponse,
    DemographicsResponse
)
from pydantic import BaseModel

router = APIRouter()

class AnalyzeRequest(BaseModel):
    analysis_type: str  # 'compare', 'trend', 'country', 'demographics', 'criteria'
    university_ids: Optional[List[int]] = None
    system_id: Optional[int] = None
    criteria_id: Optional[int] = None
    country_id: Optional[int] = None
    year: Optional[int] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None

@router.get("/compare", response_model=UniversityComparisonResponse, summary="Head-to-Head University Comparison")
def compare_universities(
    university_ids: str = Query(..., description="Comma-separated list of university IDs (e.g. '1,2,3')"),
    system_id: int = Query(..., description="Ranking system ID (1: THE, 2: Shanghai, 3: CWUR)"),
    start_year: Optional[int] = Query(None, description="Start year filter"),
    end_year: Optional[int] = Query(None, description="End year filter"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple institutions on criteria scores and demographics within a specific ranking system.
    Enforces scale isolation across ranking authorities.
    """
    try:
        u_ids = [int(x.strip()) for x in university_ids.split(",") if x.strip()]
        if not u_ids:
            raise ValueError("At least one university ID must be specified.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid format for university_ids. Expected comma-separated integers.")

    try:
        return ComparisonService.compare_universities(
            db,
            university_ids=u_ids,
            system_id=system_id,
            start_year=start_year,
            end_year=end_year
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trends", response_model=TrendsResponse, summary="Longitudinal Trajectories and Top Movers")
def get_trends(
    university_ids: str = Query(..., description="Comma-separated list of university IDs"),
    criteria_id: int = Query(..., description="Ranking criteria ID to track over time"),
    compute_movers: bool = Query(True, description="Whether to include strongest improvements and declines"),
    db: Session = Depends(get_db)
):
    """Track multi-year university performance, dynamic relative ranking positions, and top movers."""
    try:
        u_ids = [int(x.strip()) for x in university_ids.split(",") if x.strip()]
        if not u_ids:
            raise ValueError("At least one university ID must be specified.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid format for university_ids. Expected comma-separated integers.")

    try:
        return TrendsService.get_university_trends(
            db,
            university_ids=u_ids,
            criteria_id=criteria_id,
            compute_movers=compute_movers
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/country-comparison", summary="Compare Countries on Criteria")
def compare_countries(
    criteria_id: int = Query(..., description="Criterion ID"),
    year: int = Query(..., description="Year"),
    min_universities: int = Query(2, ge=1, description="Minimum number of institutions required for a country to be included"),
    db: Session = Depends(get_db)
):
    """Compare country-level performance for a specific criterion and year."""
    try:
        return CountryService.compare_countries_by_criteria(
            db, criteria_id=criteria_id, year=year, min_universities=min_universities
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/criteria", response_model=CriteriaAnalysisResponse, summary="Criteria Distributions and Trade-offs")
def get_criteria_analysis(
    system_id: int = Query(..., description="Ranking system ID (1: THE, 2: Shanghai, 3: CWUR)"),
    year: Optional[int] = Query(None, description="Optional single year filter"),
    db: Session = Depends(get_db)
):
    """Retrieve statistical score distributions and pairwise Pearson correlations among criteria within a system."""
    try:
        return CriteriaService.get_system_correlations_matrix(db, system_id=system_id, year=year)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/demographics", response_model=DemographicsResponse, summary="Student Demographics & Associations")
def get_demographics(db: Session = Depends(get_db)):
    """Analyze student populations, internationalization, staff ratios, and empirical associations with ranking indicators."""
    return DemographicsService.get_demographics_overview(db)

@router.post("/analyze", summary="Structured Analytical Query Dispatcher")
def analyze_data(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """Unified POST analytics endpoint that dispatches requests to appropriate deterministic analytics engines."""
    a_type = payload.analysis_type.lower()
    if a_type == "compare":
        if not payload.university_ids or not payload.system_id:
            raise HTTPException(status_code=400, detail="compare requires university_ids and system_id")
        return ComparisonService.compare_universities(
            db,
            university_ids=payload.university_ids,
            system_id=payload.system_id,
            start_year=payload.start_year,
            end_year=payload.end_year
        )
    elif a_type == "trend":
        if not payload.university_ids or not payload.criteria_id:
            raise HTTPException(status_code=400, detail="trend requires university_ids and criteria_id")
        return TrendsService.get_university_trends(
            db,
            university_ids=payload.university_ids,
            criteria_id=payload.criteria_id
        )
    elif a_type == "country":
        if not payload.country_id:
            raise HTTPException(status_code=400, detail="country requires country_id")
        return CountryService.get_country_detail(db, country_id=payload.country_id)
    elif a_type == "criteria":
        if not payload.system_id:
            raise HTTPException(status_code=400, detail="criteria requires system_id")
        return CriteriaService.get_system_correlations_matrix(db, system_id=payload.system_id, year=payload.year)
    elif a_type == "demographics":
        return DemographicsService.get_demographics_overview(db)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported analysis_type '{payload.analysis_type}'.")
