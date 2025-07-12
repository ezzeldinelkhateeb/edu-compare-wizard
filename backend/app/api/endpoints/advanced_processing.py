"""
Advanced Processing API Endpoints
نقاط نهاية المعالجة المتقدمة
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Dict, Any, List, Optional
import uuid
import os
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

from app.core.config import get_settings
from app.services.landing_ai_service import LandingAIService
from app.services.gemini_service import GeminiService
from app.models.schemas import (
    ProcessingSessionRequest, ProcessingSessionResponse,
    ProcessingStep, ProcessingResult, ComparisonResult
)

settings = get_settings()
router = APIRouter()

# تخزين مؤقت لجلسات المعالجة
processing_sessions = {}

class AdvancedProcessingSession:
    """جلسة معالجة متقدمة"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.status = "initializing"
        self.progress = 0
        self.current_step = "إنشاء الجلسة"
        self.processing_steps = [
            ProcessingStep(
                id="init",
                name="إنشاء الجلسة",
                status="processing",
                progress=10
            ),
            ProcessingStep(
                id="upload",
                name="رفع الملفات",
                status="pending",
                progress=0
            ),
            ProcessingStep(
                id="ocr_old",
                name="OCR - الكتاب القديم",
                status="pending",
                progress=0,
                max_attempts=4
            ),
            ProcessingStep(
                id="ocr_new", 
                name="OCR - الكتاب الجديد",
                status="pending",
                progress=0,
                max_attempts=4
            ),
            ProcessingStep(
                id="ai_comparison",
                name="مقارنة AI",
                status="pending",
                progress=0
            ),
            ProcessingStep(
                id="report_generation",
                name="إنشاء التقرير",
                status="pending",
                progress=0
            )
        ]
        self.old_files = []
        self.new_files = []
        self.processing_results = []
        self.comparison_results = []
        self.logs = []
        self.session_dir = None
        
    def add_log(self, message: str, level: str = "info"):
        """إضافة سجل جديد"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        
        # طباعة في وحدة التحكم أيضاً
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
    
    def update_step(self, step_id: str, **updates):
        """تحديث خطوة معالجة"""
        for step in self.processing_steps:
            if step.id == step_id:
                for key, value in updates.items():
                    setattr(step, key, value)
                break
        
        # حساب التقدم الإجمالي
        completed_steps = sum(1 for step in self.processing_steps if step.status == "completed")
        total_steps = len(self.processing_steps)
        self.progress = (completed_steps / total_steps) * 100
    
    def get_status(self) -> Dict[str, Any]:
        """الحصول على حالة الجلسة"""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "processing_steps": [step.model_dump() for step in self.processing_steps],
            "old_files_count": len(self.old_files),
            "new_files_count": len(self.new_files),
            "processing_results_count": len(self.processing_results),
            "comparison_results_count": len(self.comparison_results),
            "logs": self.logs[-20:],  # آخر 20 سجل
            "created_at": self.created_at.isoformat(),
            "updated_at": datetime.now().isoformat()
        }


@router.post("/advanced-processing/create-session", response_model=ProcessingSessionResponse)
async def create_processing_session(request: ProcessingSessionRequest):
    """
    إنشاء جلسة معالجة متقدمة جديدة
    Create new advanced processing session
    """
    try:
        session_id = str(uuid.uuid4())
        session = AdvancedProcessingSession(session_id)
        
        # إنشاء مجلد الجلسة
        session_dir = os.path.join(settings.UPLOAD_DIR, "advanced_sessions", session_id)
        os.makedirs(session_dir, exist_ok=True)
        session.session_dir = session_dir
        
        # حفظ الجلسة
        processing_sessions[session_id] = session
        
        session.add_log(f"🚀 تم إنشاء جلسة معالجة متقدمة: {session_id}")
        session.update_step("init", status="completed", progress=100)
        session.current_step = "انتظار رفع الملفات"
        session.status = "waiting_for_files"
        
        logger.info(f"✅ تم إنشاء جلسة معالجة متقدمة: {session_id}")
        
        return ProcessingSessionResponse(
            session_id=session_id,
            status="created",
            message="تم إنشاء جلسة المعالجة المتقدمة بنجاح"
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء جلسة المعالجة: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في إنشاء جلسة المعالجة: {str(e)}"
        )


@router.post("/advanced-processing/{session_id}/upload-files")
async def upload_files_to_session(
    session_id: str,
    old_files: List[UploadFile] = File(...),
    new_files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    رفع الملفات إلى جلسة المعالجة
    Upload files to processing session
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    
    session = processing_sessions[session_id]
    
    try:
        session.add_log("📤 بدء رفع الملفات...")
        session.update_step("upload", status="processing", progress=20)
        
        # إنشاء مجلدات للملفات
        old_files_dir = os.path.join(session.session_dir, "old_files")
        new_files_dir = os.path.join(session.session_dir, "new_files")
        os.makedirs(old_files_dir, exist_ok=True)
        os.makedirs(new_files_dir, exist_ok=True)
        
        # حفظ الملفات القديمة
        for i, file in enumerate(old_files):
            file_path = os.path.join(old_files_dir, f"{i}_{file.filename}")
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            session.old_files.append({
                "id": f"old_{i}",
                "filename": file.filename,
                "path": file_path,
                "size": len(content),
                "uploaded_at": datetime.now().isoformat()
            })
            
            session.add_log(f"📁 تم رفع الملف القديم: {file.filename}")
        
        # حفظ الملفات الجديدة
        for i, file in enumerate(new_files):
            file_path = os.path.join(new_files_dir, f"{i}_{file.filename}")
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            session.new_files.append({
                "id": f"new_{i}",
                "filename": file.filename,
                "path": file_path,
                "size": len(content),
                "uploaded_at": datetime.now().isoformat()
            })
            
            session.add_log(f"📁 تم رفع الملف الجديد: {file.filename}")
        
        session.update_step("upload", status="completed", progress=100)
        session.current_step = "بدء معالجة OCR"
        session.status = "files_uploaded"
        
        session.add_log(f"✅ تم رفع {len(old_files)} ملف قديم و {len(new_files)} ملف جديد")
        
        # بدء المعالجة في الخلفية
        if background_tasks:
            background_tasks.add_task(process_files_background, session_id)
        
        return {
            "session_id": session_id,
            "status": "files_uploaded",
            "old_files_count": len(old_files),
            "new_files_count": len(new_files),
            "message": "تم رفع الملفات بنجاح وبدء المعالجة"
        }
        
    except Exception as e:
        session.add_log(f"❌ خطأ في رفع الملفات: {str(e)}", "error")
        session.update_step("upload", status="error")
        session.status = "error"
        raise HTTPException(
            status_code=500,
            detail=f"فشل في رفع الملفات: {str(e)}"
        )


async def process_files_background(session_id: str):
    """معالجة الملفات في الخلفية"""
    session = processing_sessions[session_id]
    
    try:
        session.add_log("🔍 بدء معالجة OCR للملفات...")
        session.status = "processing"
        
        # إنشاء خدمات المعالجة
        landing_service = LandingAIService()
        gemini_service = GeminiService()
        
        # معالجة الملفات القديمة
        session.add_log("📄 معالجة الكتاب القديم...")
        session.update_step("ocr_old", status="processing", progress=10)
        
        for i, file_info in enumerate(session.old_files):
            session.add_log(f"🔍 معالجة الملف القديم {i+1}: {file_info['filename']}")
            session.update_step("ocr_old", attempts=i+1, details=f"معالجة {file_info['filename']}")
            
            try:
                result = await landing_service.extract_from_file(
                    file_info['path'],
                    os.path.join(session.session_dir, "ocr_results")
                )
                
                processing_result = {
                    "id": file_info['id'],
                    "filename": file_info['filename'],
                    "status": "completed" if result.success else "error",
                    "confidence": result.confidence_score,
                    "text_length": len(result.markdown_content),
                    "word_count": result.text_elements,
                    "processing_time": result.processing_time,
                    "language": "ara" if result.success else "unknown",
                    "extracted_text": result.markdown_content,
                    "structured_analysis": result.structured_analysis.model_dump() if result.structured_analysis else None
                }
                
                session.processing_results.append(processing_result)
                session.add_log(f"✅ اكتمل الملف القديم {i+1}: ثقة {result.confidence_score:.1%}")
                
            except Exception as e:
                session.add_log(f"❌ فشل في معالجة الملف القديم {i+1}: {str(e)}", "error")
        
        session.update_step("ocr_old", status="completed", progress=100)
        
        # معالجة الملفات الجديدة
        session.add_log("📄 معالجة الكتاب الجديد...")
        session.update_step("ocr_new", status="processing", progress=10)
        
        for i, file_info in enumerate(session.new_files):
            session.add_log(f"🔍 معالجة الملف الجديد {i+1}: {file_info['filename']}")
            session.update_step("ocr_new", attempts=i+1, details=f"معالجة {file_info['filename']}")
            
            try:
                result = await landing_service.extract_from_file(
                    file_info['path'],
                    os.path.join(session.session_dir, "ocr_results")
                )
                
                processing_result = {
                    "id": file_info['id'],
                    "filename": file_info['filename'],
                    "status": "completed" if result.success else "error",
                    "confidence": result.confidence_score,
                    "text_length": len(result.markdown_content),
                    "word_count": result.text_elements,
                    "processing_time": result.processing_time,
                    "language": "ara" if result.success else "unknown",
                    "extracted_text": result.markdown_content,
                    "structured_analysis": result.structured_analysis.model_dump() if result.structured_analysis else None
                }
                
                session.processing_results.append(processing_result)
                session.add_log(f"✅ اكتمل الملف الجديد {i+1}: ثقة {result.confidence_score:.1%}")
                
            except Exception as e:
                session.add_log(f"❌ فشل في معالجة الملف الجديد {i+1}: {str(e)}", "error")
        
        session.update_step("ocr_new", status="completed", progress=100)
        
        # مقارنة الملفات
        session.add_log("🤖 بدء مقارنة الملفات باستخدام AI...")
        session.update_step("ai_comparison", status="processing", progress=20)
        
        old_results = [r for r in session.processing_results if r['id'].startswith('old_')]
        new_results = [r for r in session.processing_results if r['id'].startswith('new_')]
        
        for i, (old_result, new_result) in enumerate(zip(old_results, new_results)):
            if old_result['status'] == 'completed' and new_result['status'] == 'completed':
                session.add_log(f"🔄 مقارنة {old_result['filename']} مع {new_result['filename']}")
                
                try:
                    comparison = await gemini_service.compare_texts(
                        old_result['extracted_text'],
                        new_result['extracted_text']
                    )
                    
                    comparison_result = {
                        "id": f"comparison_{i}",
                        "old_file_id": old_result['id'],
                        "new_file_id": new_result['id'],
                        "similarity": comparison.similarity_percentage,
                        "confidence": comparison.confidence_score,
                        "processing_time": comparison.processing_time,
                        "changes": comparison.content_changes,
                        "summary": comparison.summary,
                        "recommendation": comparison.recommendation,
                        "detailed_analysis": comparison.detailed_analysis,
                        "status": "completed"
                    }
                    
                    session.comparison_results.append(comparison_result)
                    session.add_log(f"✅ اكتملت المقارنة: تشابه {comparison.similarity_percentage}%")
                    
                except Exception as e:
                    session.add_log(f"❌ فشل في المقارنة: {str(e)}", "error")
        
        session.update_step("ai_comparison", status="completed", progress=100)
        
        # إنشاء التقرير النهائي
        session.add_log("📊 إنشاء التقرير النهائي...")
        session.update_step("report_generation", status="processing", progress=50)
        
        # حفظ التقرير النهائي
        report_path = os.path.join(session.session_dir, "final_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "session_info": {
                    "session_id": session_id,
                    "created_at": session.created_at.isoformat(),
                    "completed_at": datetime.now().isoformat()
                },
                "processing_results": session.processing_results,
                "comparison_results": session.comparison_results,
                "logs": session.logs
            }, f, ensure_ascii=False, indent=2)
        
        session.update_step("report_generation", status="completed", progress=100)
        session.status = "completed"
        session.current_step = "اكتملت المعالجة"
        session.add_log("🎉 اكتملت جميع خطوات المعالجة بنجاح!")
        
    except Exception as e:
        session.add_log(f"❌ خطأ في المعالجة: {str(e)}", "error")
        session.status = "error"
        logger.error(f"خطأ في معالجة الجلسة {session_id}: {e}")


@router.get("/advanced-processing/{session_id}/status")
async def get_processing_status(session_id: str):
    """
    الحصول على حالة جلسة المعالجة
    Get processing session status
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    
    session = processing_sessions[session_id]
    return session.get_status()


