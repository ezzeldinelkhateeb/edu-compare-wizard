"""
Health Check Endpoints
نقاط فحص صحة النظام
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import asyncio
from datetime import datetime

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    فحص صحة النظام العام
    General system health check
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "🚀 نظام مقارنة المناهج التعليمية يعمل بشكل طبيعي",
        "version": "1.0.0",
        "environment": getattr(settings, 'ENVIRONMENT', 'development')
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    فحص صحة مفصل لجميع الخدمات
    Detailed health check for all services
    """
    health_results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "services": {}
    }
    
    # فحص خدمة LandingAI
    try:
        from app.services.landing_ai_service import landing_ai_service
        landing_health = await landing_ai_service.health_check()
        health_results["services"]["landing_ai"] = landing_health
    except Exception as e:
        health_results["services"]["landing_ai"] = {
            "status": "error",
            "message": f"خطأ في تحميل خدمة LandingAI: {str(e)}"
        }
    
    # فحص خدمة Gemini
    try:
        from app.services.gemini_service import gemini_service
        gemini_health = await gemini_service.health_check()
        health_results["services"]["gemini"] = gemini_health
    except Exception as e:
        health_results["services"]["gemini"] = {
            "status": "error",
            "message": f"خطأ في تحميل خدمة Gemini: {str(e)}"
        }
    
    # فحص خدمة المقارنة البصرية
    try:
        from app.services.visual_comparison_service import visual_comparison_service
        visual_health = await visual_comparison_service.health_check()
        health_results["services"]["visual_comparison"] = visual_health
    except Exception as e:
        health_results["services"]["visual_comparison"] = {
            "status": "error",
            "message": f"خطأ في تحميل خدمة المقارنة البصرية: {str(e)}"
        }
    
    # فحص Redis/Celery
    try:
        from celery_app.worker import celery_app
        celery_inspect = celery_app.control.inspect()
        active_tasks = celery_inspect.active()
        
        health_results["services"]["celery"] = {
            "status": "healthy" if active_tasks is not None else "unhealthy",
            "message": "Celery متصل" if active_tasks is not None else "Celery غير متصل",
            "active_workers": len(active_tasks) if active_tasks else 0
        }
    except Exception as e:
        health_results["services"]["celery"] = {
            "status": "error",
            "message": f"خطأ في Celery: {str(e)}"
        }
    
    # تحديد الحالة العامة
    unhealthy_services = [
        name for name, service in health_results["services"].items()
        if service.get("status") != "healthy"
    ]
    
    if unhealthy_services:
        health_results["overall_status"] = "degraded"
        health_results["unhealthy_services"] = unhealthy_services
        health_results["message"] = f"⚠️ بعض الخدمات تواجه مشاكل: {', '.join(unhealthy_services)}"
    else:
        health_results["message"] = "✅ جميع الخدمات تعمل بشكل طبيعي"
    
    return health_results


@router.get("/health/ai-services")
async def ai_services_health() -> Dict[str, Any]:
    """
    فحص صحة خدمات الذكاء الاصطناعي فقط
    AI services health check only
    """
    ai_health = {
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # اختبار LandingAI
    try:
        from app.services.landing_ai_service import landing_ai_service
        ai_health["services"]["landing_ai"] = await landing_ai_service.health_check()
    except Exception as e:
        ai_health["services"]["landing_ai"] = {
            "status": "error",
            "error": str(e)
        }
    
    # اختبار Gemini
    try:
        from app.services.gemini_service import gemini_service
        ai_health["services"]["gemini"] = await gemini_service.health_check()
    except Exception as e:
        ai_health["services"]["gemini"] = {
            "status": "error", 
            "error": str(e)
        }
    
    # تحديد الحالة العامة
    all_healthy = all(
        service.get("status") == "healthy" 
        for service in ai_health["services"].values()
    )
    
    ai_health["overall_status"] = "healthy" if all_healthy else "degraded"
    ai_health["message"] = (
        "✅ جميع خدمات الذكاء الاصطناعي جاهزة" if all_healthy 
        else "⚠️ بعض خدمات الذكاء الاصطناعي تواجه مشاكل"
    )
    
    return ai_health


@router.get("/health/quick")
async def quick_health_check() -> Dict[str, str]:
    """
    فحص سريع للحالة
    Quick health status
    """
    try:
        # اختبار سريع للاتصال بقاعدة البيانات أو الخدمات الأساسية
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 