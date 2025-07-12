"""
نقطة نهاية API للمقارنة السريعة مع المعالجة المتوازية
Ultra Fast Comparison API Endpoint with Parallel Processing
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import os
import uuid
from datetime import datetime
from loguru import logger
import asyncio

from app.core.config import get_settings
from app.models.schemas import ComparisonResponse, UltraFastComparisonRequest, UltraFastComparisonResponse
from celery_app.optimized_tasks import quick_dual_comparison, parallel_extract_text_batch

settings = get_settings()
router = APIRouter()

# تخزين الجلسات النشطة
active_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/ultra-fast/upload-and-compare")
async def upload_and_compare_ultra_fast(
    old_image: UploadFile = File(...),
    new_image: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    رفع الصور ومقارنتها بشكل سريع جداً مع معالجة متوازية
    Upload images and compare them ultra-fast with parallel processing
    """
    try:
        # إنشاء معرف جلسة جديد
        session_id = str(uuid.uuid4())
        
        logger.info(f"🚀 بدء المقارنة السريعة - الجلسة: {session_id}")
        
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
        
        logger.info(f"📁 تم حفظ الصور في: {session_dir}")
        
        # حفظ معلومات الجلسة
        active_sessions[session_id] = {
            "session_id": session_id,
            "old_image_path": old_image_path,
            "new_image_path": new_image_path,
            "old_image_name": old_image.filename,
            "new_image_name": new_image.filename,
            "created_at": datetime.now().isoformat(),
            "status": "processing",
            "progress": 0
        }
        
        # بدء المقارنة السريعة في الخلفية
        task = quick_dual_comparison.delay(session_id, old_image_path, new_image_path)
        
        # حفظ معرف المهمة
        active_sessions[session_id]["task_id"] = task.id
        
        return JSONResponse(
            content={
                "message": "تم بدء المقارنة السريعة بنجاح",
                "session_id": session_id,
                "task_id": task.id,
                "status": "processing",
                "estimated_time": "30-60 ثانية",
                "endpoints": {
                    "status": f"/api/ultra-fast/status/{session_id}",
                    "result": f"/api/ultra-fast/result/{session_id}",
                    "cancel": f"/api/ultra-fast/cancel/{session_id}"
                }
            },
            status_code=202
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في بدء المقارنة السريعة: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"فشل في بدء المقارنة السريعة: {str(e)}"
        )


