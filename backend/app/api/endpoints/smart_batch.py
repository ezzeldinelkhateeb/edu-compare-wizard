"""
Smart Batch Processing API Endpoint
واجهة API للمعالجة الجماعية الذكية
"""

import os
import json
import asyncio
from typing import Dict, List, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile, Form
from pydantic import BaseModel
import uuid
import tempfile
import shutil

# Import the smart processor
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from smart_batch_processor import SmartBatchProcessor

router = APIRouter()

# نموذج الطلب
class BatchProcessRequest(BaseModel):
    old_directory: str
    new_directory: str
    max_workers: int = 4
    visual_threshold: float = 0.95

# نموذج الاستجابة
class BatchProcessResponse(BaseModel):
    session_id: str
    status: str
    message: str

class BatchProcessResult(BaseModel):
    session_id: str
    status: str
    results: List[Dict[str, Any]]
    stats: Dict[str, Any]
    message: str

# تخزين النتائج في الذاكرة (يمكن تحسينه بقاعدة بيانات)
batch_sessions = {}

@router.post("/start-batch-process", response_model=BatchProcessResponse)
async def start_batch_process(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks
):
    """بدء المعالجة الجماعية الذكية"""
    
    # التحقق من وجود المجلدات
    if not Path(request.old_directory).exists():
        raise HTTPException(
            status_code=400,
            detail=f"المجلد القديم غير موجود: {request.old_directory}"
        )
    
    if not Path(request.new_directory).exists():
        raise HTTPException(
            status_code=400,
            detail=f"المجلد الجديد غير موجود: {request.new_directory}"
        )
    
    # إنشاء جلسة جديدة
    session_id = str(uuid.uuid4())
    
    # تسجيل الجلسة
    batch_sessions[session_id] = {
        "status": "بدء المعالجة",
        "results": [],
        "stats": {},
        "created_at": Path(__file__).stat().st_mtime
    }
    
    # بدء المعالجة في الخلفية
    background_tasks.add_task(
        run_batch_processing,
        session_id,
        request
    )
    
    return BatchProcessResponse(
        session_id=session_id,
        status="تم البدء",
        message="تم بدء المعالجة الجماعية الذكية. استخدم session_id للاستعلام عن النتائج."
    )

@router.post("/start-batch-process-files", response_model=BatchProcessResponse)
async def start_batch_process_files(
    old_files: List[UploadFile] = File(...),
    new_files: List[UploadFile] = File(...),
    max_workers: int = Form(4),
    visual_threshold: float = Form(0.95),
    background_tasks: BackgroundTasks = None
):
    """بدء المعالجة الجماعية الذكية بملفات مرفوعة"""
    
    # التحقق من وجود ملفات
    if not old_files or not new_files:
        raise HTTPException(
            status_code=400,
            detail="يجب رفع ملفات للمنهج القديم والجديد"
        )
    
    # إنشاء جلسة جديدة
    session_id = str(uuid.uuid4())
    
    try:
        # إنشاء مجلدات مؤقتة
        temp_dir = tempfile.mkdtemp(prefix=f"smart_batch_{session_id}_")
        old_dir = os.path.join(temp_dir, "old")
        new_dir = os.path.join(temp_dir, "new")
        
        os.makedirs(old_dir, exist_ok=True)
        os.makedirs(new_dir, exist_ok=True)
        
        # حفظ الملفات القديمة
        for i, file in enumerate(old_files):
            if file.filename:
                file_path = os.path.join(old_dir, f"{i}_{file.filename}")
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
        
        # حفظ الملفات الجديدة
        for i, file in enumerate(new_files):
            if file.filename:
                file_path = os.path.join(new_dir, f"{i}_{file.filename}")
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
        
        # تسجيل الجلسة
        batch_sessions[session_id] = {
            "status": "بدء المعالجة",
            "results": [],
            "stats": {},
            "created_at": Path(__file__).stat().st_mtime,
            "temp_dir": temp_dir  # لحذفه لاحقاً
        }
        
        # إنشاء طلب معالجة
        request = BatchProcessRequest(
            old_directory=old_dir,
            new_directory=new_dir,
            max_workers=max_workers,
            visual_threshold=visual_threshold
        )
        
        # بدء المعالجة في الخلفية
        background_tasks.add_task(
            run_batch_processing_with_cleanup,
            session_id,
            request,
            temp_dir
        )
        
        return BatchProcessResponse(
            session_id=session_id,
            status="تم البدء",
            message=f"تم بدء المعالجة الذكية لـ {len(old_files) + len(new_files)} ملف"
        )
        
    except Exception as e:
        # تنظيف المجلد المؤقت في حالة الخطأ
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"فشل في معالجة الملفات: {str(e)}"
        )

async def run_batch_processing(session_id: str, request: BatchProcessRequest):
    """تشغيل المعالجة الجماعية في الخلفية"""
    
    try:
        # تحديث الحالة
        batch_sessions[session_id]["status"] = "جاري المعالجة"
        
        # دالة تحديث الحالة
        def update_status(status_data):
            batch_sessions[session_id].update({
                "status": status_data.get("status", "جاري المعالجة"),
                "progress": status_data.get("progress", 0),
                "current_file": status_data.get("current_file"),
                "message": status_data.get("message", ""),
                "stats": status_data.get("stats", {}),
                "results": status_data.get("results", [])
            })
        
        # إنشاء المعالج الذكي مع دالة تحديث الحالة
        processor = SmartBatchProcessor(
            old_dir=request.old_directory,
            new_dir=request.new_directory,
            max_workers=request.max_workers,
            visual_threshold=request.visual_threshold,
            session_id=session_id,
            status_callback=update_status
        )
        
        # تشغيل المعالجة
        processor.run_batch_processing()
        
        # حفظ النتائج النهائية
        batch_sessions[session_id].update({
            "status": "مكتمل",
            "results": processor.results,
            "stats": processor.stats,
            "progress": 100
        })
        
    except Exception as e:
        batch_sessions[session_id].update({
            "status": "فشل",
            "error": str(e)
        })

