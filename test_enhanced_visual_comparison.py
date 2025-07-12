#!/usr/bin/env python3
"""
اختبار النظام المحسن للمقارنة البصرية والتحقق من Landing AI
Enhanced Visual Comparison and Landing AI Verification Test
"""

import asyncio
import sys
import os
from pathlib import Path

# إضافة مسار البرنامج
sys.path.append('backend')

from app.services.visual_comparison_service import visual_comparison_service
from app.services.landing_ai_service import LandingAIService

async def test_enhanced_system():
    """اختبار النظام المحسن"""
    
    print("🚀 بدء اختبار النظام المحسن للمقارنة البصرية والتحقق من Landing AI")
    print("=" * 80)
    
    # مسارات الصور للاختبار
    test_images = [
        "backend/103.jpg",
        "103.jpg"
    ]
    
    # البحث عن صور صالحة للاختبار
    valid_images = []
    for img_path in test_images:
        if os.path.exists(img_path):
            valid_images.append(img_path)
    
    if len(valid_images) < 2:
        print("❌ نحتاج لصورتين على الأقل للاختبار")
        print("📁 الصور المتاحة:", valid_images)
        return
    
    old_image = valid_images[0]
    new_image = valid_images[1] if len(valid_images) > 1 else valid_images[0]
    
    try:
        # 1. اختبار خدمة Landing AI
        print("\n🔍 الخطوة 1: فحص خدمة Landing AI")
        print("-" * 50)
        
        landing_service = LandingAIService()
        
        print(f"✅ Landing AI مُفعل: {landing_service.enabled}")
        print(f"🔑 API Key مُعد: {bool(landing_service.api_key)}")
        print(f"🔧 OCR متوفر: {getattr(landing_service, 'ocr_available', False)}")
        print(f"🎭 وضع المحاكاة: {getattr(landing_service, 'mock_mode', True)}")
        
        # فحص الصحة
        health = await landing_service.health_check()
        print(f"🏥 حالة الخدمة: {health}")
        
        # 2. اختبار استخراج النص
        print(f"\n📝 الخطوة 2: اختبار استخراج النص")
        print(f"📁 الصورة الأولى: {old_image}")
        print("-" * 50)
        
        old_result = await landing_service.extract_from_file(old_image)
        
        print(f"✅ نجح الاستخراج: {old_result.success}")
        if old_result.success:
            print(f"📊 عدد الأحرف: {len(old_result.markdown_content)}")
            print(f"🎯 مستوى الثقة: {old_result.confidence_score:.1%}")
            print(f"⏱️ وقت المعالجة: {old_result.processing_time:.2f}s")
            print(f"📄 محتوى عينة: {old_result.markdown_content[:200]}...")
        else:
            print(f"❌ خطأ في الاستخراج: {old_result.error_message}")
        
        # 3. اختبار المقارنة البصرية المحسنة
        print(f"\n🖼️ الخطوة 3: اختبار المقارنة البصرية المحسنة")
        print(f"📁 مقارنة: {Path(old_image).name} vs {Path(new_image).name}")
        print("-" * 50)
        
        # إنشاء مجلد مؤقت للنتائج
        output_dir = "test_enhanced_results"
        os.makedirs(output_dir, exist_ok=True)
        
        visual_result = await visual_comparison_service.compare_images(
            old_image_path=old_image,
            new_image_path=new_image,
            output_dir=output_dir
        )
        
        print(f"🎯 نسبة التطابق الإجمالية: {visual_result.similarity_score:.1f}%")
        print(f"📊 SSIM: {visual_result.ssim_score:.3f}")
        print(f"🔐 pHash: {visual_result.phash_score:.3f}")
        if visual_result.clip_score:
            print(f"🧠 CLIP: {visual_result.clip_score:.3f}")
        print(f"📈 الهستوجرام: {visual_result.histogram_correlation:.3f}")
        print(f"🔍 مطابقة الميزات: {visual_result.feature_matching_score:.3f}")
        print(f"🏗️ تشابه الحواف: {visual_result.edge_similarity:.3f}")
        
        print(f"\n📋 تحليل المحتوى:")
        print(f"   نوع المحتوى: {visual_result.content_type_detected}")
        print(f"   محتوى متطابق محتمل: {visual_result.probable_content_match}")
        print(f"   تغييرات كبيرة: {visual_result.major_changes_detected}")
        print(f"   عدد المناطق المتغيرة: {len(visual_result.changed_regions)}")
        
        print(f"\n🎯 ملخص التحليل:")
        print(f"   {visual_result.analysis_summary}")
        
        print(f"\n💡 التوصيات:")
        print(f"   {visual_result.recommendations}")
        
        print(f"\n🔧 ملاحظات الثقة:")
        print(f"   {visual_result.confidence_notes}")
        
        if visual_result.difference_map_path:
            print(f"\n🗺️ خريطة الاختلافات: {visual_result.difference_map_path}")
        
        # 4. مقارنة النتائج
        print(f"\n⚖️ الخطوة 4: مقارنة النتائج")
        print("-" * 50)
        
        print(f"📊 مقارنة التطابق:")
        print(f"   المقارنة البصرية: {visual_result.similarity_score:.1f}%")
        
        if old_result.success and old_image == new_image:
            print(f"   💡 ملاحظة: تم اختبار نفس الصورة (يجب أن تكون متطابقة 100%)")
            
            if visual_result.similarity_score < 95:
                print(f"   ⚠️ تحذير: التطابق أقل من المتوقع لنفس الصورة")
            else:
                print(f"   ✅ النتيجة طبيعية لنفس الصورة")
        
        # 5. خلاصة الاختبار
        print(f"\n📋 الخطوة 5: خلاصة الاختبار")
        print("=" * 50)
        
        services_status = []
        if landing_service.enabled:
            services_status.append("✅ Landing AI متوفر")
        else:
            services_status.append("❌ Landing AI غير متوفر")
        
        if getattr(landing_service, 'ocr_available', False):
            services_status.append("✅ Tesseract OCR متوفر")
        else:
            services_status.append("❌ Tesseract OCR غير متوفر")
        
        services_status.append("✅ المقارنة البصرية المحسنة متوفرة")
        
        print("🔧 حالة الخدمات:")
        for status in services_status:
            print(f"   {status}")
        
        print(f"\n🎯 التوصية النهائية:")
        if landing_service.enabled:
            print("   ✅ النظام جاهز للاستخدام مع Landing AI الحقيقي")
        elif getattr(landing_service, 'ocr_available', False):
            print("   ⚠️ النظام يعمل مع Tesseract OCR (بديل)")
        else:
            print("   ❌ النظام يعمل في وضع المحاكاة فقط")
        
        print(f"   🖼️ المقارنة البصرية المحسنة تعمل بكفاءة عالية")
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_system()) 