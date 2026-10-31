from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.overview_service import OverviewService
from app.services.country_service import CountryService
from app.models.schemas import (
    OverviewKPIs,
    CountryCount,
    CountryDetailResponse,
    MultiSystemUniversity
)

router = APIRouter()

@router.get("/overview", response_model=OverviewKPIs, summary="Global Overview KPIs and Coverage")
def get_overview(db: Session = Depends(get_db)):
    """Retrieve top-level platform KPIs, system coverage, and institutional totals."""
    return OverviewService.get_overview_kpis(db)

@router.get("/overview/multi-system", response_model=List[MultiSystemUniversity], summary="Universities in Multiple Ranking Systems")
def get_multi_system_universities(
    min_systems: int = Query(2, ge=2, le=3, description="Minimum number of ranking systems (2 or 3)"),
    db: Session = Depends(get_db)
):
    """Retrieve institutions that appear across multiple ranking authorities."""
    return OverviewService.get_multi_system_universities(db, min_systems=min_systems)

@router.get("/universities", summary="Searchable & Paginated University Catalog")
def list_universities(
    country_id: Optional[int] = Query(None, description="Filter by Country ID"),
    search: Optional[str] = Query(None, min_length=1, description="Case-insensitive name search query"),
    limit: int = Query(50, ge=1, le=5000, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """List higher education institutions with optional filtering by country and name search."""
    return OverviewService.list_universities(
        db, country_id=country_id, search=search, limit=limit, offset=offset
    )

@router.get("/universities/{university_id}", summary="Get University Detail")
def get_university_detail(
    university_id: int = Path(..., description="Unique University ID"),
    db: Session = Depends(get_db)
):
    """Get single university profile with country and appearances across ranking authorities."""
    from app.database.models import University, UniversityRankingYear, RankingCriteria, RankingSystem
    from sqlalchemy import distinct

    uni = db.query(University).filter(University.id == university_id).first()
    if not uni:
        raise HTTPException(status_code=404, detail=f"University with ID {university_id} not found.")

    sys_rows = db.query(distinct(RankingSystem.id), RankingSystem.system_name)\
                 .join(RankingCriteria, RankingSystem.id == RankingCriteria.ranking_system_id)\
                 .join(UniversityRankingYear, RankingCriteria.id == UniversityRankingYear.ranking_criteria_id)\
                 .filter(UniversityRankingYear.university_id == university_id).all()

    return {
        "id": uni.id,
        "university_name": uni.university_name,
        "country_id": uni.country_id,
        "country_name": uni.country.country_name,
        "ranking_systems": [{"id": s[0], "name": s[1]} for s in sys_rows]
    }

@router.get("/countries", summary="List All Countries & University Distribution")
def list_countries(db: Session = Depends(get_db)):
    """Retrieve all countries represented in the dataset and their total institution counts."""
    return CountryService.get_country_university_distribution(db)

@router.get("/countries/{country_id}", response_model=CountryDetailResponse, summary="Country Performance Profile")
def get_country_detail(
    country_id: int = Path(..., description="Unique Country ID"),
    db: Session = Depends(get_db)
):
    """Retrieve detailed country profile, system representation, and historical score metrics."""
    try:
        return CountryService.get_country_detail(db, country_id=country_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/ranking-systems", summary="List Ranking Systems")
def list_ranking_systems(db: Session = Depends(get_db)):
    """Retrieve the three world ranking systems."""
    return OverviewService.list_ranking_systems(db)

@router.get("/criteria", summary="List Ranking Criteria")
def list_criteria(
    system_id: Optional[int] = Query(None, description="Filter criteria by ranking system ID (1: THE, 2: Shanghai, 3: CWUR)"),
    db: Session = Depends(get_db)
):
    """Retrieve ranking criteria metadata, metric types (rank vs score), and system mappings."""
    return OverviewService.list_criteria(db, system_id=system_id)
