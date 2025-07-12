#!/usr/bin/env python3
"""
اختبار نظام استخراج النصوص ومقارنتها
Test script for image extraction and text comparison
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# إضافة مجلد التطبيق للـ Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

async def test_landingai_extraction():
    """اختبار استخراج النص من الصورة باستخدام LandingAI"""
    
    print("🚀 بدء اختبار نظام استخراج النصوص...")
    
    # مسار الصورة
    image_path = "../103.jpg"
    if not os.path.exists(image_path):
        print(f"❌ الصورة غير موجودة: {image_path}")
        return None
    
    print(f"📄 اختبار الصورة: {image_path}")
    print(f"📊 حجم الملف: {os.path.getsize(image_path) / 1024:.1f} KB")
    
    try:
        # استيراد خدمة LandingAI
        from app.services.landing_ai_service import landing_ai_service
        
        print("🔍 بدء استخراج النص باستخدام LandingAI...")
        
        # استخراج النص
        result = await landing_ai_service.extract_from_file(image_path)
        
        print(f"✅ اكتمل الاستخراج في {result.processing_time:.2f} ثانية")
        print(f"📈 نجح الاستخراج: {result.success}")
        
        if result.success:
            print(f"📝 طول النص المستخرج: {len(result.markdown_content)} حرف")
            print(f"🔢 عدد العناصر: {result.total_chunks}")
            print(f"🎯 درجة الثقة: {result.confidence_score:.2f}")
            
            # عرض جزء من النص المستخرج
            if result.markdown_content:
                print("\n📋 عينة من النص المستخرج:")
                print("-" * 50)
                # عرض أول 500 حرف
                preview = result.markdown_content[:500]
                print(preview)
                if len(result.markdown_content) > 500:
                    print(f"... (و {len(result.markdown_content) - 500} حرف إضافي)")
                print("-" * 50)
            
            # عرض التحليل المنظم إذا توفر
            if result.structured_analysis:
                print("\n📊 التحليل المنظم:")
                analysis = result.structured_analysis
                print(f"   📚 الموضوع: {analysis.subject}")
                print(f"   🎓 المستوى: {analysis.grade_level}")
                print(f"   📖 العنوان: {analysis.chapter_title}")
                print(f"   🎯 عدد الأهداف: {len(analysis.learning_objectives)}")
                print(f"   📝 عدد المواضيع: {len(analysis.topics)}")
                
                if analysis.learning_objectives:
                    print("   🎯 الأهداف التعليمية:")
                    for i, obj in enumerate(analysis.learning_objectives[:3], 1):
                        print(f"      {i}. {obj}")
        else:
            print(f"❌ فشل الاستخراج: {result.error_message}")
            
        return result
        
    except Exception as e:
        print(f"❌ خطأ في اختبار LandingAI: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_gemini_analysis(extracted_text):
    """اختبار تحليل النص باستخدام Gemini"""
    
    if not extracted_text:
        print("⚠️ لا يوجد نص لتحليله بـ Gemini")
        return None
    
    print("\n🧠 بدء تحليل النص باستخدام Gemini...")
    
    try:
        from app.services.gemini_service import gemini_service
        
        # إنشاء نص مقارنة تجريبي للاختبار
        test_old_text = "نص تجريبي قديم للمقارنة مع النص المستخرج"
        
        print("🔍 بدء المقارنة النصية...")
        
        # مقارنة النصوص
        comparison = await gemini_service.compare_texts(
            old_text=test_old_text,
            new_text=extracted_text,
            context={"content_type": "منهج تعليمي", "test_mode": True}
        )
        
        print(f"✅ اكتملت المقارنة في {comparison.processing_time:.2f} ثانية")
        print(f"📊 نسبة التشابه: {comparison.similarity_percentage:.1f}%")
        print(f"🎯 درجة الثقة: {comparison.confidence_score:.2f}")
        
        print(f"\n📝 ملخص التحليل:")
        print(f"   {comparison.summary}")
        
        print(f"\n💡 التوصية:")
        print(f"   {comparison.recommendation}")
        
        if comparison.content_changes:
            print(f"\n🔄 التغييرات المكتشفة:")
            for i, change in enumerate(comparison.content_changes[:3], 1):
                print(f"   {i}. {change}")
        
        return comparison
        
    except Exception as e:
        print(f"❌ خطأ في اختبار Gemini: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """الدالة الرئيسية للاختبار"""
    
    print("=" * 60)
    print("🎯 اختبار نظام مقارنة المناهج التعليمية")
    print("=" * 60)
    
    # اختبار استخراج النص
    extraction_result = await test_landingai_extraction()
    
    if extraction_result and extraction_result.success:
        # اختبار تحليل النص
        gemini_result = await test_gemini_analysis(extraction_result.markdown_content)
        
        print("\n" + "=" * 60)
        print("📈 نتائج الاختبار النهائية:")
        print("=" * 60)
        print(f"✅ LandingAI: {'نجح' if extraction_result.success else 'فشل'}")
        print(f"✅ Gemini: {'نجح' if gemini_result else 'فشل'}")
        print(f"⚡ الوقت الإجمالي: {extraction_result.processing_time + (gemini_result.processing_time if gemini_result else 0):.2f} ثانية")
        
        if extraction_result.success and gemini_result:
            print("🎉 النظام يعمل بنجاح!")
        else:
            print("⚠️ النظام يعمل جزئياً")
    else:
        print("\n❌ فشل الاختبار في مرحلة الاستخراج")
    
    print("=" * 60)

if __name__ == "__main__":
    # تشغيل الاختبار
    asyncio.run(main()) 