async def run_batch_processing_with_cleanup(session_id: str, request: BatchProcessRequest, temp_dir: str):
    """تشغيل المعالجة الجماعية مع تنظيف المجلدات المؤقتة"""
    
    try:
        # تحديث الحالة
        batch_sessions[session_id]["status"] = "جاري المعالجة"
        
        # دالة تحديث الحالة
        def update_status(status_data):
            batch_sessions[session_id].update({
                "status": status_data.get("status", "جاري المعالجة"),
                "progress": status_data.get("progress", 0),
                "current_file": status_data.get("current_file"),
                "message": status_data.get("message", ""),
                "stats": status_data.get("stats", {}),
                "results": status_data.get("results", [])
            })
        
        # إنشاء المعالج الذكي مع دالة تحديث الحالة
        processor = SmartBatchProcessor(
            old_dir=request.old_directory,
            new_dir=request.new_directory,
            max_workers=request.max_workers,
            visual_threshold=request.visual_threshold,
            session_id=session_id,
            status_callback=update_status
        )
        
        # تشغيل المعالجة
        processor.run_batch_processing()
        
        # حفظ النتائج النهائية
        batch_sessions[session_id].update({
            "status": "مكتمل",
            "results": processor.results,
            "stats": processor.stats,
            "progress": 100
        })
        
    except Exception as e:
        batch_sessions[session_id].update({
            "status": "فشل",
            "error": str(e)
        })
    finally:
        # تنظيف المجلد المؤقت
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass  # تجاهل أخطاء التنظيف

@router.get("/batch-status/{session_id}", response_model=BatchProcessResult)
async def get_batch_status(session_id: str):
    """الحصول على حالة ونتائج المعالجة الجماعية"""
    
    if session_id not in batch_sessions:
        raise HTTPException(
            status_code=404,
            detail="جلسة غير موجودة"
        )
    
    session_data = batch_sessions[session_id]
    
    # إضافة معلومات التقدم للرسالة
    message = f"حالة المعالجة: {session_data['status']}"
    if session_data.get("progress"):
        message += f" - التقدم: {session_data['progress']}%"
    if session_data.get("current_file"):
        message += f" - الملف الحالي: {session_data['current_file']}"
    if session_data.get("message"):
        message += f" - {session_data['message']}"
    
    return BatchProcessResult(
        session_id=session_id,
        status=session_data["status"],
        results=session_data.get("results", []),
        stats=session_data.get("stats", {}),
        message=message
    )

@router.get("/batch-sessions")
async def list_batch_sessions():
    """قائمة بجميع جلسات المعالجة"""
    
    sessions_info = []
    for session_id, data in batch_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "status": data["status"],
            "total_pairs": data.get("stats", {}).get("total_pairs", 0),
            "created_at": data.get("created_at", 0)
        })
    
    return {
        "sessions": sessions_info,
        "total_sessions": len(sessions_info)
    }

@router.delete("/batch-sessions/{session_id}")
async def delete_batch_session(session_id: str):
    """حذف جلسة معالجة"""
    
    if session_id not in batch_sessions:
        raise HTTPException(
            status_code=404,
            detail="جلسة غير موجودة"
        )
    
    del batch_sessions[session_id]
    
    return {
        "message": "تم حذف الجلسة بنجاح",
        "session_id": session_id
    }

@router.get("/system-info")
async def get_system_info():
    """معلومات النظام والقدرات"""
    
    return {
        "system_name": "نظام المقارنة الذكي للمناهج التعليمية",
        "version": "2.0",
        "features": [
            "مقارنة بصرية سريعة",
            "استخراج النص الذكي",
            "تحسين النص لتوفير التكلفة",
            "تحليل عميق بالذكاء الاصطناعي",
            "معالجة جماعية متوازية",
            "تقارير تفصيلية واضحة"
        ],
        "pipeline_stages": [
            {
                "stage": 1,
                "name": "المقارنة البصرية السريعة",
                "cost": "مجاني",
                "description": "يوقف المعالجة إذا كان التشابه البصري >95%"
            },
            {
                "stage": 2,
                "name": "استخراج النص",
                "cost": "1 API call لكل صورة",
                "description": "استخراج النص من الصورتين باستخدام LandingAI"
            },
            {
                "stage": 3,
                "name": "تحسين النص",
                "cost": "مجاني",
                "description": "تقليل حجم النص 70%+ مع الحفاظ على المعنى"
            },
            {
                "stage": 4,
                "name": "التحليل العميق",
                "cost": "1 API call",
                "description": "مقارنة ذكية بالذكاء الاصطناعي مع تجاهل التغييرات الطفيفة"
            }
        ],
        "expected_savings": "42.8% متوسط توفير في التكلفة",
        "supported_formats": ["JPG", "JPEG", "PNG"],
        "max_concurrent_workers": 8,
        "active_sessions": len(batch_sessions)
    } 