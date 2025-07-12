"""
تطبيق FastAPI الرئيسي لنظام مقارن المناهج التعليمية
Main FastAPI Application for Educational Content Comparison System
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import sys
import os
from datetime import datetime
import json
import math
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import compare, advanced_processing, smart_batch
from app.api.endpoints.ultra_fast_compare import router as ultra_fast_compare_router
from app.core.config import settings

# إضافة المسار للاستيراد
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.models.schemas import ErrorResponse

# تطبيق إعدادات agentic-doc المحسّنة عند بدء التشغيل
from app.core import configure_agentic_doc

settings = get_settings()

# JSON encoder مخصص للتعامل مع القيم غير الصالحة
class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder آمن يتعامل مع القيم غير المدعومة"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)

# تطبيق JSON Response مخصص
class SafeJSONResponse(JSONResponse):
    """JSONResponse آمن يستخدم encoder مخصص"""
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=SafeJSONEncoder
        ).encode("utf-8")

# إعداد الـ logging
logger.remove()
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

if settings.LOG_FILE:
    logger.add(
        settings.LOG_FILE,
        rotation="500 MB",
        retention="1 month",
        level=settings.LOG_LEVEL,
        encoding="utf-8"
    )

# إنشاء تطبيق FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="نظام ذكي لمقارنة المناهج التعليمية باستخدام الذكاء الاصطناعي",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    default_response_class=SafeJSONResponse,
)

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # السماح لجميع المنافذ في بيئة التطوير
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# إعداد TrustedHost (للأمان)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # في الإنتاج يجب تحديد النطاقات المسموحة
    )

# معالجة الأخطاء العامة
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """معالج الأخطاء العام"""
    logger.error(f"Unhandled exception: {exc}")
    
    if settings.DEBUG:
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    error_response = {
        "error_code": "INTERNAL_SERVER_ERROR",
        "error_message": "حدث خطأ داخلي في الخادم",
        "timestamp": datetime.now().isoformat(),
        "details": {"exception": str(exc)} if settings.DEBUG else None
    }
    
    return SafeJSONResponse(
        status_code=500,
        content=error_response
    )

# الصفحة الرئيسية
@app.get("/")
async def root():
    """الصفحة الرئيسية للـ API"""
    return {
        "message": "مرحباً بك في نظام مقارن المناهج التعليمية",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs_url": "/docs" if settings.DEBUG else "غير متاح في الإنتاج",
        "api_base": settings.API_V1_STR
    }

# فحص صحة التطبيق
@app.get("/health")
async def health_check():
    """فحص صحة التطبيق"""
    try:
        # يمكن إضافة فحوصات أخرى هنا (قاعدة البيانات، Redis، إلخ)
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "api": "running",
                "database": "checking...",  # سيتم تحديثه لاحقاً
                "redis": "checking...",     # سيتم تحديثه لاحقاً
                "ai_services": "checking..."  # سيتم تحديثه لاحقاً
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# إعداد التطبيق عند البدء
@app.on_event("startup")
async def startup_event():
    """إعداد التطبيق عند بدء التشغيل"""
    logger.info("🚀 بدء تشغيل نظام مقارن المناهج التعليمية")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🌐 Server: {settings.HOST}:{settings.PORT}")
    logger.info(f"📁 Upload Directory: {settings.UPLOAD_DIR}")
    
    # إنشاء مجلدات الرفع إذا لم تكن موجودة
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(os.path.join(settings.UPLOAD_DIR, "temp"), exist_ok=True)
        logger.info("✅ تم إنشاء مجلدات الرفع بنجاح")
    except OSError as e:
        logger.error(f"❌ خطأ في إنشاء مجلدات الرفع: {e}")

# إعداد التطبيق عند الإيقاف
@app.on_event("shutdown")
async def shutdown_event():
    """إعدادات إيقاف التشغيل"""
    logger.info("🛑 إيقاف تشغيل نظام مقارن المناهج التعليمية")

# استيراد وتسجيل الـ routers
from app.api.endpoints.upload import router as upload_router
from app.api.endpoints.compare import router as compare_router
from app.api.endpoints.websocket import router as websocket_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.advanced_processing import router as advanced_processing_router
from app.api.endpoints.ultra_fast_compare import router as ultra_fast_compare_router
from app.api.endpoints.multilingual_comparison import router as multilingual_router
from app.api.endpoints.smart_batch import router as smart_batch_router

app.include_router(upload_router, prefix=settings.API_V1_STR, tags=["upload"])
app.include_router(compare_router, prefix=settings.API_V1_STR, tags=["comparison"])
app.include_router(websocket_router, prefix=settings.API_V1_STR, tags=["websocket"])
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(ultra_fast_compare_router, prefix=settings.API_V1_STR, tags=["ultra-fast"])
app.include_router(advanced_processing_router, prefix=settings.API_V1_STR, tags=["advanced-processing"])
app.include_router(multilingual_router, prefix=f"{settings.API_V1_STR}/multilingual", tags=["multilingual"])
app.include_router(smart_batch_router, prefix=f"{settings.API_V1_STR}/smart-batch", tags=["smart-batch"])

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🔥 تشغيل الخادم مباشرة")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )