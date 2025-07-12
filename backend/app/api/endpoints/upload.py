"""
API endpoints لرفع الملفات
File Upload API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import aiofiles
import os
import uuid
from datetime import datetime
from loguru import logger

from app.core.config import get_settings
from app.models.schemas import (
    UploadSessionRequest, UploadSessionResponse, FileUploadResponse,
    FileType, JobStatus, ErrorResponse, SuccessResponse
)

# Import Celery components at the module level to avoid import delays
try:
    from celery_app.tasks import file_id_to_path_store
except ImportError as e:
    logger.warning(f"⚠️  Celery import failed: {e}")
    file_id_to_path_store = {}

settings = get_settings()
router = APIRouter()

# تخزين الجلسات مؤقتاً (في التطبيق الحقيقي سيكون في قاعدة البيانات)
sessions_store = {}
files_store = {}


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """التحقق من صحة الملف"""
    # فحص نوع الملف
    if not file.content_type:
        return False, "نوع الملف غير محدد"
    
    # فحص امتداد الملف
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ""
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"نوع الملف غير مدعوم. الأنواع المدعومة: {', '.join(settings.ALLOWED_EXTENSIONS)}"
    
    # فحص حجم الملف (سيتم فحصه أثناء الحفظ)
    return True, "صحيح"


async def save_uploaded_file(file: UploadFile, session_id: str, file_type: FileType) -> tuple[str, str]:
    """حفظ الملف المرفوع وإرجاع المسار ومعرف الملف"""
    file_id = str(uuid.uuid4())
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else ""
    safe_filename = f"{file_id}.{file_ext}"
    
    # تحديد مسار الحفظ
    save_dir = os.path.join(settings.UPLOAD_DIR, session_id, file_type.value)
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, safe_filename)
    
    # حفظ الملف
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            
            # فحص حجم الملف
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"حجم الملف كبير جداً. الحد الأقصى: {settings.MAX_FILE_SIZE / (1024*1024):.1f} MB"
                )
            
            await f.write(content)
            
        logger.info(f"✅ تم حفظ الملف: {file.filename} في {file_path}")
        return file_path, file_id
        
    except Exception as e:
        # حذف الملف في حالة الخطأ
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"❌ خطأ في حفظ الملف {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في حفظ الملف: {str(e)}")


@router.post("/upload/session", response_model=UploadSessionResponse)
async def create_upload_session(request: UploadSessionRequest):
    """إنشاء جلسة رفع جديدة"""
    try:
        session_id = str(uuid.uuid4())
        session_name = request.session_name or f"جلسة_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        
        # حفظ بيانات الجلسة
        session_data = {
            "session_id": session_id,
            "session_name": session_name,
            "description": request.description,
            "created_at": datetime.now(),
            "status": JobStatus.PENDING,
            "old_files": [],
            "new_files": [],
            "total_files": 0
        }
        
        sessions_store[session_id] = session_data
        
        # إنشاء مجلدات الجلسة
        session_dir = os.path.join(settings.UPLOAD_DIR, session_id)
        os.makedirs(os.path.join(session_dir, "old"), exist_ok=True)
        os.makedirs(os.path.join(session_dir, "new"), exist_ok=True)
        
        logger.info(f"🆕 تم إنشاء جلسة جديدة: {session_id} - {session_name}")
        
        return UploadSessionResponse(
            session_id=session_id,
            session_name=session_name,
            created_at=session_data["created_at"],
            status=JobStatus.PENDING,
            message="تم إنشاء الجلسة بنجاح"
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء الجلسة: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في إنشاء الجلسة: {str(e)}")


@router.post("/upload/file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    file_type: FileType = Form(...)
):
    """رفع ملف واحد إلى جلسة موجودة"""
    try:
        # التحقق من وجود الجلسة
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        session = sessions_store[session_id]
        
        # التحقق من صحة الملف
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # حفظ الملف
        file_path, file_id = await save_uploaded_file(file, session_id, file_type)
        
        # تحديث بيانات الجلسة
        file_info = {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "content_type": file.content_type,
            "uploaded_at": datetime.now()
        }
        
        # Store file_id to path mapping for Celery tasks
        file_id_to_path_store[file_id] = file_path

        if file_type == FileType.OLD:
            session["old_files"].append(file_info)
        else:
            session["new_files"].append(file_info)
        
        session["total_files"] = len(session["old_files"]) + len(session["new_files"])
        
        # حفظ معلومات الملف
        files_store[file_id] = file_info
        
        logger.info(f"📁 تم رفع ملف {file_type.value}: {file.filename} للجلسة {session_id}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_info["file_size"],
            upload_url=file_path,
            message="تم رفع الملف بنجاح"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في رفع الملف: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في رفع الملف: {str(e)}")


@router.post("/upload/batch", response_model=List[FileUploadResponse])
async def upload_batch_files(
    files: List[UploadFile] = File(...),
    session_id: str = Form(...),
    file_type: FileType = Form(...)
):
    """رفع مجموعة من الملفات"""
    try:
        # التحقق من وجود الجلسة
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        if len(files) > 100:  # حد أقصى 100 ملف
            raise HTTPException(status_code=400, detail="عدد الملفات كبير جداً. الحد الأقصى 100 ملف")
        
        results = []
        failed_files = []
        
        for file in files:
            try:
                # التحقق من صحة الملف
                is_valid, error_msg = validate_file(file)
                if not is_valid:
                    failed_files.append(f"{file.filename}: {error_msg}")
                    continue
                
                # حفظ الملف
                file_path, file_id = await save_uploaded_file(file, session_id, file_type)
                
                # تحديث بيانات الجلسة
                file_info = {
                    "file_id": file_id,
                    "filename": file.filename,
                    "file_path": file_path,
                    "file_size": os.path.getsize(file_path),
                    "content_type": file.content_type,
                    "uploaded_at": datetime.now()
                }
                
                # Store file_id to path mapping for Celery tasks
                from celery_app.tasks import file_id_to_path_store
                file_id_to_path_store[file_id] = file_path

                session = sessions_store[session_id]
                if file_type == FileType.OLD:
                    session["old_files"].append(file_info)
                else:
                    session["new_files"].append(file_info)
                
                files_store[file_id] = file_info
                
                results.append(FileUploadResponse(
                    file_id=file_id,
                    filename=file.filename,
                    file_type=file_type,
                    file_size=file_info["file_size"],
                    upload_url=file_path,
                    message="تم رفع الملف بنجاح"
                ))
                
            except Exception as e:
                failed_files.append(f"{file.filename}: {str(e)}")
                continue
        
        # تحديث إجمالي الملفات
        session = sessions_store[session_id]
        session["total_files"] = len(session["old_files"]) + len(session["new_files"])
        
        logger.info(f"📁 تم رفع {len(results)} ملف للجلسة {session_id}. فشل في {len(failed_files)} ملف")
        
        if failed_files and len(results) == 0:
            raise HTTPException(status_code=400, detail=f"فشل في رفع جميع الملفات: {'; '.join(failed_files)}")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في رفع مجموعة الملفات: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في رفع الملفات: {str(e)}")


@router.get("/upload/session/{session_id}")
async def get_session_info(session_id: str):
    """الحصول على معلومات الجلسة"""
    try:
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        session = sessions_store[session_id]
        return {
            "session_id": session_id,
            "session_name": session["session_name"],
            "description": session["description"],
            "status": session["status"],
            "created_at": session["created_at"],
            "total_files": session["total_files"],
            "old_files_count": len(session["old_files"]),
            "new_files_count": len(session["new_files"]),
            "old_files": session["old_files"],
            "new_files": session["new_files"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في جلب معلومات الجلسة: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في جلب معلومات الجلسة: {str(e)}")


@router.delete("/upload/session/{session_id}")
async def delete_session(session_id: str):
    """حذف الجلسة وجميع ملفاتها"""
    try:
        if session_id not in sessions_store:
            raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
        
        # حذف ملفات الجلسة
        session_dir = os.path.join(settings.UPLOAD_DIR, session_id)
        if os.path.exists(session_dir):
            import shutil
            shutil.rmtree(session_dir)
        
        # حذف معلومات الجلسة
        session = sessions_store[session_id]
        for file_info in session["old_files"] + session["new_files"]:
            files_store.pop(file_info["file_id"], None)
        
        del sessions_store[session_id]
        
        logger.info(f"🗑️ تم حذف الجلسة: {session_id}")
        
        return SuccessResponse(
            message="تم حذف الجلسة بنجاح"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في حذف الجلسة: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في حذف الجلسة: {str(e)}")


@router.get("/upload/sessions")
async def list_sessions():
    """قائمة جميع الجلسات"""
    try:
        sessions_list = []
        for session_id, session in sessions_store.items():
            sessions_list.append({
                "session_id": session_id,
                "session_name": session["session_name"],
                "status": session["status"],
                "created_at": session["created_at"],
                "total_files": session["total_files"],
                "old_files_count": len(session["old_files"]),
                "new_files_count": len(session["new_files"])
            })
        
        return {
            "sessions": sessions_list,
            "total_sessions": len(sessions_list)
        }
        
    except Exception as e:
        logger.error(f"❌ خطأ في جلب قائمة الجلسات: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في جلب قائمة الجلسات: {str(e)}") 