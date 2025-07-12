"""
Advanced Processing API Endpoints
نقاط نهاية المعالجة المتقدمة
"""

import os
import asyncio
import aiofiles
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from datetime import datetime
import logging
import re
import uuid
import zipfile
import tempfile
from dataclasses import dataclass, asdict
from loguru import logger

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from starlette.responses import Response

from app.core.config import get_settings
from app.services.landing_ai_service import LandingAIService
from app.services.gemini_service import GeminiService
from app.services.enhanced_report_service import EnhancedReportService, ReportData
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
        
        # حساب التقدم الإجمالي بطريقة أكثر دقة
        total_progress = 0
        total_steps = len(self.processing_steps)
        
        for step in self.processing_steps:
            if step.status == "completed":
                total_progress += 100
            elif step.status == "processing":
                # استخدم تقدم الخطوة الحالية
                total_progress += max(step.progress, 10)  # حد أدنى 10% للخطوات قيد المعالجة
            elif step.status == "pending":
                total_progress += 0
            elif step.status == "error":
                total_progress += 0
        
        self.progress = min(total_progress / total_steps, 100)  # تأكد من عدم تجاوز 100%
    
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


def sanitize_filename(filename: str) -> str:
    """تنظيف اسم الملف من الأحرف غير المسموحة"""
    # إزالة الأحرف غير المسموحة (بما في ذلك الشرطة المائلة)
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # إزالة المسافات المتعددة والاستبدال بـ _
    sanitized = re.sub(r'\s+', '_', sanitized)
    # إزالة النقاط المتعددة
    sanitized = re.sub(r'\.+', '.', sanitized)
    # إزالة الأحرف الخاصة الأخرى مع الحفاظ على الأحرف العربية والأرقام
    sanitized = re.sub(r'[^\w\-_\.\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', '_', sanitized)
    # التأكد من عدم البدء أو الانتهاء بنقطة أو مسافة
    sanitized = sanitized.strip('. _')
    # التأكد من وجود امتداد صالح
    if not sanitized:
        sanitized = "unnamed_file"
    return sanitized[:255]  # تحديد طول اسم الملف


