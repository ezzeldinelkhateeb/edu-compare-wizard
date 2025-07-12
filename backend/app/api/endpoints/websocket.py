"""
WebSocket endpoints للتقدم الحي
WebSocket Endpoints for Real-time Progress Updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
from datetime import datetime
from loguru import logger

from app.models.schemas import WebSocketMessage, ProgressUpdate
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()

# إدارة اتصالات WebSocket
class WebSocketManager:
    def __init__(self):
        # تخزين الاتصالات النشطة مصنفة حسب job_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, job_id: str):
        """إضافة اتصال جديد"""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        
        self.active_connections[job_id].append(websocket)
        logger.info(f"🔌 تم إضافة اتصال WebSocket للوظيفة: {job_id}")
        
        # إرسال رسالة ترحيب
        await self.send_message(websocket, {
            "type": "connection_established",
            "data": {
                "job_id": job_id,
                "message": "تم الاتصال بنجاح",
                "timestamp": datetime.now().isoformat()
            }
        })
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """إزالة اتصال"""
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
                logger.info(f"🔌 تم قطع اتصال WebSocket للوظيفة: {job_id}")
            
            # إزالة job_id إذا لم تعد هناك اتصالات
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
    
    async def send_message(self, websocket: WebSocket, message: dict):
        """إرسال رسالة إلى اتصال واحد"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False, default=str))
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال رسالة WebSocket: {e}")
    
    async def broadcast_to_job(self, job_id: str, message: dict):
        """إرسال رسالة لجميع الاتصالات المرتبطة بوظيفة معينة"""
        if job_id not in self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections[job_id]:
            try:
                await self.send_message(websocket, message)
            except Exception as e:
                logger.error(f"❌ خطأ في البث للوظيفة {job_id}: {e}")
                disconnected.append(websocket)
        
        # إزالة الاتصالات المنقطعة
        for websocket in disconnected:
            self.disconnect(websocket, job_id)
    
    async def send_progress_update(self, job_id: str, progress_data: dict):
        """إرسال تحديث التقدم"""
        message = {
            "type": "progress_update",
            "data": progress_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_job(job_id, message)
        logger.debug(f"📊 تم إرسال تحديث التقدم للوظيفة {job_id}: {progress_data.get('progress_percentage', 0)}%")
    
    async def send_stage_update(self, job_id: str, stage: str, message: str):
        """إرسال تحديث المرحلة"""
        update = {
            "type": "stage_update",
            "data": {
                "job_id": job_id,
                "stage": stage,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.broadcast_to_job(job_id, update)
        logger.info(f"📝 تحديث المرحلة للوظيفة {job_id}: {stage} - {message}")
    
    async def send_error(self, job_id: str, error_message: str, error_code: str = "PROCESSING_ERROR"):
        """إرسال رسالة خطأ"""
        message = {
            "type": "error",
            "data": {
                "job_id": job_id,
                "error_code": error_code,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.broadcast_to_job(job_id, message)
        logger.error(f"❌ تم إرسال خطأ للوظيفة {job_id}: {error_message}")
    
    async def send_completion(self, job_id: str, result_data: dict):
        """إرسال إشعار الاكتمال"""
        message = {
            "type": "job_completed",
            "data": {
                "job_id": job_id,
                "result": result_data,
                "timestamp": datetime.now().isoformat(),
                "message": "تم اكتمال المعالجة بنجاح"
            }
        }
        await self.broadcast_to_job(job_id, message)
        logger.info(f"✅ تم إرسال إشعار الاكتمال للوظيفة {job_id}")
    
    def get_active_connections_count(self, job_id: str = None) -> int:
        """الحصول على عدد الاتصالات النشطة"""
        if job_id:
            return len(self.active_connections.get(job_id, []))
        return sum(len(connections) for connections in self.active_connections.values())


# إنشاء instance من مدير WebSocket
websocket_manager = WebSocketManager()


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint للتقدم الحي"""
    await websocket_manager.connect(websocket, job_id)
    
    try:
        while True:
            # استقبال الرسائل من العميل (إن وجدت)
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # معالجة رسائل العميل
                if message.get("type") == "ping":
                    await websocket_manager.send_message(websocket, {
                        "type": "pong",
                        "data": {"timestamp": datetime.now().isoformat()}
                    })
                elif message.get("type") == "request_status":
                    # يمكن إضافة منطق للحصول على حالة الوظيفة
                    await websocket_manager.send_message(websocket, {
                        "type": "status_response",
                        "data": {
                            "job_id": job_id,
                            "status": "processing",  # من قاعدة البيانات
                            "message": "الوظيفة قيد المعالجة"
                        }
                    })
                
            except json.JSONDecodeError:
                await websocket_manager.send_message(websocket, {
                    "type": "error",
                    "data": {
                        "error_code": "INVALID_JSON",
                        "error_message": "تنسيق الرسالة غير صحيح"
                    }
                })
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة رسالة WebSocket: {e}")
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, job_id)
        logger.info(f"🔌 تم قطع اتصال WebSocket للوظيفة: {job_id}")
    except Exception as e:
        logger.error(f"❌ خطأ في WebSocket للوظيفة {job_id}: {e}")
        websocket_manager.disconnect(websocket, job_id)


@router.get("/ws/stats")
async def websocket_stats():
    """إحصائيات اتصالات WebSocket"""
    stats = {
        "total_connections": websocket_manager.get_active_connections_count(),
        "active_jobs": len(websocket_manager.active_connections),
        "connections_per_job": {
            job_id: len(connections) 
            for job_id, connections in websocket_manager.active_connections.items()
        },
        "timestamp": datetime.now().isoformat()
    }
    return stats


# دالة مساعدة للاستخدام من أجزاء أخرى من التطبيق
def get_websocket_manager() -> WebSocketManager:
    """الحصول على مدير WebSocket"""
    return websocket_manager


# دوال مساعدة للإرسال من خدمات أخرى
async def notify_progress(job_id: str, progress_percentage: float, current_file: str = None, message: str = None):
    """إرسال تحديث التقدم"""
    progress_data = {
        "job_id": job_id,
        "progress_percentage": min(100, max(0, progress_percentage)),
        "current_file": current_file,
        "message": message
    }
    await websocket_manager.send_progress_update(job_id, progress_data)


async def notify_stage_change(job_id: str, stage: str, message: str):
    """إرسال تحديث المرحلة"""
    await websocket_manager.send_stage_update(job_id, stage, message)


async def notify_error(job_id: str, error_message: str, error_code: str = "PROCESSING_ERROR"):
    """إرسال إشعار خطأ"""
    await websocket_manager.send_error(job_id, error_message, error_code)


async def notify_completion(job_id: str, result_data: dict):
    """إرسال إشعار الاكتمال"""
    await websocket_manager.send_completion(job_id, result_data) 