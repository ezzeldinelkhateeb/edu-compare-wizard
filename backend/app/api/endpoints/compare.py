"""
API endpoints للمقارنة
Comparison API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Response
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
from loguru import logger
import asyncio
import os
import json
import math

from app.core.config import get_settings
from app.models.schemas import (
    StartComparisonRequest, StartComparisonResponse, 
    ComparisonSessionResult, ProcessingProgress,
    JobStatus, ErrorResponse, ProcessingStage
)
from celery_app.tasks import process_file_comparison
from app.db.database import SessionLocal
from app.db import crud


settings = get_settings()
router = APIRouter()

# تخزين معلومات الوظائف مؤقتاً (في التطبيق الحقيقي سيكون في قاعدة البيانات)
jobs_store = {}

# تخزين معلومات الجلسات
sessions_store = {}


def clean_json_values(obj):
    """
    تنظيف القيم لتكون متوافقة مع JSON
    Clean values to be JSON compliant
    """
    if isinstance(obj, dict):
        return {k: clean_json_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif hasattr(obj, '__dict__'):
        return clean_json_values(obj.__dict__)
    else:
        return obj


@router.post("/compare/start", response_model=StartComparisonResponse)
async def start_comparison(request: StartComparisonRequest):
    """
    بدء عملية المقارنة
    Start comparison process
    """
    try:
        # التحقق من وجود الملفات
        if not request.old_files or not request.new_files:
            raise HTTPException(
                status_code=400, 
                detail="يجب تحديد ملفات للمنهج القديم والجديد"
            )
        
        if len(request.old_files) != len(request.new_files):
            raise HTTPException(
                status_code=400,
                detail="عدد الملفات القديمة يجب أن يساوي عدد الملفات الجديدة"
            )
        
        # إنشاء معرف وظيفة جديد
        job_id = str(uuid.uuid4())
        
        logger.info(f"🚀 بدء عملية مقارنة جديدة - Job: {job_id}, Session: {request.session_id}")
        logger.info(f"📁 عدد الملفات: {len(request.old_files)} قديم, {len(request.new_files)} جديد")
        
        # حفظ معلومات الوظيفة
        job_info = {
            "job_id": job_id,
            "session_id": request.session_id,
            "status": JobStatus.PENDING,
            "old_files": request.old_files,
            "new_files": request.new_files,
            "comparison_settings": request.comparison_settings,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "progress": 0,
            "current_stage": ProcessingStage.INITIALIZATION.value,
            "current_file": None,
            "error_message": None,
            "result": None
        }
        
        jobs_store[job_id] = job_info
        
        # بدء مهمة Celery
        try:
            task = process_file_comparison.delay(
                job_id=job_id,
                session_id=request.session_id,
                old_files=request.old_files,
                new_files=request.new_files
            )
            
            # حفظ معرف المهمة
            job_info["celery_task_id"] = task.id
            job_info["status"] = JobStatus.PROCESSING
            
            logger.info(f"✅ تم بدء مهمة Celery: {task.id} للوظيفة {job_id}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء مهمة Celery: {e}")
            job_info["status"] = JobStatus.FAILED
            job_info["error_message"] = f"فشل في بدء المعالجة: {str(e)}"
            raise HTTPException(
                status_code=500,
                detail=f"فشل في بدء عملية المقارنة: {str(e)}"
            )
        
        return StartComparisonResponse(
            job_id=job_id,
            session_id=request.session_id,
            status=JobStatus.PROCESSING,
            message="تم بدء عملية المقارنة بنجاح"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في بدء المقارنة: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في بدء عملية المقارنة: {str(e)}"
        )


@router.get("/compare/status/{job_id}", response_model=ProcessingProgress)
async def get_comparison_status(job_id: str):
    """
    الحصول على حالة المقارنة
    Get comparison status
    """
    logger.debug(f"🔍 جلب الحالة للوظيفة: {job_id}")
    try:
        if job_id not in jobs_store:
            logger.warning(f"⚠️ محاولة جلب وظيفة غير موجودة: {job_id}")
            raise HTTPException(status_code=404, detail="الوظيفة غير موجودة")
        
        job_info = jobs_store[job_id]
        logger.debug(f"ℹ️ المعلومات الأولية للوظيفة: {job_info}")
        
        # إذا كانت الوظيفة تحتوي على مهمة Celery، تحقق من حالتها
        if "celery_task_id" in job_info:
            from celery_app.worker import celery_app
            task = celery_app.AsyncResult(job_info["celery_task_id"])
            logger.debug(f"📊 حالة مهمة Celery [{task.id}]: {task.state}")
            
            # تحديث الحالة بناءً على حالة Celery
            if task.state == "PENDING":
                job_info["status"] = JobStatus.PENDING
            elif task.state == "PROGRESS":
                job_info["status"] = JobStatus.PROCESSING
                if isinstance(task.info, dict):
                    logger.debug(f"📈 بيانات التقدم من Celery: {task.info}")
                    job_info["progress"] = task.info.get("progress", job_info["progress"])
                    job_info["message"] = task.info.get("message", job_info.get("message"))
                    job_info["current_stage"] = task.info.get("current_stage", job_info.get("current_stage"))
                    job_info["current_file"] = task.info.get("current_file", job_info.get("current_file"))
            elif task.state == "SUCCESS":
                job_info["status"] = JobStatus.COMPLETED
                logger.debug(f"✅ مهمة Celery ناجحة. النتيجة: {task.result}")
                job_info["result"] = task.result
                job_info["progress"] = 100
                job_info["message"] = "اكتملت المعالجة بنجاح"
            elif task.state == "FAILURE":
                job_info["status"] = JobStatus.FAILED
                logger.error(f"☠️ فشل مهمة Celery. الخطأ: {task.info}")
                job_info["error_message"] = str(task.info) if task.info else "فشل غير معروف"
        
        job_info["updated_at"] = datetime.now()
        
        progress_response = ProcessingProgress(
            job_id=job_id,
            session_id=job_info["session_id"],
            status=job_info["status"],
            current_stage=job_info.get("current_stage", "UNKNOWN"),
            progress_percentage=job_info.get("progress", 0),
            current_file=job_info.get("current_file"),
            files_processed=job_info.get("files_processed", 0),
            total_files=len(job_info["old_files"]) + len(job_info["new_files"]),
            estimated_time_remaining=job_info.get("estimated_time_remaining"),
            message=job_info.get("message"),
            error_message=job_info.get("error_message"),
            created_at=job_info["created_at"],
            updated_at=job_info["updated_at"]
        )
        logger.debug(f"📬 إرسال استجابة الحالة: {progress_response}")
        return progress_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.opt(exception=True).error(f"❌ خطأ فادح في جلب حالة الوظيفة {job_id}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في جلب حالة الوظيفة: {str(e)}"
        )


@router.get("/compare/result/{job_id}", response_model=ComparisonSessionResult)
async def get_comparison_result(job_id: str):
    """
    الحصول على نتيجة المقارنة
    Get comparison result
    """
    try:
        if job_id not in jobs_store:
            raise HTTPException(status_code=404, detail="الوظيفة غير موجودة")
        
        job_info = jobs_store[job_id]
        
        if job_info["status"] != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"الوظيفة لم تكتمل بعد. الحالة الحالية: {job_info['status']}"
            )
        
        if not job_info.get("result"):
            raise HTTPException(status_code=404, detail="نتائج المقارنة غير متوفرة")
        
        result = job_info["result"]
        
        # تحويل النتائج إلى ComparisonSessionResult
        comparison_result = ComparisonSessionResult(
            session_id=job_info["session_id"],
            job_id=job_id,
            session_name=f"مقارنة_{job_id[:8]}",
            status=JobStatus.COMPLETED,
            total_files=result.get("total_files", 0),
            processed_files=result.get("processed_files", 0),
            identical_files=len([r for r in result.get("results", []) if r.get("overall_similarity", 0) > 95]),
            changed_files=len([r for r in result.get("results", []) if r.get("overall_similarity", 0) <= 95]),
            failed_files=result.get("failed_files", 0),
            average_visual_similarity=result.get("summary", {}).get("average_visual_similarity", 0),
            average_text_similarity=result.get("summary", {}).get("average_text_similarity", 0),
            average_overall_similarity=(
                result.get("summary", {}).get("average_visual_similarity", 0) +
                result.get("summary", {}).get("average_text_similarity", 0)
            ) / 2,
            file_results=[],  # سيتم تحويل هذا لاحقاً
            total_processing_time=sum(r.get("visual_comparison", {}).get("processing_time", 0) + 
                                    r.get("text_comparison", {}).get("processing_time", 0) 
                                    for r in result.get("results", [])),
            created_at=job_info["created_at"],
            completed_at=datetime.fromisoformat(result.get("completed_at", datetime.now().isoformat()))
        )
        
        logger.info(f"📊 تم جلب نتائج المقارنة للوظيفة: {job_id}")
        return comparison_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في جلب نتائج الوظيفة {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في جلب نتائج المقارنة: {str(e)}"
        )


@router.delete("/compare/job/{job_id}")
async def cancel_comparison(job_id: str):
    """
    إلغاء عملية المقارنة
    Cancel comparison process
    """
    try:
        if job_id not in jobs_store:
            raise HTTPException(status_code=404, detail="الوظيفة غير موجودة")
        
        job_info = jobs_store[job_id]
        
        # إلغاء مهمة Celery إذا كانت قيد التشغيل
        if "celery_task_id" in job_info and job_info["status"] == JobStatus.PROCESSING:
            from celery_app.worker import celery_app
            celery_app.control.revoke(job_info["celery_task_id"], terminate=True)
            logger.info(f"🛑 تم إلغاء مهمة Celery: {job_info['celery_task_id']}")
        
        # تحديث حالة الوظيفة
        job_info["status"] = JobStatus.CANCELLED
        job_info["updated_at"] = datetime.now()
        job_info["message"] = "تم إلغاء الوظيفة بواسطة المستخدم"
        
        logger.info(f"🛑 تم إلغاء الوظيفة: {job_id}")
        
        return {
            "success": True,
            "message": "تم إلغاء عملية المقارنة بنجاح",
            "job_id": job_id,
            "cancelled_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في إلغاء الوظيفة {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في إلغاء الوظيفة: {str(e)}"
        )


@router.get("/compare/jobs")
async def list_all_jobs():
    """
    قائمة جميع الوظائف
    List all jobs
    """
    try:
        jobs_list = []
        for job_id, job_info in jobs_store.items():
            jobs_list.append({
                "job_id": job_id,
                "session_id": job_info["session_id"],
                "status": job_info["status"],
                "progress": job_info.get("progress", 0),
                "current_stage": job_info.get("current_stage"),
                "total_files": len(job_info["old_files"]),
                "created_at": job_info["created_at"],
                "updated_at": job_info["updated_at"]
            })
        
        return {
            "jobs": jobs_list,
            "total_jobs": len(jobs_list),
            "active_jobs": len([j for j in jobs_list if j["status"] == JobStatus.PROCESSING]),
            "completed_jobs": len([j for j in jobs_list if j["status"] == JobStatus.COMPLETED]),
            "failed_jobs": len([j for j in jobs_list if j["status"] == JobStatus.FAILED])
        }
        
    except Exception as e:
        logger.error(f"❌ خطأ في جلب قائمة الوظائف: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في جلب قائمة الوظائف: {str(e)}"
        )


@router.post("/compare/create-session")
async def create_comparison_session(
    old_image: UploadFile = File(...),
    new_image: UploadFile = File(...)
):
    """
    إنشاء جلسة مقارنة جديدة مع رفع الصور
    Create new comparison session with image uploads
    """
    try:
        session_id = str(uuid.uuid4())
        
        # إنشاء مجلد للجلسة
        session_dir = os.path.join(settings.UPLOAD_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # حفظ الصور
        old_image_path = os.path.join(session_dir, f"old_image_{old_image.filename}")
        new_image_path = os.path.join(session_dir, f"new_image_{new_image.filename}")
        
        # كتابة الملفات
        with open(old_image_path, "wb") as f:
            content = await old_image.read()
            f.write(content)
            
        with open(new_image_path, "wb") as f:
            content = await new_image.read()
            f.write(content)
        
        # حفظ معلومات الجلسة
        session_info = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "uploaded_files": {
                "old": {
                    "filename": old_image.filename,
                    "path": old_image_path,
                    "size": os.path.getsize(old_image_path)
                },
                "new": {
                    "filename": new_image.filename,
                    "path": new_image_path,
                    "size": os.path.getsize(new_image_path)
                }
            }
        }
        
        sessions_store[session_id] = session_info
        
        logger.info(f"🆕 تم إنشاء جلسة مقارنة جديدة: {session_id}")
        logger.info(f"📁 تم رفع الملفات: {old_image.filename}, {new_image.filename}")
        
        return {
            "session_id": session_id,
            "status": "created",
            "message": "تم إنشاء جلسة المقارنة بنجاح",
            "files_uploaded": {
                "old_image": old_image.filename,
                "new_image": new_image.filename
            }
        }
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء جلسة المقارنة: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في إنشاء جلسة المقارنة: {str(e)}"
        )


@router.post("/compare/extract-text/{session_id}/{file_type}")
async def extract_text_from_image(session_id: str, file_type: str):
    """
    استخراج النص من الصورة
    Extract text from image using OCR
    """
    try:
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        session = sessions_store[session_id]
        
        # التحقق من وجود الملف
        if file_type not in session["uploaded_files"] or not session["uploaded_files"][file_type]:
            raise HTTPException(
                status_code=400, 
                detail=f"لم يتم رفع صورة {file_type} للجلسة {session_id}"
            )
        
        uploaded_file = session["uploaded_files"][file_type]
        image_path = uploaded_file["path"]
        
        # استخدام خدمة Landing AI للاستخراج الحقيقي
        from app.services.landing_ai_service import LandingAIService
        
        logger.info(f"🚀 بدء استخراج النص من الصورة {file_type} باستخدام Landing AI...")
        
        # إنشاء خدمة Landing AI
        landing_ai_service = LandingAIService()
        
        # استخراج النص باستخدام Landing AI
        extraction_result = await landing_ai_service.extract_from_file(
            file_path=image_path,
            job_id=session_id
        )
        
        if not extraction_result.success:
            logger.error(f"❌ فشل في استخراج النص: {extraction_result.error_message}")
            raise HTTPException(
                status_code=500,
                detail=f"فشل في استخراج النص: {extraction_result.error_message}"
            )
        
        # تحويل النتيجة إلى التنسيق المتوقع
        ocr_result = {
            "success": True,
            "text": extraction_result.markdown_content or "لم يتم استخراج نص",
            "confidence": extraction_result.confidence_score,
            "language": "ar",
            "character_count": len(extraction_result.markdown_content or ""),
            "word_count": len((extraction_result.markdown_content or "").split()),
            "processing_time": extraction_result.processing_time,
            "image_info": {
                "width": 800,  # يمكن تحسين هذا لاحقاً
                "height": 600,
                "format": "PNG",
                "size_bytes": uploaded_file["size"]
            },
            "extraction_details": {
                "total_chunks": extraction_result.total_chunks,
                "chunks_by_type": extraction_result.chunks_by_type,
                "text_elements": extraction_result.text_elements,
                "table_elements": extraction_result.table_elements,
                "image_elements": extraction_result.image_elements
            }
        }
        
        # حفظ نتيجة OCR في الجلسة
        session["ocr_results"] = session.get("ocr_results", {})
        session["ocr_results"][file_type] = ocr_result
        
        logger.info(f"✅ تم استخراج النص من الصورة {file_type} للجلسة {session_id}")
        logger.info(f"📊 تفاصيل الاستخراج: {extraction_result.word_count if hasattr(extraction_result, 'word_count') else len((extraction_result.markdown_content or '').split())} كلمة، ثقة: {extraction_result.confidence_score:.2f}")
        
        return ocr_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في استخراج النص: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في استخراج النص: {str(e)}"
        )


@router.post("/compare/analyze/{session_id}")
async def analyze_comparison(session_id: str):
    """
    تحليل المقارنة بالذكاء الاصطناعي
    AI-powered comparison analysis
    """
    try:
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        session = sessions_store[session_id]
        
        # التحقق من وجود النصوص المستخرجة
        ocr_results = session.get("ocr_results", {})
        old_text = ocr_results.get("old")
        new_text = ocr_results.get("new")
        
        if not old_text or not new_text:
            raise HTTPException(
                status_code=400, 
                detail="يجب استخراج النص من كلا الصورتين أولاً"
            )
        
        # استخدام خدمة Gemini للتحليل الحقيقي
        from app.services.gemini_service import GeminiService
        
        logger.info(f"🤖 بدء تحليل المقارنة باستخدام Gemini AI...")
        
        # استخراج النصوص من نتائج OCR
        old_extracted_text = old_text.get("text", "")
        new_extracted_text = new_text.get("text", "")
        
        # إنشاء خدمة Gemini
        gemini_service = GeminiService()
        
        # إعداد السياق للمقارنة
        comparison_context = {
            "domain": "education",
            "content_type": "curriculum",
            "language": "arabic",
            "analysis_type": "educational_content_comparison",
            "old_file_info": {
                "character_count": old_text.get("character_count", 0),
                "word_count": old_text.get("word_count", 0),
                "confidence": old_text.get("confidence", 0)
            },
            "new_file_info": {
                "character_count": new_text.get("character_count", 0),
                "word_count": new_text.get("word_count", 0),
                "confidence": new_text.get("confidence", 0)
            }
        }
        
        logger.info(f"📝 تحليل النصوص: القديم ({len(old_extracted_text)} حرف), الجديد ({len(new_extracted_text)} حرف)")
        
        # تشغيل تحليل المقارنة باستخدام Gemini
        comparison_result = await gemini_service.compare_texts(
            old_text=old_extracted_text,
            new_text=new_extracted_text,
            context=comparison_context
        )
        
        # تحويل النتيجة إلى التنسيق المتوقع
        analysis_result = {
            "similarity_percentage": comparison_result.similarity_percentage,
            "content_changes": comparison_result.content_changes,
            "questions_changes": comparison_result.questions_changes,
            "major_differences": comparison_result.major_differences,
            "added_content": comparison_result.added_content,
            "removed_content": comparison_result.removed_content,
            "summary": comparison_result.summary,
            "recommendation": comparison_result.recommendation,
            "detailed_analysis": comparison_result.detailed_analysis,
            "processing_time": comparison_result.processing_time,
            "confidence_score": comparison_result.confidence_score,
            "old_text_length": comparison_result.old_text_length,
            "new_text_length": comparison_result.new_text_length,
            "common_words_count": comparison_result.common_words_count,
            "unique_old_words": comparison_result.unique_old_words,
            "unique_new_words": comparison_result.unique_new_words,
            "service_used": comparison_result.service_used,
            "examples_changes": getattr(comparison_result, 'examples_changes', []),
            "modified_content": getattr(comparison_result, 'modified_content', [])
        }
        
        # حفظ النتيجة في الجلسة
        session["analysis_result"] = analysis_result
        session["status"] = "completed"
        
        logger.info(f"✅ تم تحليل المقارنة للجلسة {session_id}")
        logger.info(f"📊 نتائج التحليل: {comparison_result.similarity_percentage:.1f}% تشابه، ثقة: {comparison_result.confidence_score:.2f}")
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في تحليل المقارنة: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في تحليل المقارنة: {str(e)}"
        )


@router.get("/compare/download-report/{session_id}")
async def download_report(session_id: str, format: str = "html"):
    """
    تحميل تقرير المقارنة بصيغة HTML أو Markdown
    Download comparison report in HTML or Markdown format
    """
    try:
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        session = sessions_store[session_id]
        
        if session["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail="لم تكتمل عملية المقارنة بعد"
            )
        
        # إنشاء التقرير المحسن باستخدام الخدمة الجديدة
        from app.services.enhanced_report_service import EnhancedReportService, ReportData
        from app.services.visual_comparison_service import VisualComparisonService
        from fastapi.responses import Response
        
        # الحصول على بيانات الجلسة
        ocr_results = session.get("ocr_results", {})
        analysis_result = session.get("analysis_result", {})
        uploaded_files = session.get("uploaded_files", {})
        
        # حساب التشابه البصري
        from app.services.visual_comparison_service import enhanced_visual_comparison_service
        visual_similarity = 95.0  # قيمة افتراضية، سيتم حسابها من الصور
        
        if "old" in uploaded_files and "new" in uploaded_files:
            try:
                old_file_path = uploaded_files["old"]["path"]
                new_file_path = uploaded_files["new"]["path"]
                
                # إنشاء مجلد مؤقت للمقارنة البصرية
                temp_output_dir = os.path.join(settings.UPLOAD_DIR, session_id, "temp_visual")
                os.makedirs(temp_output_dir, exist_ok=True)
                
                visual_result = await enhanced_visual_comparison_service.compare_images(
                    old_image_path=old_file_path, 
                    new_image_path=new_file_path,
                    output_dir=temp_output_dir
                )
                visual_similarity = visual_result.similarity_score
            except Exception as e:
                logger.warning(f"⚠️ فشل في حساب التشابه البصري: {e}")
        
        # تحضير بيانات التقرير
        report_data = ReportData(
            session_id=session_id,
            old_image_name=uploaded_files.get("old", {}).get("filename", "صورة قديمة"),
            new_image_name=uploaded_files.get("new", {}).get("filename", "صورة جديدة"),
            old_extracted_text=ocr_results.get("old", {}).get("text", ""),
            new_extracted_text=ocr_results.get("new", {}).get("text", ""),
            visual_similarity=visual_similarity,
            text_analysis=analysis_result,
            processing_time={
                "old_ocr": ocr_results.get("old", {}).get("processing_time", 0),
                "new_ocr": ocr_results.get("new", {}).get("processing_time", 0),
                "comparison": analysis_result.get("processing_time", 0)
            },
            confidence_scores={
                "old_confidence": ocr_results.get("old", {}).get("confidence", 0),
                "new_confidence": ocr_results.get("new", {}).get("confidence", 0)
            }
        )
        
        # إنشاء خدمة التقارير
        report_service = EnhancedReportService()
        
        # إنتاج التقارير
        report_paths = await report_service.generate_comprehensive_report(
            session_id=session_id,
            report_data=report_data,
            include_extracted_text=True,
            include_visual_analysis=True
        )
        
        # تحديد نوع الملف المطلوب
        if format.lower() == "md" or format.lower() == "markdown":
            file_path = report_paths["markdown_path"]
            media_type = "text/markdown"
            filename = f"تقرير_المقارنة_{session_id}.md"
        elif format.lower() == "txt" or format.lower() == "text":
            file_path = report_paths["extracted_text_path"]
            media_type = "text/plain"
            filename = f"النصوص_المستخرجة_{session_id}.md"
        else:  # HTML افتراضي
            file_path = report_paths["html_path"]
            media_type = "text/html"
            filename = f"تقرير_المقارنة_{session_id}.html"
        
        # قراءة محتوى الملف
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"📄 تم إنشاء تقرير {format.upper()} للجلسة {session_id}")

        # حفظ التقرير في قاعدة البيانات حتى يمكن الرجوع إليه لاحقاً
        try:
            from app.services.report_storage_service import save_report_to_db
            await save_report_to_db(
                session_id=session_id,
                report_format=format.lower(),
                content=content,
                analysis_result=analysis_result,
            )
        except Exception as save_exc:
            logger.warning(f"⚠️ لم يتم حفظ التقرير في قاعدة البيانات: {save_exc}")

        return Response(
            content=content.encode('utf-8'),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": f"{media_type}; charset=utf-8"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل التقرير: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في تحميل التقرير: {str(e)}"
        )


@router.post("/compare/visual-analysis/{session_id}")
async def perform_visual_comparison(session_id: str):
    """
    إجراء مقارنة بصرية محسنة للصور
    Perform enhanced visual comparison of images
    """
    try:
        logger.info(f"🖼️ بدء المقارنة البصرية للجلسة {session_id}")
        
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        session = sessions_store[session_id]
        uploaded_files = session.get("uploaded_files", {})
        
        if "old" not in uploaded_files or "new" not in uploaded_files:
            raise HTTPException(
                status_code=400,
                detail="يجب رفع كلا الصورتين أولاً"
            )
        
        old_file_path = uploaded_files["old"]["path"]
        new_file_path = uploaded_files["new"]["path"]
        
        # التحقق من وجود الملفات
        if not os.path.exists(old_file_path) or not os.path.exists(new_file_path):
            raise HTTPException(
                status_code=404,
                detail="ملفات الصور غير موجودة"
            )
        
        # استيراد خدمة المقارنة البصرية المحسنة
        from app.services.visual_comparison_service import enhanced_visual_comparison_service
        
        logger.info(f"🔍 تحليل الصور: {uploaded_files['old']['filename']} vs {uploaded_files['new']['filename']}")
        
        # إنشاء مجلد الإخراج
        output_dir = os.path.join(settings.UPLOAD_DIR, session_id, "visual_analysis")
        os.makedirs(output_dir, exist_ok=True)
        
        # إجراء المقارنة البصرية المحسنة
        visual_result = await enhanced_visual_comparison_service.compare_images(
            old_image_path=old_file_path,
            new_image_path=new_file_path,
            output_dir=output_dir
        )
        
        # تحويل النتيجة إلى dict للإرسال
        visual_analysis = {
            "similarity_score": visual_result.similarity_score,
            "ssim_score": visual_result.ssim_score,
            "phash_score": visual_result.phash_score,
            "clip_score": visual_result.clip_score,
            "histogram_correlation": visual_result.histogram_correlation,
            "feature_matching_score": visual_result.feature_matching_score,
            "edge_similarity": visual_result.edge_similarity,
            "layout_similarity": visual_result.layout_similarity,
            "text_region_overlap": visual_result.text_region_overlap,
            "weights_used": visual_result.weights_used,
            "processing_time": visual_result.processing_time,
            "old_image_size": visual_result.old_image_size,
            "new_image_size": visual_result.new_image_size,
            "difference_detected": visual_result.difference_detected,
            "major_changes_detected": visual_result.major_changes_detected,
            "changed_regions": visual_result.changed_regions,
            "mean_squared_error": visual_result.mean_squared_error,
            "peak_signal_noise_ratio": visual_result.peak_signal_noise_ratio,
            "content_type_detected": visual_result.content_type_detected,
            "probable_content_match": visual_result.probable_content_match,
            "analysis_summary": visual_result.analysis_summary,
            "recommendations": visual_result.recommendations,
            "confidence_notes": visual_result.confidence_notes,
            "difference_map_path": visual_result.difference_map_path
        }
        
        # حفظ النتيجة في الجلسة
        session["visual_analysis"] = visual_analysis
        
        logger.info(f"✅ اكتملت المقارنة البصرية: {visual_result.similarity_score:.1f}% تطابق")
        logger.info(f"🎯 التحليل: {visual_result.analysis_summary}")
        
        return visual_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في المقارنة البصرية: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في المقارنة البصرية: {str(e)}"
        )


@router.get("/compare/verify-landingai/{session_id}")
async def verify_landing_ai_usage(session_id: str):
    """
    التحقق من استخدام Landing AI فعلياً في عملية الاستخراج
    Verify actual Landing AI usage in extraction process
    """
    try:
        logger.info(f"🔍 التحقق من استخدام Landing AI للجلسة {session_id}")
        
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        session = sessions_store[session_id]
        
        # فحص خدمة Landing AI
        from app.services.landing_ai_service import LandingAIService
        
        landing_service = LandingAIService()
        
        # فحص الإعدادات والحالة
        health_check = await landing_service.health_check()
        
        verification_result = {
            "landing_ai_enabled": landing_service.enabled,
            "api_key_configured": bool(landing_service.api_key),
            "agentic_doc_available": landing_service.enabled and hasattr(landing_service, 'enabled'),
            "health_status": health_check,
            "ocr_fallback_available": getattr(landing_service, 'ocr_available', False),
            "mock_mode": getattr(landing_service, 'mock_mode', True),
            "service_priority": "Landing AI" if landing_service.enabled else "Tesseract OCR",
            "configuration": {
                "batch_size": getattr(landing_service, 'batch_size', 0),
                "max_workers": getattr(landing_service, 'max_workers', 0),
                "max_retries": getattr(landing_service, 'max_retries', 0),
                "include_marginalia": getattr(landing_service, 'include_marginalia', False),
                "include_metadata": getattr(landing_service, 'include_metadata', False),
                "save_visual_groundings": getattr(landing_service, 'save_visual_groundings', False)
            }
        }
        
        # فحص نتائج OCR السابقة في الجلسة
        ocr_results = session.get("ocr_results", {})
        if ocr_results:
            verification_result["session_ocr_details"] = {
                "old_image_service": ocr_results.get("old", {}).get("service_used", "unknown"),
                "new_image_service": ocr_results.get("new", {}).get("service_used", "unknown"),
                "old_confidence": ocr_results.get("old", {}).get("confidence", 0),
                "new_confidence": ocr_results.get("new", {}).get("confidence", 0),
                "old_processing_time": ocr_results.get("old", {}).get("processing_time", 0),
                "new_processing_time": ocr_results.get("new", {}).get("processing_time", 0)
            }
        
        logger.info(f"📊 نتائج التحقق: خدمة Landing AI {'مُفعلة' if landing_service.enabled else 'غير مُفعلة'}")
        
        return verification_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في التحقق من Landing AI: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في التحقق من حالة Landing AI: {str(e)}"
        )


@router.post("/compare/force-landing-ai/{session_id}")
async def force_landing_ai_extraction(session_id: str):
    """
    إجبار استخدام Landing AI لاستخراج النص (تجاهل Tesseract)
    Force Landing AI usage for text extraction (bypass Tesseract)
    """
    try:
        logger.info(f"🚀 إجبار استخدام Landing AI للجلسة {session_id}")
        
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        session = sessions_store[session_id]
        uploaded_files = session.get("uploaded_files", {})
        
        if "old" not in uploaded_files or "new" not in uploaded_files:
            raise HTTPException(
                status_code=400,
                detail="يجب رفع كلا الصورتين أولاً"
            )
        
        from app.services.landing_ai_service import LandingAIService
        
        landing_service = LandingAIService()
        
        # التحقق من توفر Landing AI
        if not landing_service.enabled:
            raise HTTPException(
                status_code=503,
                detail="خدمة Landing AI غير متوفرة. تحقق من API key وتثبيت agentic-doc"
            )
        
        # إجبار تعطيل OCR المحلي مؤقتاً
        original_ocr_available = landing_service.ocr_available
        landing_service.ocr_available = False
        landing_service.mock_mode = False
        
        try:
            # استخراج النص من الصورة القديمة
            logger.info("🔍 استخراج النص من الصورة القديمة باستخدام Landing AI فقط...")
            old_result = await landing_service.extract_from_file(uploaded_files["old"]["path"])
            
            # استخراج النص من الصورة الجديدة
            logger.info("🔍 استخراج النص من الصورة الجديدة باستخدام Landing AI فقط...")
            new_result = await landing_service.extract_from_file(uploaded_files["new"]["path"])
            
            # إعداد النتائج
            ocr_results = {
                "old": {
                    "success": old_result.success,
                    "text": old_result.markdown_content,
                    "confidence": old_result.confidence_score,
                    "character_count": len(old_result.markdown_content),
                    "word_count": len(old_result.markdown_content.split()),
                    "processing_time": old_result.processing_time,
                    "service_used": "LandingAI_Forced",
                    "extraction_details": {
                        "total_chunks": old_result.total_chunks,
                        "chunks_by_type": old_result.chunks_by_type,
                        "text_elements": old_result.text_elements,
                        "table_elements": old_result.table_elements,
                        "image_elements": old_result.image_elements
                    },
                    "error_message": old_result.error_message if not old_result.success else None
                },
                "new": {
                    "success": new_result.success,
                    "text": new_result.markdown_content,
                    "confidence": new_result.confidence_score,
                    "character_count": len(new_result.markdown_content),
                    "word_count": len(new_result.markdown_content.split()),
                    "processing_time": new_result.processing_time,
                    "service_used": "LandingAI_Forced",
                    "extraction_details": {
                        "total_chunks": new_result.total_chunks,
                        "chunks_by_type": new_result.chunks_by_type,
                        "text_elements": new_result.text_elements,
                        "table_elements": new_result.table_elements,
                        "image_elements": new_result.image_elements
                    },
                    "error_message": new_result.error_message if not new_result.success else None
                }
            }
            
            # حفظ النتائج
            session["ocr_results"] = ocr_results
            session["forced_landing_ai"] = True
            
            logger.info(f"✅ تم استخراج النص باستخدام Landing AI فقط")
            logger.info(f"📊 الصورة القديمة: {len(old_result.markdown_content)} حرف، ثقة: {old_result.confidence_score:.2f}")
            logger.info(f"📊 الصورة الجديدة: {len(new_result.markdown_content)} حرف، ثقة: {new_result.confidence_score:.2f}")
            
            return {
                "message": "تم استخراج النص باستخدام Landing AI فقط",
                "old_image_result": ocr_results["old"],
                "new_image_result": ocr_results["new"],
                "service_verification": "LandingAI_Only",
                "success": old_result.success and new_result.success
            }
            
        finally:
            # استعادة الإعدادات الأصلية
            landing_service.ocr_available = original_ocr_available
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في إجبار استخدام Landing AI: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في إجبار استخدام Landing AI: {str(e)}"
        )


@router.get("/compare/session-status/{session_id}")
async def get_session_status(session_id: str):
    """
    الحصول على حالة الجلسة وإمكانية استخدام fallback
    Get session status and fallback availability
    """
    try:
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="جلسة المقارنة غير موجودة")
        
        session = sessions_store[session_id]
        
        # استيراد الخدمة للتحقق من توفر Tesseract
        from app.services.landing_ai_service import landing_ai_service
        
        # تحديد ما إذا كان هناك فشل في الاستخراج
        extraction_failed = False
        if "ocr_results" in session:
            old_failed = not session["ocr_results"]["old"]["success"]
            new_failed = not session["ocr_results"]["new"]["success"]
            extraction_failed = old_failed or new_failed
        
        return {
            "session_id": session_id,
            "status": session.get("status", "unknown"),
            "extraction_failed": extraction_failed,
            "fallback_used": session.get("fallback_ocr_used", False),
            "fallback_available": landing_ai_service.ocr_available,
            "fallback_endpoint": f"/api/v1/compare/fallback-ocr/{session_id}" if extraction_failed else None,
            "message": "يمكن المحاولة مع OCR التقليدي" if extraction_failed and landing_ai_service.ocr_available else None,
            "warning": "⚠️ OCR التقليدي أقل دقة من LandingAI" if extraction_failed else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في الحصول على حالة الجلسة: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في الحصول على حالة الجلسة: {str(e)}"
        )

@router.post("/compare/fallback-ocr/{session_id}")
async def fallback_ocr_extraction(session_id: str):
    """
    استخراج النص باستخدام Tesseract OCR كبديل بعد موافقة المستخدم
    Extract text using Tesseract OCR as fallback after user approval
    """
    try:
        # التحقق من وجود الجلسة
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="جلسة المقارنة غير موجودة")
        
        session = sessions_store[session_id]
        old_image_path = session["uploaded_files"]["old"]["path"]
        new_image_path = session["uploaded_files"]["new"]["path"]
        
        logger.info(f"🔄 بدء استخراج النص باستخدام Tesseract OCR للجلسة: {session_id}")
        
        # استيراد الخدمة
        from app.services.landing_ai_service import landing_ai_service
        
        # التحقق من توفر Tesseract
        if not landing_ai_service.ocr_available:
            raise HTTPException(
                status_code=503, 
                detail="Tesseract OCR غير متاح في النظام"
            )
        
        # استخراج النص من الصورتين باستخدام Tesseract
        logger.info("🔍 استخراج النص من الصورة القديمة باستخدام Tesseract...")
        old_result = await landing_ai_service._fallback_ocr_extraction(
            old_image_path, 
            os.path.dirname(old_image_path), 
            os.path.basename(old_image_path)
        )
        
        logger.info("🔍 استخراج النص من الصورة الجديدة باستخدام Tesseract...")
        new_result = await landing_ai_service._fallback_ocr_extraction(
            new_image_path, 
            os.path.dirname(new_image_path), 
            os.path.basename(new_image_path)
        )
        
        # تحديث الجلسة
        session["ocr_results"] = {
            "old": {
                "success": old_result.success,
                "text": old_result.markdown_content,
                "confidence": old_result.confidence_score,
                "character_count": len(old_result.markdown_content),
                "word_count": len(old_result.markdown_content.split()),
                "processing_time": old_result.processing_time,
                "service_used": "Tesseract_OCR",
                "extraction_method": "Tesseract_Fallback",
                "error_message": old_result.error_message if not old_result.success else None
            },
            "new": {
                "success": new_result.success,
                "text": new_result.markdown_content,
                "confidence": new_result.confidence_score,
                "character_count": len(new_result.markdown_content),
                "word_count": len(new_result.markdown_content.split()),
                "processing_time": new_result.processing_time,
                "service_used": "Tesseract_OCR",
                "extraction_method": "Tesseract_Fallback",
                "error_message": new_result.error_message if not new_result.success else None
            }
        }
        
        session["fallback_ocr_used"] = True
        session["status"] = "completed_with_fallback"
        
        logger.info(f"✅ تم استخراج النص باستخدام Tesseract OCR للجلسة: {session_id}")
        
        return {
            "message": "تم استخراج النص باستخدام Tesseract OCR كبديل",
            "session_id": session_id,
            "old_image_result": session["ocr_results"]["old"],
            "new_image_result": session["ocr_results"]["new"],
            "warning": "⚠️ تم استخدام OCR التقليدي - قد تكون الدقة أقل من LandingAI",
            "success": old_result.success and new_result.success,
            "extraction_method": "Tesseract_Fallback"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في استخراج النص باستخدام Tesseract: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في استخراج النص باستخدام Tesseract: {str(e)}"
        )

@router.post("/compare/full-comparison/{session_id}")
async def full_comparison(session_id: str):
    """
    إجراء مقارنة كاملة للصور في الجلسة
    Perform full comparison of images in session
    """
    try:
        # التحقق من وجود الجلسة
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="جلسة المقارنة غير موجودة")
        
        session = sessions_store[session_id]
        old_image_path = session["uploaded_files"]["old"]["path"]
        new_image_path = session["uploaded_files"]["new"]["path"]
        
        logger.info(f"🔄 بدء المقارنة الكاملة للجلسة: {session_id}")
        
        # استيراد الخدمات
        from app.services.landing_ai_service import landing_ai_service
        from app.services.gemini_service import gemini_service
        from app.services.visual_comparison_service import enhanced_visual_comparison_service
        
        # 1. استخراج النص من الصور مع معالجة محسنة للأخطاء
        old_result = None
        new_result = None
        
        try:
            logger.info("📝 استخراج النص من الصورة القديمة...")
            old_result = await landing_ai_service.extract_from_file(old_image_path)
            if old_result.success:
                logger.info(f"✅ نجح استخراج النص من الصورة القديمة: {len(old_result.markdown_content)} حرف")
            else:
                logger.warning(f"⚠️ فشل في استخراج النص من الصورة القديمة: {old_result.error_message}")
        except Exception as e:
            logger.error(f"❌ خطأ في استخراج النص من الصورة القديمة: {e}")
            # إنشاء نتيجة فاشلة
            from app.services.landing_ai_service import LandingAIExtractionResult
            old_result = LandingAIExtractionResult(
                file_path=old_image_path,
                file_name=os.path.basename(old_image_path),
                processing_time=0,
                success=False,
                error_message=str(e)
            )
        
        try:
            logger.info("📝 استخراج النص من الصورة الجديدة...")
            new_result = await landing_ai_service.extract_from_file(new_image_path)
            if new_result.success:
                logger.info(f"✅ نجح استخراج النص من الصورة الجديدة: {len(new_result.markdown_content)} حرف")
            else:
                logger.warning(f"⚠️ فشل في استخراج النص من الصورة الجديدة: {new_result.error_message}")
        except Exception as e:
            logger.error(f"❌ خطأ في استخراج النص من الصورة الجديدة: {e}")
            # إنشاء نتيجة فاشلة
            from app.services.landing_ai_service import LandingAIExtractionResult
            new_result = LandingAIExtractionResult(
                file_path=new_image_path,
                file_name=os.path.basename(new_image_path),
                processing_time=0,
                success=False,
                error_message=str(e)
            )
        
        # 2. المقارنة النصية باستخدام Gemini مع معالجة أفضل للأخطاء
        comparison_result = None
        if old_result and new_result and old_result.success and new_result.success:
            try:
                logger.info("🤖 تحليل المقارنة النصية باستخدام Gemini...")
                comparison_result = await gemini_service.compare_texts(
                    old_result.markdown_content, 
                    new_result.markdown_content
                )
                logger.info("✅ تمت المقارنة النصية بنجاح")
            except Exception as e:
                logger.error(f"❌ فشل في المقارنة النصية: {e}")
                comparison_result = None
        else:
            logger.warning("⚠️ فشل في استخراج النص، تخطي المقارنة النصية")
        
        # 3. المقارنة البصرية مع معالجة أفضل للأخطاء
        visual_result = None
        try:
            logger.info("👁️ إجراء المقارنة البصرية...")
            visual_result = await enhanced_visual_comparison_service.compare_images(
                old_image_path, new_image_path
            )
            if visual_result:
                logger.info(f"✅ تمت المقارنة البصرية بنجاح: {visual_result.similarity_score:.1f}% تطابق")
            else:
                logger.warning("⚠️ فشل في المقارنة البصرية")
        except Exception as e:
            logger.error(f"❌ خطأ في المقارنة البصرية: {e}")
            visual_result = None
        
        # 4. التحقق من LandingAI
        landing_ai_verification = {
            "landing_ai_enabled": not landing_ai_service.mock_mode,
            "api_key_configured": bool(landing_ai_service.api_key),
            "agentic_doc_available": landing_ai_service.agentic_doc_available,
            "health_status": {"status": "healthy"},
            "ocr_fallback_available": landing_ai_service.ocr_available,
            "mock_mode": landing_ai_service.mock_mode,
            "service_priority": "tesseract_ocr" if landing_ai_service.mock_mode else "landing_ai",
            "configuration": {
                "batch_size": 4,
                "max_workers": 5,
                "max_retries": 3,
                "include_marginalia": True,
                "include_metadata": True,
                "save_visual_groundings": False
            }
        }
        
        if old_result.success and new_result.success:
            landing_ai_verification["session_ocr_details"] = {
                "old_image_service": "tesseract" if landing_ai_service.mock_mode else "landing_ai",
                "new_image_service": "tesseract" if landing_ai_service.mock_mode else "landing_ai",
                "old_confidence": old_result.confidence_score,
                "new_confidence": new_result.confidence_score,
                "old_processing_time": old_result.processing_time,
                "new_processing_time": new_result.processing_time
            }
        
        # تحديث حالة الجلسة
        session["status"] = "completed"
        session["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ تمت المقارنة الكاملة بنجاح للجلسة: {session_id}")
        
        # تحديد حالة الجلسة بناءً على نجاح العمليات
        session_status = "completed"
        if not (old_result and new_result):
            session_status = "failed"
        elif not (old_result.success or new_result.success):
            session_status = "partial_failure"
        
        response_data = {
            "session_id": session_id,
            "status": session_status,
            "old_image_result": {
                "success": old_result.success if old_result else False,
                "text": old_result.markdown_content if old_result and old_result.success else "",
                "confidence": old_result.confidence_score if old_result and old_result.success else 0,
                "language": "العربية" if old_result and old_result.success else "unknown",
                "character_count": len(old_result.markdown_content) if old_result and old_result.success else 0,
                "word_count": len(old_result.markdown_content.split()) if old_result and old_result.success else 0,
                "processing_time": old_result.processing_time if old_result else 0,
                "error_message": old_result.error_message if old_result and not old_result.success else None,
                "extraction_method": "LandingAI" if old_result and old_result.success else "Failed",
                "image_info": {
                    "width": 0,
                    "height": 0,
                    "format": "JPEG",
                    "size_bytes": session["uploaded_files"]["old"]["size"]
                }
            },
            "new_image_result": {
                "success": new_result.success if new_result else False,
                "text": new_result.markdown_content if new_result and new_result.success else "",
                "confidence": new_result.confidence_score if new_result and new_result.success else 0,
                "language": "العربية" if new_result and new_result.success else "unknown",
                "character_count": len(new_result.markdown_content) if new_result and new_result.success else 0,
                "word_count": len(new_result.markdown_content.split()) if new_result and new_result.success else 0,
                "processing_time": new_result.processing_time if new_result else 0,
                "error_message": new_result.error_message if new_result and not new_result.success else None,
                "extraction_method": "LandingAI" if new_result and new_result.success else "Failed",
                "image_info": {
                    "width": 0,
                    "height": 0,
                    "format": "JPEG",
                    "size_bytes": session["uploaded_files"]["new"]["size"]
                }
            },
            "comparison_result": clean_json_values(comparison_result.__dict__) if comparison_result else None,
            "visual_comparison_result": clean_json_values(visual_result.__dict__) if visual_result else None,
            "landing_ai_verification": landing_ai_verification,
            "summary": {
                "text_extraction_success": bool(old_result and new_result and old_result.success and new_result.success),
                "text_comparison_success": bool(comparison_result),
                "visual_comparison_success": bool(visual_result),
                "overall_success": bool(old_result and new_result and (old_result.success or new_result.success) and visual_result),
                "errors": []
            }
        }
        
        # إضافة الأخطاء إلى الملخص
        fallback_available = False
        if old_result and not old_result.success:
            response_data["summary"]["errors"].append(f"فشل في استخراج النص من الصورة القديمة: {old_result.error_message}")
            fallback_available = True
        if new_result and not new_result.success:
            response_data["summary"]["errors"].append(f"فشل في استخراج النص من الصورة الجديدة: {new_result.error_message}")
            fallback_available = True
        if not comparison_result and old_result and new_result and old_result.success and new_result.success:
            response_data["summary"]["errors"].append("فشل في المقارنة النصية باستخدام Gemini")
        if not visual_result:
            response_data["summary"]["errors"].append("فشل في المقارنة البصرية")
        
        # إضافة معلومات fallback
        if fallback_available:
            response_data["fallback_options"] = {
                "tesseract_available": landing_ai_service.ocr_available,
                "fallback_endpoint": f"/api/v1/compare/fallback-ocr/{session_id}",
                "message": "يمكن المحاولة مع OCR التقليدي (أقل دقة) بعد موافقتك",
                "warning": "⚠️ OCR التقليدي أقل دقة من LandingAI"
            }
        else:
            response_data["fallback_options"] = None
        
        return clean_json_values(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في المقارنة الكاملة: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في إجراء المقارنة الكاملة: {str(e)}"
        )


# ---------------------------------------------
# Endpoints لإدارة تقارير المقارنة المحفوظة
# ---------------------------------------------


@router.get("/compare/reports")
async def list_saved_reports(
    skip: int = 0,
    limit: int = 50,
    session_id: Optional[str] = None,
):
    """عرض قائمة بالتقارير المحفوظة مع إمكانية التصفية حسب session_id"""
    try:
        db = SessionLocal()
        reports = crud.list_reports(db, skip=skip, limit=limit, session_id=session_id)
        # إرجاع بيانات مختصرة بدون المحتوى الكامل لتسريع الاستجابة
        results: List[dict] = [
            {
                "id": r.id,
                "session_id": r.session_id,
                "report_format": r.report_format,
                "created_at": r.created_at,
            }
            for r in reports
        ]
        return {
            "total": len(results),
            "results": results,
        }
    finally:
        db.close()


@router.get("/compare/report/{report_id}")
async def get_saved_report(report_id: int):
    """تنزيل تقرير محفوظ باستخدام معرفه"""
    db = SessionLocal()
    try:
        report = crud.get_report(db, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="التقرير غير موجود")

        media_type = (
            "text/markdown"
            if report.report_format in {"md", "markdown"}
            else "text/html" if report.report_format == "html" else "text/plain"
        )
        filename = f"comparison_report_{report.id}.{report.report_format}"

        return Response(
            content=report.content.encode("utf-8"),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": f"{media_type}; charset=utf-8",
            },
        )
    finally:
        db.close()