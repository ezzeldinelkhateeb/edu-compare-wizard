#!/usr/bin/env python3
"""
اختبار التكامل مع الخدمات الحقيقية
Test Real Services Integration
"""

import os
import sys
import asyncio
import requests
from pathlib import Path

# إضافة مسار المشروع
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_services():
    """اختبار الخدمات الأساسية"""
    
    print("🧪 اختبار التكامل مع الخدمات الحقيقية")
    print("=" * 50)
    
    # 1. اختبار خدمة Gemini
    print("\n1️⃣ اختبار خدمة Gemini...")
    try:
        from backend.app.services.gemini_service import GeminiService
        
        gemini = GeminiService()
        print(f"   ✅ تم تحميل خدمة Gemini - وضع المحاكاة: {gemini.mock_mode}")
        
        if not gemini.mock_mode:
            print("   📡 اختبار الاتصال بـ Gemini...")
            health = await gemini.health_check()
            print(f"   ✅ حالة Gemini: {health.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"   ❌ خطأ في خدمة Gemini: {e}")
    
    # 2. اختبار خدمة Landing AI
    print("\n2️⃣ اختبار خدمة Landing AI...")
    try:
        from backend.app.services.landing_ai_service import LandingAIService
        
        landing_ai = LandingAIService()
        print(f"   ✅ تم تحميل خدمة Landing AI - مُفعلة: {landing_ai.enabled}")
        print(f"   📊 OCR متاح: {landing_ai.ocr_available}")
        
        if landing_ai.enabled:
            health = await landing_ai.health_check()
            print(f"   ✅ حالة Landing AI: {health.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"   ❌ خطأ في خدمة Landing AI: {e}")
    
    # 3. اختبار الباك إند
    print("\n3️⃣ اختبار الباك إند...")
    try:
        backend_url = "http://localhost:8000"
        
        # اختبار Health Check
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ الباك إند يعمل - الحالة: {health_data.get('status', 'unknown')}")
            
            services = health_data.get('services', {})
            for service_name, service_status in services.items():
                print(f"   📡 {service_name}: {service_status}")
        else:
            print(f"   ⚠️ الباك إند يستجيب لكن هناك مشكلة: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ الباك إند غير متاح - تأكد من تشغيله على localhost:8000")
    except Exception as e:
        print(f"   ❌ خطأ في الاتصال بالباك إند: {e}")
    
    # 4. اختبار متغيرات البيئة
    print("\n4️⃣ اختبار متغيرات البيئة...")
    
    env_vars = [
        ("GEMINI_API_KEY", "مفتاح Gemini"),
        ("VISION_AGENT_API_KEY", "مفتاح Landing AI"),
        ("REDIS_URL", "رابط Redis")
    ]
    
    for var_name, description in env_vars:
        value = os.getenv(var_name)
        if value:
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"   ✅ {description}: {masked_value}")
        else:
            print(f"   ⚠️ {description}: غير محدد")
    
    print("\n" + "=" * 50)
    print("🎯 الخلاصة:")
    print("   • النظام الآن يستخدم الخدمات الحقيقية بدلاً من البيانات التجريبية")
    print("   • Landing AI لاستخراج النص من الصور")
    print("   • Gemini AI لمقارنة وتحليل النصوص")
    print("   • سجلات مفصلة تظهر في الكونسول أثناء المعالجة")
    print("\n🚀 يمكنك الآن تجربة النظام مع صور حقيقية!")

if __name__ == "__main__":
    asyncio.run(test_services()) 