@router.get("/ultra-fast/status/{session_id}")
async def get_comparison_status(session_id: str):
    """
    الحصول على حالة المقارنة السريعة
    Get ultra-fast comparison status
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail="الجلسة غير موجودة"
            )
        
        session = active_sessions[session_id]
        task_id = session.get("task_id")
        
        if not task_id:
            raise HTTPException(
                status_code=400,
                detail="لا يوجد معرف مهمة للجلسة"
            )
        
        # فحص حالة المهمة
        from celery_app.worker import celery_app
        task = celery_app.AsyncResult(task_id)
        
        status_info = {
            "session_id": session_id,
            "task_id": task_id,
            "state": task.state,
            "created_at": session["created_at"],
            "old_image_name": session["old_image_name"],
            "new_image_name": session["new_image_name"]
        }
        
        if task.state == 'PENDING':
            status_info.update({
                "status": "waiting",
                "message": "في انتظار بدء المعالجة...",
                "progress": 0
            })
        elif task.state == 'PROGRESS':
            meta = task.info
            status_info.update({
                "status": "processing",
                "message": meta.get('message', 'جاري المعالجة...'),
                "progress": meta.get('progress', 0),
                "stage": meta.get('stage', 'unknown'),
                "current_file": meta.get('current_file', '')
            })
        elif task.state == 'SUCCESS':
            status_info.update({
                "status": "completed",
                "message": "اكتملت المقارنة بنجاح",
                "progress": 100,
                "result_available": True
            })
        elif task.state == 'FAILURE':
            meta = task.info
            status_info.update({
                "status": "failed",
                "message": f"فشلت المعالجة: {str(meta) if meta else 'خطأ غير معروف'}",
                "progress": 0,
                "error": str(meta) if meta else "خطأ غير معروف"
            })
        else:
            status_info.update({
                "status": "unknown",
                "message": f"حالة غير معروفة: {task.state}",
                "progress": 0
            })
        
        # تحديث الجلسة
        active_sessions[session_id].update({
            "status": status_info["status"],
            "progress": status_info.get("progress", 0),
            "last_checked": datetime.now().isoformat()
        })
        
        return JSONResponse(content=status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في فحص حالة الجلسة {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في فحص الحالة: {str(e)}"
        )


@router.get("/ultra-fast/result/{session_id}")
async def get_comparison_result(session_id: str):
    """
    الحصول على نتيجة المقارنة السريعة
    Get ultra-fast comparison result
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail="الجلسة غير موجودة"
            )
        
        session = active_sessions[session_id]
        task_id = session.get("task_id")
        
        if not task_id:
            raise HTTPException(
                status_code=400,
                detail="لا يوجد معرف مهمة للجلسة"
            )
        
        # فحص حالة المهمة
        from celery_app.worker import celery_app
        task = celery_app.AsyncResult(task_id)
        
        if task.state != 'SUCCESS':
            if task.state == 'PENDING':
                status = "في انتظار بدء المعالجة"
            elif task.state == 'PROGRESS':
                meta = task.info
                status = f"جاري المعالجة: {meta.get('message', 'غير محدد')}"
            elif task.state == 'FAILURE':
                status = f"فشلت المعالجة: {str(task.info) if task.info else 'خطأ غير معروف'}"
            else:
                status = f"حالة غير معروفة: {task.state}"
            
            raise HTTPException(
                status_code=400,
                detail=f"النتيجة غير متوفرة بعد. الحالة الحالية: {status}"
            )
        
        # الحصول على النتيجة
        result = task.result
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="فشل في الحصول على نتيجة المقارنة"
            )
        
        # إضافة معلومات الجلسة للنتيجة
        enhanced_result = {
            **result,
            "session_info": {
                "session_id": session_id,
                "old_image_name": session["old_image_name"],
                "new_image_name": session["new_image_name"],
                "created_at": session["created_at"],
                "completed_at": result.get("completed_at"),
                "total_processing_time": result.get("total_processing_time")
            }
        }
        
        # تحديث حالة الجلسة
        active_sessions[session_id].update({
            "status": "completed",
            "progress": 100,
            "result_retrieved_at": datetime.now().isoformat()
        })
        
        logger.info(f"✅ تم إرجاع نتيجة المقارنة للجلسة: {session_id}")
        
        return JSONResponse(content=enhanced_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في الحصول على نتيجة الجلسة {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في الحصول على النتيجة: {str(e)}"
        )


@router.post("/ultra-fast/cancel/{session_id}")
async def cancel_comparison(session_id: str):
    """
    إلغاء المقارنة السريعة
    Cancel ultra-fast comparison
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail="الجلسة غير موجودة"
            )
        
        session = active_sessions[session_id]
        task_id = session.get("task_id")
        
        if not task_id:
            raise HTTPException(
                status_code=400,
                detail="لا يوجد معرف مهمة للجلسة"
            )
        
        # إلغاء المهمة
        from celery_app.worker import celery_app
        celery_app.control.revoke(task_id, terminate=True)
        
        # تحديث الجلسة
        active_sessions[session_id].update({
            "status": "cancelled",
            "progress": 0,
            "cancelled_at": datetime.now().isoformat()
        })
        
        logger.info(f"🚫 تم إلغاء المقارنة للجلسة: {session_id}")
        
        return JSONResponse(content={
            "message": "تم إلغاء المقارنة بنجاح",
            "session_id": session_id,
            "task_id": task_id,
            "status": "cancelled"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في إلغاء الجلسة {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في إلغاء المقارنة: {str(e)}"
        )


@router.get("/ultra-fast/sessions")
async def list_active_sessions():
    """
    عرض الجلسات النشطة
    List active sessions
    """
    try:
        sessions_list = []
        
        for session_id, session_data in active_sessions.items():
            # فحص حالة المهمة إذا كانت موجودة
            current_status = session_data.get("status", "unknown")
            
            if "task_id" in session_data:
                from celery_app.worker import celery_app
                task = celery_app.AsyncResult(session_data["task_id"])
                
                if task.state == 'SUCCESS':
                    current_status = "completed"
                elif task.state == 'FAILURE':
                    current_status = "failed"
                elif task.state == 'PROGRESS':
                    current_status = "processing"
                elif task.state == 'PENDING':
                    current_status = "waiting"
            
            sessions_list.append({
                "session_id": session_id,
                "status": current_status,
                "progress": session_data.get("progress", 0),
                "old_image_name": session_data.get("old_image_name", ""),
                "new_image_name": session_data.get("new_image_name", ""),
                "created_at": session_data.get("created_at", ""),
                "task_id": session_data.get("task_id", "")
            })
        
        return JSONResponse(content={
            "total_sessions": len(sessions_list),
            "sessions": sessions_list
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض الجلسات: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في عرض الجلسات: {str(e)}"
        )


@router.delete("/ultra-fast/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """
    تنظيف ملفات الجلسة
    Cleanup session files
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404,
                detail="الجلسة غير موجودة"
            )
        
        session = active_sessions[session_id]
        
        # حذف الملفات
        session_dir = os.path.join(settings.UPLOAD_DIR, session_id)
        if os.path.exists(session_dir):
            import shutil
            shutil.rmtree(session_dir)
            logger.info(f"🗑️ تم حذف مجلد الجلسة: {session_dir}")
        
        # إزالة الجلسة من الذاكرة
        del active_sessions[session_id]
        
        return JSONResponse(content={
            "message": "تم تنظيف الجلسة بنجاح",
            "session_id": session_id,
            "status": "cleaned"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في تنظيف الجلسة {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في تنظيف الجلسة: {str(e)}"
        ) 