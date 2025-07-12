from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import ComparisonReport


def create_report(
    db: Session,
    session_id: str,
    report_format: str,
    content: str,
    analysis_json: Optional[str] = None,
) -> ComparisonReport:
    """Create and persist a comparison report to the database."""
    db_report = ComparisonReport(
        session_id=session_id,
        report_format=report_format,
        content=content,
        analysis_json=analysis_json,
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def get_report(db: Session, report_id: int) -> Optional[ComparisonReport]:
    return db.get(ComparisonReport, report_id)


def list_reports(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    session_id: Optional[str] = None,
) -> List[ComparisonReport]:
    stmt = select(ComparisonReport)
    if session_id:
        stmt = stmt.where(ComparisonReport.session_id == session_id)
    stmt = stmt.order_by(ComparisonReport.id.desc()).offset(skip).limit(limit)
    return db.scalars(stmt).all() 