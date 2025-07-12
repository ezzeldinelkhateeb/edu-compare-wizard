#!/usr/bin/env python3
"""
اختبار اتصال LandingAI
Test LandingAI Connection
"""

import os
import sys
import asyncio
from pathlib import Path

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.landing_ai_service import LandingAIService
from app.core.config import get_settings

async def test_landing_ai():
    """اختبار اتصال LandingAI مع الصورة المحددة"""
    print("🧪 بدء اختبار اتصال LandingAI...")
    
    # مسار الصورة المحددة
    image_path = "103.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ الصورة غير موجودة: {image_path}")
        return False
    
    print(f"📸 الصورة الموجودة: {image_path}")
    
    try:
        # إنشاء خدمة LandingAI
        settings = get_settings()
        landing_service = LandingAIService()
        
        print("🔍 تحقق من API Key...")
        if hasattr(settings, 'VISION_AGENT_API_KEY') and settings.VISION_AGENT_API_KEY:
            print("✅ API Key موجود")
        else:
            print("⚠️ API Key غير موجود - سيتم استخدام OCR المحلي")
        
        print(f"🚀 بدء استخراج النص من: {image_path}")
        
        # استخراج النص من الصورة
        result = await landing_service.extract_from_file(image_path)
        
        print("📊 نتائج الاستخراج:")
        print(f"   ✅ نجح: {result.success}")
        print(f"   📝 النص: {result.markdown_content[:100]}...")
        print(f"   🎯 الثقة: {result.confidence_score:.2%}")
        print(f"   📁 الملف: {result.file_name}")
        print(f"   ⏱️ وقت المعالجة: {result.processing_time:.2f}s")
        
        # تفاصيل إضافية
        if result.structured_analysis:
            analysis = result.structured_analysis
            print("🎓 تحليل المحتوى التعليمي:")
            print(f"   📚 الموضوع: {analysis.subject}")
            print(f"   🎯 عدد الأهداف: {len(analysis.learning_objectives)}")
            print(f"   📝 عدد المواضيع: {len(analysis.topics)}")
            print(f"   💡 المفاهيم الأساسية: {len(analysis.key_concepts)}")
        
        # إحصائيات العناصر
        print("📊 إحصائيات العناصر:")
        print(f"   📝 نصوص: {result.text_elements}")
        print(f"   📋 جداول: {result.table_elements}")
        print(f"   🖼️ صور: {result.image_elements}")
        print(f"   📖 عناوين: {result.title_elements}")
        print(f"   📦 إجمالي القطع: {result.total_chunks}")
        
        # اختبار معالجة متقدمة إذا كانت متوفرة
        print("\n🔬 اختبار المعالجة المتقدمة...")
        try:
            advanced_result = await landing_service.extract_from_multiple_files([image_path])
            print("✅ المعالجة المتقدمة نجحت")
            print(f"   📁 عدد الملفات المعالجة: {len(advanced_result)}")
        except Exception as e:
            print(f"⚠️ المعالجة المتقدمة غير متوفرة: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار LandingAI: {e}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 اختبار اتصال LandingAI")
    print("=" * 50)
    
    success = asyncio.run(test_landing_ai())
    
    print("\n" + "=" * 50)
    if success:
        print("✅ اختبار LandingAI مكتمل بنجاح!")
    else:
        print("❌ فشل اختبار LandingAI!")
    print("=" * 50) 