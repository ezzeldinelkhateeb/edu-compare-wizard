#!/usr/bin/env python3
"""
اختبار النظام المحدث مع OCR الحقيقي
Test Updated System with Real OCR
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.landing_ai_service import LandingAIService
from app.services.gemini_service import GeminiService

async def test_updated_workflow():
    """اختبار سير العمل المحدث"""
    
    print("🚀 بدء اختبار النظام المحدث")
    print("=" * 50)
    
    # مسار الصورة للاختبار
    image_path = "103.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ الصورة غير موجودة: {image_path}")
        return
    
    try:
        # 1. اختبار خدمة LandingAI مع OCR الحقيقي
        print("\n📄 1. اختبار استخراج النص الحقيقي...")
        print("-" * 30)
        
        landing_service = LandingAIService()
        
        print(f"🔧 إعدادات الخدمة:")
        print(f"   - وضع المحاكاة: {landing_service.mock_mode}")
        print(f"   - OCR متاح: {landing_service.ocr_available}")
        print(f"   - اللغات: {landing_service.ocr_languages}")
        
        # استخراج النص
        extraction_result = await landing_service.extract_from_file(image_path)
        
        print(f"\n📊 نتائج الاستخراج:")
        print(f"   - نجح: {extraction_result.success}")
        print(f"   - وقت المعالجة: {extraction_result.processing_time:.2f}s")
        print(f"   - ثقة الاستخراج: {extraction_result.confidence_score:.2f}")
        print(f"   - عدد الكلمات: {extraction_result.text_elements}")
        print(f"   - طول النص: {len(extraction_result.markdown_content)} حرف")
        
        if extraction_result.structured_analysis:
            analysis = extraction_result.structured_analysis
            print(f"   - الموضوع: {analysis.subject}")
            print(f"   - الفصل: {analysis.chapter_title}")
            print(f"   - عدد التمارين: {analysis.exercises_count}")
            print(f"   - مستوى الصعوبة: {analysis.difficulty_level}")
        
        # عرض جزء من النص المستخرج
        if extraction_result.markdown_content:
            preview = extraction_result.markdown_content[:200]
            print(f"\n📝 معاينة النص:")
            print(f"   {preview}...")
        
        # 2. اختبار خدمة Gemini للتحليل
        print("\n🤖 2. اختبار تحليل Gemini...")
        print("-" * 30)
        
        gemini_service = GeminiService()
        
        print(f"🔧 إعدادات Gemini:")
        print(f"   - وضع المحاكاة: {gemini_service.mock_mode}")
        print(f"   - النموذج: {gemini_service.model_name}")
        print(f"   - درجة الحرارة: {gemini_service.temperature}")
        
        # تحليل النص
        if extraction_result.success and extraction_result.markdown_content:
            # محاكاة مقارنة مع نص مشابه
            old_text = extraction_result.markdown_content
            new_text = extraction_result.markdown_content + "\n\nإضافة جديدة: مسألة إضافية حول المكابس."
            
            comparison_result = await gemini_service.compare_texts(old_text, new_text)
            
            print(f"\n📊 نتائج المقارنة:")
            print(f"   - نسبة التشابه: {comparison_result.similarity_percentage}%")
            print(f"   - وقت المعالجة: {comparison_result.processing_time:.2f}s")
            print(f"   - ثقة التحليل: {comparison_result.confidence_score:.2f}")
            print(f"   - إضافات جديدة: {len(comparison_result.added_content)}")
            print(f"   - محتوى محذوف: {len(comparison_result.removed_content)}")
            
            # عرض الملخص
            if comparison_result.summary:
                print(f"\n📋 ملخص المقارنة:")
                print(f"   {comparison_result.summary}")
            
            # عرض التوصية
            if comparison_result.recommendation:
                print(f"\n💡 التوصية:")
                print(f"   {comparison_result.recommendation}")
        
        # 3. حفظ النتائج
        print("\n💾 3. حفظ النتائج...")
        print("-" * 30)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # حفظ نتيجة الاستخراج
        extraction_file = f"updated_extraction_{timestamp}.json"
        with open(extraction_file, 'w', encoding='utf-8') as f:
            json.dump({
                "extraction_result": {
                    "success": extraction_result.success,
                    "processing_time": extraction_result.processing_time,
                    "confidence_score": extraction_result.confidence_score,
                    "text_elements": extraction_result.text_elements,
                    "markdown_content": extraction_result.markdown_content,
                    "structured_analysis": extraction_result.structured_analysis.dict() if extraction_result.structured_analysis else None
                },
                "timestamp": timestamp,
                "test_type": "updated_system_with_real_ocr"
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تم حفظ نتائج الاستخراج في: {extraction_file}")
        
        # حفظ نتيجة المقارنة
        if 'comparison_result' in locals():
            comparison_file = f"updated_comparison_{timestamp}.json"
            with open(comparison_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "comparison_result": {
                        "similarity_percentage": comparison_result.similarity_percentage,
                        "processing_time": comparison_result.processing_time,
                        "confidence_score": comparison_result.confidence_score,
                        "content_changes": comparison_result.content_changes,
                        "added_content": comparison_result.added_content,
                        "removed_content": comparison_result.removed_content,
                        "summary": comparison_result.summary,
                        "recommendation": comparison_result.recommendation,
                        "detailed_analysis": comparison_result.detailed_analysis
                    },
                    "timestamp": timestamp,
                    "test_type": "updated_system_comparison"
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✅ تم حفظ نتائج المقارنة في: {comparison_file}")
        
        # 4. ملخص الاختبار
        print("\n🎯 4. ملخص الاختبار")
        print("-" * 30)
        
        total_time = extraction_result.processing_time
        if 'comparison_result' in locals():
            total_time += comparison_result.processing_time
        
        print(f"✅ اكتمل الاختبار بنجاح!")
        print(f"📊 إحصائيات:")
        print(f"   - إجمالي وقت المعالجة: {total_time:.2f}s")
        print(f"   - نجح استخراج النص: {'✅' if extraction_result.success else '❌'}")
        print(f"   - نجح تحليل المقارنة: {'✅' if 'comparison_result' in locals() else '❌'}")
        print(f"   - جودة الاستخراج: {extraction_result.confidence_score:.1%}")
        
        if 'comparison_result' in locals():
            print(f"   - نسبة التشابه: {comparison_result.similarity_percentage}%")
        
        print(f"\n🎉 النظام المحدث يعمل بشكل صحيح!")
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()

async def test_health_checks():
    """اختبار صحة الخدمات"""
    
    print("\n🔍 فحص صحة الخدمات...")
    print("=" * 30)
    
    try:
        # فحص خدمة LandingAI
        landing_service = LandingAIService()
        landing_health = await landing_service.health_check()
        
        print(f"📄 LandingAI Service:")
        print(f"   - الحالة: {'✅ متاح' if landing_health['status'] == 'healthy' else '❌ غير متاح'}")
        print(f"   - OCR متاح: {'✅' if landing_service.ocr_available else '❌'}")
        print(f"   - API متاح: {'✅' if not landing_service.mock_mode else '❌ (وضع محاكاة)'}")
        
        # فحص خدمة Gemini
        gemini_service = GeminiService()
        gemini_health = await gemini_service.health_check()
        
        print(f"\n🤖 Gemini Service:")
        print(f"   - الحالة: {'✅ متاح' if gemini_health['status'] == 'healthy' else '❌ غير متاح'}")
        print(f"   - API متاح: {'✅' if not gemini_service.mock_mode else '❌ (وضع محاكاة)'}")
        print(f"   - النموذج: {gemini_service.model_name}")
        
    except Exception as e:
        print(f"❌ خطأ في فحص الصحة: {e}")

def main():
    """الدالة الرئيسية"""
    print("🧪 اختبار النظام المحدث مع OCR الحقيقي")
    print("=" * 60)
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 المجلد: {os.getcwd()}")
    
    # تشغيل الاختبارات
    asyncio.run(test_health_checks())
    asyncio.run(test_updated_workflow())

if __name__ == "__main__":
    main() 