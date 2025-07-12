import json
from loguru import logger
from app.db.database import SessionLocal
from app.db import crud


async def save_report_to_db(
    *,
    session_id: str,
    report_format: str,
    content: str,
    analysis_result: dict | None = None,
):
    """Save generated report content and optional analysis result to database."""
    db = SessionLocal()
    try:
        analysis_json = (
            json.dumps(analysis_result, ensure_ascii=False)
            if analysis_result is not None
            else None
        )
        db_report = crud.create_report(
            db=db,
            session_id=session_id,
            report_format=report_format,
            content=content,
            analysis_json=analysis_json,
        )
        logger.info(
            f"💾 Saved comparison report #{db_report.id} for session {session_id}"
        )
        return db_report
    except Exception as e:
        logger.error(f"❌ Failed to save report to DB: {e}")
    finally:
        db.close() 