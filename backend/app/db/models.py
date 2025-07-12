from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.database import Base


class ComparisonReport(Base):
    """ORM model representing a saved comparison report."""

    __tablename__ = "comparison_reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    report_format = Column(String(16), default="md", nullable=False)
    content = Column(Text, nullable=False)
    analysis_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 