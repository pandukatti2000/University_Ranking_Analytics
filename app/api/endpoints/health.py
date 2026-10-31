from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db

router = APIRouter()

@router.get("/health", summary="System Health & Database Connectivity Ping")
def check_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1;")).scalar()
        db_status = "connected"
    except Exception as e:
        db_status = f"unreachable: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "service": "University Ranking Analytics API",
        "version": "1.0.0"
    }