@router.get("/advanced-processing/{session_id}/results")
async def get_processing_results(session_id: str):
    """
    الحصول على نتائج المعالجة الكاملة
    Get complete processing results
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    
    session = processing_sessions[session_id]
    
    if session.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="المعالجة لم تكتمل بعد"
        )
    
    return {
        "session_id": session_id,
        "status": session.status,
        "processing_results": session.processing_results,
        "comparison_results": session.comparison_results,
        "statistics": {
            "total_files": len(session.old_files) + len(session.new_files),
            "completed_files": len([r for r in session.processing_results if r['status'] == 'completed']),
            "average_confidence": sum(r['confidence'] for r in session.processing_results if r['status'] == 'completed') / len([r for r in session.processing_results if r['status'] == 'completed']) if session.processing_results else 0,
            "total_processing_time": sum(r['processing_time'] for r in session.processing_results if r['status'] == 'completed'),
            "completed_comparisons": len([c for c in session.comparison_results if c['status'] == 'completed'])
        },
        "logs": session.logs
    }


@router.delete("/advanced-processing/{session_id}")
async def delete_processing_session(session_id: str):
    """
    حذف جلسة المعالجة
    Delete processing session
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    
    session = processing_sessions[session_id]
    
    # حذف ملفات الجلسة
    if session.session_dir and os.path.exists(session.session_dir):
        import shutil
        shutil.rmtree(session.session_dir)
    
    # حذف الجلسة من الذاكرة
    del processing_sessions[session_id]
    
    logger.info(f"🗑️ تم حذف جلسة المعالجة: {session_id}")
    
    return {
        "session_id": session_id,
        "status": "deleted",
        "message": "تم حذف الجلسة بنجاح"
    }


@router.get("/advanced-processing/sessions")
async def list_all_sessions():
    """
    عرض جميع جلسات المعالجة
    List all processing sessions
    """
    sessions_info = []
    
    for session_id, session in processing_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "status": session.status,
            "progress": session.progress,
            "created_at": session.created_at.isoformat(),
            "files_count": len(session.old_files) + len(session.new_files),
            "results_count": len(session.processing_results)
        })
    
    return {
        "total_sessions": len(sessions_info),
        "sessions": sessions_info
    } 