"""
اختبار متكامل للخدمات الحقيقية
Test all real API services together
"""

import os
import asyncio
from pathlib import Path
from datetime import datetime

from app.services.landing_ai_service import LandingAIService
from app.services.gemini_service import GeminiService
from app.services.visual_comparison_service import VisualComparisonService

# تكوين المسارات
CURRENT_DIR = Path(__file__).parent
TEST_IMAGE = CURRENT_DIR / "103.jpg"
OUTPUT_DIR = CURRENT_DIR / "test_results"

async def test_all_services():
    """اختبار جميع الخدمات معاً"""
    print("🎯 اختبار الخدمات الحقيقية")
    print("=" * 60)

    # 1. إنشاء مجلد النتائج
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 2. تهيئة الخدمات
    landing_service = LandingAIService()
    gemini_service = GeminiService()
    visual_service = VisualComparisonService()
    
    print("\n🔷 اختبار LandingAI Service")
    print("=" * 60)
    
    try:
        # استخراج النص من الصورة
        result = await landing_service.extract_from_file(
            str(TEST_IMAGE),
            str(OUTPUT_DIR)
        )
        print(f"✅ نجح استخراج النص: {len(result.markdown_content)} حرف")
        print(f"⏱️  وقت المعالجة: {result.processing_time:.2f}s")
        print(f"📊 درجة الثقة: {result.confidence_score:.2%}")
        
        if result.structured_analysis:
            print("\n📝 التحليل الهيكلي:")
            print(f"- الموضوع: {result.structured_analysis.subject}")
            print(f"- المستوى: {result.structured_analysis.grade_level}")
            print(f"- عدد الأهداف: {len(result.structured_analysis.learning_objectives)}")
            print(f"- عدد المواضيع: {len(result.structured_analysis.topics)}")
            print(f"- عدد المفاهيم: {len(result.structured_analysis.key_concepts)}")
    
    except Exception as e:
        print(f"❌ خطأ في LandingAI: {e}")
    
    print("\n🔶 اختبار Gemini Service")
    print("=" * 60)
    
    try:
        # نص للاختبار
        old_text = "مرحباً! هذا نص تجريبي للاختبار."
        new_text = "مرحباً! هذا نص معدل للاختبار مع بعض الإضافات."
        
        result = await gemini_service.compare_texts(old_text, new_text)
        print(f"✅ نجحت المقارنة النصية")
        print(f"⏱️  وقت المعالجة: {result.processing_time:.2f}s")
        print(f"📊 نسبة التشابه: {result.similarity_percentage:.1f}%")
        print(f"\n📝 ملخص التحليل:")
        print(result.summary)
    
    except Exception as e:
        print(f"❌ خطأ في Gemini: {e}")
    
    print("\n🔷 اختبار Visual Comparison Service")
    print("=" * 60)
    
    try:
        # مقارنة الصورة مع نفسها (للاختبار)
        result = await visual_service.compare_images(
            str(TEST_IMAGE),
            str(TEST_IMAGE),
            str(OUTPUT_DIR)
        )
        print(f"✅ نجحت المقارنة البصرية")
        print(f"⏱️  وقت المعالجة: {result.processing_time:.2f}s")
        print(f"📊 درجة التشابه: {result.similarity_score:.1f}%")
        print(f"- SSIM: {result.ssim_score:.3f}")
        print(f"- pHash: {result.phash_score:.3f}")
        if result.clip_score:
            print(f"- CLIP: {result.clip_score:.3f}")
    
    except Exception as e:
        print(f"❌ خطأ في المقارنة البصرية: {e}")
    
    print("\n📋 تقرير النتائج النهائي")
    print("=" * 60)
    
    # فحص صحة الخدمات
    landing_health = await landing_service.health_check()
    gemini_health = await gemini_service.health_check()
    visual_health = await visual_service.health_check()
    
    print(f"LandingAI Service: {'✅' if landing_health['status'] == 'ok' else '❌'}")
    print(f"Gemini Service: {'✅' if gemini_health['status'] == 'ok' else '❌'}")
    print(f"Visual Service: {'✅' if visual_health['status'] == 'ok' else '❌'}")

if __name__ == "__main__":
    asyncio.run(test_all_services()) 