async def _generate_comprehensive_batch_report(session: AdvancedProcessingSession, individual_reports: List[Dict]) -> Dict:
    """إنشاء تقرير شامل لجميع المقارنات في المجموعة"""
    
    successful_comparisons = [c for c in session.comparison_results if c['status'] == 'completed']
    failed_comparisons = [c for c in session.comparison_results if c['status'] != 'completed']
    
    average_similarity = 0
    if successful_comparisons:
        average_similarity = sum(c['similarity'] for c in successful_comparisons) / len(successful_comparisons)
    
    total_processing_time = sum(r['processing_time'] for r in session.processing_results if r['status'] == 'completed')
    
    # إنشاء تقرير HTML شامل
    html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير المقارنة الشاملة - {session.session_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 20px; margin-bottom: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; }}
        .stat-label {{ margin-top: 5px; opacity: 0.9; }}
        .comparison-grid {{ display: grid; gap: 20px; margin: 30px 0; }}
        .comparison-card {{ border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; background: #f9fafb; }}
        .similarity-bar {{ background: #e5e7eb; height: 20px; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .similarity-fill {{ background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981); height: 100%; transition: width 0.3s ease; }}
        .file-names {{ font-weight: bold; color: #374151; margin-bottom: 10px; }}
        .summary {{ background: white; padding: 15px; border-left: 4px solid #3b82f6; margin: 10px 0; }}
        .recommendation {{ background: #fef3c7; padding: 15px; border-left: 4px solid #f59e0b; margin: 10px 0; }}
        .error-notice {{ background: #fee2e2; color: #dc2626; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 تقرير المقارنة الشاملة</h1>
            <p>معرف الجلسة: {session.session_id}</p>
            <p>تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(successful_comparisons)}</div>
                <div class="stat-label">مقارنات ناجحة</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(failed_comparisons)}</div>
                <div class="stat-label">مقارنات فاشلة</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{average_similarity:.1f}%</div>
                <div class="stat-label">متوسط التشابه</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_processing_time:.1f}s</div>
                <div class="stat-label">وقت المعالجة الإجمالي</div>
            </div>
        </div>

        {_generate_quota_warning() if failed_comparisons else ''}

        <h2>📝 تفاصيل المقارنات</h2>
        <div class="comparison-grid">"""
    
    # إضافة تفاصيل كل مقارنة
    for i, comparison in enumerate(successful_comparisons):
        old_file = next((r for r in session.processing_results if r['id'] == comparison['old_file_id']), None)
        new_file = next((r for r in session.processing_results if r['id'] == comparison['new_file_id']), None)
        
        if old_file and new_file:
            html_content += f"""
            <div class="comparison-card">
                <div class="file-names">📄 {old_file['filename']} ← {new_file['filename']}</div>
                <div class="similarity-bar">
                    <div class="similarity-fill" style="width: {comparison['similarity']}%"></div>
                </div>
                <div style="text-align: center; font-weight: bold; margin: 10px 0;">
                    نسبة التشابه: {comparison['similarity']}%
                </div>
                <div class="summary">
                    <strong>الملخص:</strong> {comparison['summary']}
                </div>
                <div class="recommendation">
                    <strong>التوصية:</strong> {comparison['recommendation']}
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 15px; font-size: 0.9em; color: #6b7280;">
                    <div>⚡ ثقة: {comparison['confidence']*100:.1f}%</div>
                    <div>⏱️ وقت المعالجة: {comparison['processing_time']:.1f}s</div>
                    <div>📊 حالة: مكتملة</div>
                </div>
            </div>"""
    
    html_content += """
        </div>

        <div class="footer">
            <p>تم إنتاج هذا التقرير تلقائياً بواسطة نظام مقارن المناهج التعليمية</p>
            <p>استخدم Landing.AI للتعرف البصري | Google Gemini للتحليل الذكي</p>
        </div>
    </div>
</body>
</html>"""
    
    # حفظ التقرير الشامل
    comprehensive_html_path = os.path.join(session.session_dir, "comprehensive_report.html")
    with open(comprehensive_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return {
        "html_path": comprehensive_html_path,
        "individual_reports_count": len(individual_reports),
        "successful_comparisons": len(successful_comparisons),
        "failed_comparisons": len(failed_comparisons),
        "average_similarity": average_similarity,
        "total_processing_time": total_processing_time
    }


def _generate_quota_warning() -> str:
    """إنشاء تحذير خاص بحدود Gemini API"""
    return """
    <div class="error-notice">
        <h3>⚠️ تنبيه مهم</h3>
        <p>تم الوصول إلى الحد الأقصى اليومي لـ Gemini AI API (50 طلب/يوم للاشتراك المجاني).</p>
        <p>تم حساب التشابه الأساسي فقط. للحصول على تحليل متقدم مفصل، يُرجى:</p>
        <ul>
            <li>الانتظار حتى اليوم التالي لإعادة تعيين الحد</li>
            <li>أو الترقية إلى خطة Gemini API مدفوعة</li>
        </ul>
    </div>"""


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
        
        session.add_log(f"📁 إنشاء مجلد الملفات القديمة: {old_files_dir}")
        session.add_log(f"📁 إنشاء مجلد الملفات الجديدة: {new_files_dir}")
        
        os.makedirs(old_files_dir, exist_ok=True)
        os.makedirs(new_files_dir, exist_ok=True)
        
        session.add_log("✅ تم إنشاء المجلدات بنجاح")
        
        # حفظ الملفات القديمة
        for i, file in enumerate(old_files):
            sanitized_filename = sanitize_filename(file.filename)
            file_path = os.path.join(old_files_dir, f"{i}_{sanitized_filename}")
            
            session.add_log(f"📁 معالجة الملف القديم: {file.filename} -> {sanitized_filename}")
            session.add_log(f"📍 مسار الحفظ: {file_path}")
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            session.old_files.append({
                "id": f"old_{i}",
                "filename": file.filename,
                "sanitized_filename": sanitized_filename,
                "path": file_path,
                "size": len(content),
                "uploaded_at": datetime.now().isoformat()
            })
            
            session.add_log(f"📁 تم رفع الملف القديم: {file.filename}")
        
        # حفظ الملفات الجديدة
        for i, file in enumerate(new_files):
            sanitized_filename = sanitize_filename(file.filename)
            file_path = os.path.join(new_files_dir, f"{i}_{sanitized_filename}")
            
            session.add_log(f"📁 معالجة الملف الجديد: {file.filename} -> {sanitized_filename}")
            session.add_log(f"📍 مسار الحفظ: {file_path}")
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            session.new_files.append({
                "id": f"new_{i}",
                "filename": file.filename,
                "sanitized_filename": sanitized_filename,
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
        import traceback
        error_details = traceback.format_exc()
        session.add_log(f"❌ خطأ في رفع الملفات: {str(e)}", "error")
        session.add_log(f"🔍 تفاصيل الخطأ: {error_details}", "error")
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
        
        # ------- parallel OCR extraction for old files -------
        old_files_count = len(session.old_files)
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)
        completed_old = 0

        async def process_old_file(idx: int, file_info: dict):
            nonlocal completed_old
            async with semaphore:
                session.add_log(f"🔍 معالجة الملف القديم {idx+1}: {file_info['filename']}")
                session.update_step("ocr_old", attempts=idx+1, details=f"معالجة {file_info['filename']}")
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
                    session.add_log(f"✅ اكتمل الملف القديم {idx+1}: ثقة {result.confidence_score:.1%}")
                except Exception as e:
                    session.add_log(f"❌ فشل في معالجة الملف القديم {idx+1}: {str(e)}", "error")
                finally:
                    completed_old += 1
                    file_progress = 20 + (70 * completed_old / old_files_count)
                    session.update_step("ocr_old", progress=file_progress, details=f"معالجة {completed_old}/{old_files_count}")

        await asyncio.gather(*[process_old_file(i, fi) for i, fi in enumerate(session.old_files)])
        
        session.update_step("ocr_old", status="completed", progress=100)
        session.current_step = "اكتملت معالجة الملفات القديمة"
        
        # معالجة الملفات الجديدة
        session.add_log("📄 معالجة الكتاب الجديد...")
        session.update_step("ocr_new", status="processing", progress=10)
        
        # ------- parallel OCR extraction for new files -------
        new_files_count = len(session.new_files)
        completed_new = 0

        async def process_new_file(idx: int, file_info: dict):
            nonlocal completed_new
            async with semaphore:
                session.add_log(f"🔍 معالجة الملف الجديد {idx+1}: {file_info['filename']}")
                session.update_step("ocr_new", attempts=idx+1, details=f"معالجة {file_info['filename']}")
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
                    session.add_log(f"✅ اكتمل الملف الجديد {idx+1}: ثقة {result.confidence_score:.1%}")
                except Exception as e:
                    session.add_log(f"❌ فشل في معالجة الملف الجديد {idx+1}: {str(e)}", "error")
                finally:
                    completed_new += 1
                    file_progress = 20 + (70 * completed_new / new_files_count)
                    session.update_step("ocr_new", progress=file_progress, details=f"معالجة {completed_new}/{new_files_count}")

        await asyncio.gather(*[process_new_file(i, fi) for i, fi in enumerate(session.new_files)])
        
        session.update_step("ocr_new", status="completed", progress=100)
        session.current_step = "اكتملت معالجة الملفات الجديدة"
        
        # مقارنة الملفات
        session.add_log("�� بدء مقارنة الملفات باستخدام AI...")
        session.update_step("ai_comparison", status="processing", progress=20)
        session.current_step = "مقارنة الملفات باستخدام AI"
        
        old_results = [r for r in session.processing_results if r['id'].startswith('old_')]
        new_results = [r for r in session.processing_results if r['id'].startswith('new_')]
        
        total_comparisons = min(len(old_results), len(new_results))
        for i, (old_result, new_result) in enumerate(zip(old_results, new_results)):
            # تحديث التقدم بناءً على المقارنة الحالية
            comparison_progress = 30 + (60 * i / total_comparisons)  # من 30% إلى 90%
            session.update_step("ai_comparison", progress=comparison_progress)
            session.current_step = f"مقارنة {i+1}/{total_comparisons}: {old_result['filename']} مع {new_result['filename']}"
            
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
        session.current_step = "اكتملت مقارنة الملفات"
        
        # إنشاء التقرير النهائي المتقدم
        session.add_log("📊 إنشاء التقرير النهائي المتقدم...")
        session.update_step("report_generation", status="processing", progress=25)
        session.current_step = "إنشاء التقرير النهائي"
        
        # إنشاء خدمة التقارير المحسنة
        report_service = EnhancedReportService()
        
        # إنشاء تقارير فردية لكل مقارنة
        individual_reports = []
        for i, comparison in enumerate(session.comparison_results):
            if comparison['status'] == 'completed':
                old_file = next((r for r in session.processing_results if r['id'] == comparison['old_file_id']), None)
                new_file = next((r for r in session.processing_results if r['id'] == comparison['new_file_id']), None)
                
                if old_file and new_file:
                    # إعداد بيانات التقرير الفردي
                    report_data = ReportData(
                        session_id=f"{session_id}_comparison_{i}",
                        old_image_name=old_file['filename'],
                        new_image_name=new_file['filename'],
                        old_extracted_text=old_file.get('extracted_text', ''),
                        new_extracted_text=new_file.get('extracted_text', ''),
                        visual_similarity=95.0,  # قيمة افتراضية للتشابه البصري
                        text_analysis={
                            'similarity_percentage': comparison['similarity'],
                            'summary': comparison['summary'],
                            'recommendation': comparison['recommendation'],
                            'major_differences': [],
                            'content_changes': comparison.get('changes', []),
                            'questions_changes': [],
                            'examples_changes': [],
                            'has_significant_changes': comparison['similarity'] < 80,
                            'detailed_analysis': comparison.get('detailed_analysis', '')
                        },
                        processing_time={
                            'old_ocr': old_file['processing_time'],
                            'new_ocr': new_file['processing_time'],
                            'comparison': comparison['processing_time']
                        },
                        confidence_scores={
                            'old_confidence': old_file['confidence'],
                            'new_confidence': new_file['confidence']
                        }
                    )
                    
                    # إنشاء تقرير فردي
                    try:
                        report_paths = await report_service.generate_comprehensive_report(
                            session_id=f"{session_id}_comparison_{i}",
                            report_data=report_data,
                            include_extracted_text=True,
                            include_visual_analysis=True
                        )
                        individual_reports.append(report_paths)
                        session.add_log(f"✅ تم إنشاء تقرير للمقارنة {i+1}")
                    except Exception as e:
                        session.add_log(f"❌ خطأ في إنشاء التقرير الفردي {i+1}: {str(e)}", "error")
        
        session.update_step("report_generation", status="processing", progress=75)
        
        # إنشاء التقرير الشامل
        session.add_log("📋 إنشاء التقرير الشامل للمجموعة...")
        comprehensive_report = await _generate_comprehensive_batch_report(session, individual_reports)
        
        # حفظ التقرير النهائي JSON (كنسخة احتياطية)
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
                "individual_reports": individual_reports,
                "comprehensive_report": comprehensive_report,
                "logs": session.logs
            }, f, ensure_ascii=False, indent=2)
        
        session.update_step("report_generation", status="completed", progress=100)
        session.status = "completed"
        session.current_step = "اكتملت المعالجة"
        session.progress = 100  # تأكد من أن التقدم الإجمالي 100%
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
    
    # حساب الإحصائيات
    successful_comparisons = [c for c in session.comparison_results if c['status'] == 'completed']
    failed_comparisons = [c for c in session.comparison_results if c['status'] != 'completed']
    
    average_similarity = 0
    if successful_comparisons:
        average_similarity = sum(c['similarity'] for c in successful_comparisons) / len(successful_comparisons)
    
    total_processing_time = sum(r['processing_time'] for r in session.processing_results if r['status'] == 'completed')
    
    # تجهيز نتائج الملفات الفردية
    file_results = []
    for comparison in successful_comparisons:
        old_file = next((r for r in session.processing_results if r['id'] == comparison['old_file_id']), None)
        new_file = next((r for r in session.processing_results if r['id'] == comparison['new_file_id']), None)
        
        if old_file and new_file:
            file_results.append({
                "old_filename": old_file['filename'],
                "new_filename": new_file['filename'],
                "similarity": comparison['similarity'],
                "confidence": comparison['confidence'],
                "processing_time": comparison['processing_time'],
                "summary": comparison['summary'],
                "recommendation": comparison['recommendation'],
                "changes": comparison['changes'],
                "old_extracted_text": old_file.get('extracted_text', ''),
                "new_extracted_text": new_file.get('extracted_text', '')
            })
    
    return {
        "session_id": session_id,
        "status": session.status,
        "total_files": len(session.old_files) + len(session.new_files),
        "successful_comparisons": len(successful_comparisons),
        "failed_comparisons": len(failed_comparisons),
        "average_similarity": average_similarity,
        "total_processing_time": total_processing_time,
        "file_results": file_results,
        "processing_results": session.processing_results,
        "comparison_results": session.comparison_results,
        "statistics": {
            "total_files": len(session.old_files) + len(session.new_files),
            "completed_files": len([r for r in session.processing_results if r['status'] == 'completed']),
            "average_confidence": sum(r['confidence'] for r in session.processing_results if r['status'] == 'completed') / len([r for r in session.processing_results if r['status'] == 'completed']) if session.processing_results else 0,
            "total_processing_time": total_processing_time,
            "completed_comparisons": len(successful_comparisons),
            "failed_comparisons": len(failed_comparisons),
            "average_similarity": average_similarity
        },
        "logs": session.logs
    }


@router.get("/advanced-processing/{session_id}/download-report")
async def download_processing_report(session_id: str):
    """
    تحميل التقرير الشامل للمعالجة كملف مضغوط
    Download comprehensive processing report as ZIP file
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    
    session = processing_sessions[session_id]
    
    if session.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="المعالجة لم تكتمل بعد"
        )
    
    try:
        # إنشاء ملف مضغوط مؤقت
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # إضافة التقرير الشامل HTML
            comprehensive_html = os.path.join(session.session_dir, "comprehensive_report.html")
            if os.path.exists(comprehensive_html):
                zipf.write(comprehensive_html, "تقرير_شامل.html")
            
            # البحث عن جميع التقارير الفردية وإضافتها
            reports_dir = os.path.join(settings.UPLOAD_DIR, "reports")
            if os.path.exists(reports_dir):
                for item in os.listdir(reports_dir):
                    item_path = os.path.join(reports_dir, item)
                    if os.path.isdir(item_path) and session_id in item:
                        # إضافة جميع ملفات التقرير في هذا المجلد
                        for file in os.listdir(item_path):
                            file_path = os.path.join(item_path, file)
                            if os.path.isfile(file_path):
                                zipf.write(file_path, f"تقارير_فردية/{file}")
            
            # إضافة النصوص المستخرجة
            extracted_texts_dir = os.path.join(session.session_dir, "ocr_results")
            if os.path.exists(extracted_texts_dir):
                for root, dirs, files in os.walk(extracted_texts_dir):
                    for file in files:
                        if file.endswith('.md'):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, extracted_texts_dir)
                            zipf.write(file_path, f"نصوص_مستخرجة/{rel_path}")
            
            # إضافة ملف JSON كنسخة احتياطية
            json_report_path = os.path.join(session.session_dir, "final_report.json")
            if os.path.exists(json_report_path):
                zipf.write(json_report_path, "تفاصيل_تقنية.json")
            
            # إنشاء ملف README يشرح محتويات الأرشيف
            readme_content = f"""# تقرير المقارنة الشاملة

## معلومات عامة
- معرف الجلسة: {session_id}
- تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- حالة المعالجة: {session.status}

## محتويات الأرشيف

### 📊 التقرير الشامل
- `تقرير_شامل.html`: تقرير HTML تفاعلي يحتوي على جميع النتائج

### 📝 التقارير الفردية
مجلد `تقارير_فردية/` يحتوي على:
- تقارير HTML/MD منفصلة لكل مقارنة
- تحليل مفصل لكل زوج من الملفات

### 📄 النصوص المستخرجة  
مجلد `نصوص_مستخرجة/` يحتوي على:
- النصوص الأصلية المستخرجة من الصور
- ملفات Markdown بالتفاصيل الكاملة

### 🔧 التفاصيل التقنية
- `تفاصيل_تقنية.json`: بيانات خام لجميع النتائج

## كيفية الاستخدام
1. افتح `تقرير_شامل.html` للحصول على نظرة عامة
2. استعرض التقارير الفردية للتفاصيل
3. راجع النصوص المستخرجة للتحقق من دقة OCR

---
تم إنتاج هذا التقرير بواسطة نظام مقارن المناهج التعليمية
"""
            
            # إضافة ملف README
            readme_path = os.path.join(session.session_dir, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            zipf.write(readme_path, "README.md")
        
        # إرجاع الملف المضغوط للتحميل
        zip_filename = f"تقرير_مقارنة_شامل_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        def cleanup_temp_file():
            try:
                os.unlink(temp_zip.name)
                os.unlink(readme_path)
            except:
                pass
        
        # استخدام StreamingResponse لإرسال الملف وحذفه بعد الإرسال
        def generate():
            with open(temp_zip.name, 'rb') as f:
                yield from f
            cleanup_temp_file()
        
        return StreamingResponse(
            generate(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "Content-Length": str(os.path.getsize(temp_zip.name))
            }
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء ملف التقرير المضغوط: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في إنشاء التقرير: {str(e)}"
        )


async def _generate_comprehensive_html_report(session: AdvancedProcessingSession) -> str:
    """إنشاء تقرير HTML شامل للمقارنة المجمعة"""
    
    # حساب الإحصائيات
    successful_comparisons = [c for c in session.comparison_results if c['status'] == 'completed']
    failed_comparisons = [c for c in session.comparison_results if c['status'] != 'completed']
    
    average_similarity = 0
    if successful_comparisons:
        average_similarity = sum(c['similarity'] for c in successful_comparisons) / len(successful_comparisons)
    
    total_processing_time = sum(r['processing_time'] for r in session.processing_results if r['status'] == 'completed')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير المقارنة الشاملة</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        .header p {{
            margin: 10px 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8fafc;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border-left: 4px solid #667eea;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 0;
        }}
        .stat-label {{
            color: #64748b;
            margin: 5px 0 0;
            font-weight: 500;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #1e293b;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 25px;
            font-size: 1.8em;
        }}
        .comparison-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }}
        .comparison-card:hover {{
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        .comparison-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .file-names {{
            font-weight: bold;
            color: #1e293b;
            font-size: 1.1em;
        }}
        .similarity {{
            background: #10b981;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .similarity.medium {{
            background: #f59e0b;
        }}
        .similarity.low {{
            background: #ef4444;
        }}
        .details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        .detail-box {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .detail-title {{
            font-weight: bold;
            color: #475569;
            margin-bottom: 8px;
        }}
        .extracted-text {{
            background: #f1f5f9;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            border: 1px solid #cbd5e1;
        }}
        .footer {{
            background: #1e293b;
            color: white;
            text-align: center;
            padding: 25px;
            font-size: 0.9em;
        }}
        .warning {{
            background: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .warning-title {{
            font-weight: bold;
            color: #92400e;
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 تقرير المقارنة الشاملة</h1>
            <p>تقرير مفصل لنتائج المقارنة بين الكتب القديمة والجديدة</p>
            <p>تم إنشاؤه في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(session.old_files) + len(session.new_files)}</div>
                <div class="stat-label">إجمالي الملفات</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(successful_comparisons)}</div>
                <div class="stat-label">مقارنات ناجحة</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{average_similarity:.1f}%</div>
                <div class="stat-label">متوسط التشابه</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_processing_time:.1f}s</div>
                <div class="stat-label">وقت المعالجة</div>
            </div>
        </div>
        
        <div class="content">
    """
    
    # إضافة تحذير API إذا كان هناك أخطاء
    if any('خطأ' in c.get('summary', '') for c in successful_comparisons):
        html_content += """
            <div class="warning">
                <div class="warning-title">⚠️ تنبيه مهم</div>
                <p>تم الوصول إلى الحد الأقصى اليومي لـ Gemini AI API (50 طلب/يوم). بعض المقارنات تظهر التشابه الأساسي فقط وليس التحليل المتقدم المفصل.</p>
            </div>
        """
    
    html_content += """
            <div class="section">
                <h2>📋 نتائج المقارنات التفصيلية</h2>
    """
    
    # إضافة تفاصيل كل مقارنة
    for i, comparison in enumerate(successful_comparisons):
        old_file = next((r for r in session.processing_results if r['id'] == comparison['old_file_id']), None)
        new_file = next((r for r in session.processing_results if r['id'] == comparison['new_file_id']), None)
        
        if old_file and new_file:
            similarity_class = "high" if comparison['similarity'] > 70 else "medium" if comparison['similarity'] > 50 else "low"
            
            html_content += f"""
                <div class="comparison-card">
                    <div class="comparison-header">
                        <div class="file-names">{old_file['filename']} ← {new_file['filename']}</div>
                        <div class="similarity {similarity_class}">{comparison['similarity']:.1f}%</div>
                    </div>
                    
                    <div class="details">
                        <div class="detail-box">
                            <div class="detail-title">ملخص التحليل</div>
                            <p>{comparison.get('summary', 'تم حساب التشابه الأساسي فقط')}</p>
                        </div>
                        <div class="detail-box">
                            <div class="detail-title">التوصية</div>
                            <p>{comparison.get('recommendation', 'يُنصح بالمراجعة اليدوية')}</p>
                        </div>
                    </div>
                    
                    <div class="details">
                        <div>
                            <div class="detail-title">النص القديم ({old_file['filename']})</div>
                            <div class="extracted-text">{old_file.get('extracted_text', 'النص غير متاح')[:500]}{'...' if len(old_file.get('extracted_text', '')) > 500 else ''}</div>
                        </div>
                        <div>
                            <div class="detail-title">النص الجديد ({new_file['filename']})</div>
                            <div class="extracted-text">{new_file.get('extracted_text', 'النص غير متاح')[:500]}{'...' if len(new_file.get('extracted_text', '')) > 500 else ''}</div>
                        </div>
                    </div>
                </div>
            """
    
    html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p>تم إنتاج هذا التقرير بواسطة نظام مقارن المناهج التعليمية</p>
            <p>مدعوم بـ Landing.AI للتعرف البصري و Gemini AI للتحليل المتقدم</p>
        </div>
    </div>
</body>
</html>
    """
    
    return html_content


async def _generate_comprehensive_markdown_report(session: AdvancedProcessingSession) -> str:
    """إنشاء تقرير Markdown شامل للمقارنة المجمعة"""
    
    # حساب الإحصائيات
    successful_comparisons = [c for c in session.comparison_results if c['status'] == 'completed']
    failed_comparisons = [c for c in session.comparison_results if c['status'] != 'completed']
    
    average_similarity = 0
    if successful_comparisons:
        average_similarity = sum(c['similarity'] for c in successful_comparisons) / len(successful_comparisons)
    
    total_processing_time = sum(r['processing_time'] for r in session.processing_results if r['status'] == 'completed')
    
    markdown_content = f"""# 📊 تقرير المقارنة الشاملة

**تاريخ الإنشاء:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**معرف الجلسة:** {session.session_id}  

---

## 📈 إحصائيات عامة

| المؤشر | القيمة |
|---------|--------|
| 📁 إجمالي الملفات | {len(session.old_files) + len(session.new_files)} |
| ✅ مقارنات ناجحة | {len(successful_comparisons)} |
| ❌ مقارنات فاشلة | {len(failed_comparisons)} |
| 🎯 متوسط التشابه | {average_similarity:.1f}% |
| ⏱️ وقت المعالجة الإجمالي | {total_processing_time:.1f} ثانية |

---
"""

    # إضافة تحذير API إذا كان هناك أخطاء
    if any('خطأ' in c.get('summary', '') for c in successful_comparisons):
        markdown_content += """
## ⚠️ تنبيه مهم

تم الوصول إلى الحد الأقصى اليومي لـ Gemini AI API (50 طلب/يوم). بعض المقارنات تظهر التشابه الأساسي فقط وليس التحليل المتقدم المفصل.

---
"""
    
    markdown_content += """
## 📋 نتائج المقارنات التفصيلية

"""
    
    # إضافة تفاصيل كل مقارنة
    for i, comparison in enumerate(successful_comparisons):
        old_file = next((r for r in session.processing_results if r['id'] == comparison['old_file_id']), None)
        new_file = next((r for r in session.processing_results if r['id'] == comparison['new_file_id']), None)
        
        if old_file and new_file:
            similarity_emoji = "🟢" if comparison['similarity'] > 70 else "🟡" if comparison['similarity'] > 50 else "🔴"
            
            markdown_content += f"""
### {similarity_emoji} مقارنة {i+1}: {old_file['filename']} ← {new_file['filename']}

**نسبة التشابه:** {comparison['similarity']:.1f}%  
**مستوى الثقة:** {comparison['confidence']:.1f}%  
**وقت المعالجة:** {comparison['processing_time']:.1f} ثانية  

#### 📝 ملخص التحليل
{comparison.get('summary', 'تم حساب التشابه الأساسي فقط')}

#### 💡 التوصية
{comparison.get('recommendation', 'يُنصح بالمراجعة اليدوية للتأكد من التغييرات')}

#### 📄 النص المستخرج

##### الملف القديم ({old_file['filename']})
```
{old_file.get('extracted_text', 'النص غير متاح')[:1000]}{'...' if len(old_file.get('extracted_text', '')) > 1000 else ''}
```

##### الملف الجديد ({new_file['filename']})
```
{new_file.get('extracted_text', 'النص غير متاح')[:1000]}{'...' if len(new_file.get('extracted_text', '')) > 1000 else ''}
```

---
"""
    
    markdown_content += f"""

## 🔧 معلومات تقنية

- **خدمة التعرف البصري:** Landing.AI
- **خدمة التحليل:** Gemini AI  
- **إجمالي ملفات الكتاب القديم:** {len(session.old_files)}
- **إجمالي ملفات الكتاب الجديد:** {len(session.new_files)}
- **متوسط ثقة التعرف البصري:** {sum(r['confidence'] for r in session.processing_results if r['status'] == 'completed') / len([r for r in session.processing_results if r['status'] == 'completed']) * 100:.1f}%

---

*تم إنتاج هذا التقرير بواسطة نظام مقارن المناهج التعليمية*
"""
    
    return markdown_content


@router.get("/advanced-processing/{session_id}/download-html")
async def download_html_report(session_id: str):
    """
    تحميل التقرير الشامل بصيغة HTML
    Download comprehensive HTML report
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    
    session = processing_sessions[session_id]
    
    if session.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="المعالجة لم تكتمل بعد"
        )
    
    try:
        # إنشاء تقرير HTML شامل
        html_content = await _generate_comprehensive_html_report(session)
        
        # إنشاء اسم الملف
        filename = f"تقرير_مقارنة_شامل_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        return Response(
            content=html_content,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/html; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء تقرير HTML: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في إنشاء التقرير: {str(e)}"
        )


@router.get("/advanced-processing/{session_id}/download-markdown")
async def download_markdown_report(session_id: str):
    """
    تحميل التقرير الشامل بصيغة Markdown
    Download comprehensive Markdown report
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    
    session = processing_sessions[session_id]
    
    if session.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="المعالجة لم تكتمل بعد"
        )
    
    try:
        # إنشاء تقرير Markdown شامل
        markdown_content = await _generate_comprehensive_markdown_report(session)
        
        # إنشاء اسم الملف
        filename = f"تقرير_مقارنة_شامل_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        return Response(
            content=markdown_content,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/markdown; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء تقرير Markdown: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في إنشاء التقرير: {str(e)}"
        )


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