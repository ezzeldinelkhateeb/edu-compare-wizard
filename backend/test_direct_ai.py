#!/usr/bin/env python3
"""
اختبار مباشر للصورة مع LandingAI وGemini
Direct test for image with LandingAI and Gemini
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# إضافة المسار للاستيراد
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_landingai_direct():
    """اختبار مباشر لـ LandingAI"""
    print("🚀 اختبار LandingAI مباشرة...")
    
    try:
        from app.services.landing_ai_service import landing_ai_service
        
        # مسار الصورة
        image_path = "../103.jpg"
        if not os.path.exists(image_path):
            print(f"❌ الصورة غير موجودة: {image_path}")
            return None
            
        print(f"📄 معالجة الصورة: {image_path}")
        print(f"📊 حجم الملف: {os.path.getsize(image_path) / 1024:.1f} KB")
        
        # استخراج النص
        print("🔍 بدء استخراج النص باستخدام LandingAI...")
        result = await landing_ai_service.extract_from_file(image_path)
        
        print(f"✅ اكتمل الاستخراج في {result.processing_time:.2f} ثانية")
        print(f"📈 نجح الاستخراج: {result.success}")
        
        if result.success:
            print(f"📝 طول النص المستخرج: {len(result.markdown_content)} حرف")
            print(f"🔢 عدد العناصر: {result.total_chunks}")
            print(f"🎯 درجة الثقة: {result.confidence_score:.2f}")
            
            # حفظ النص المستخرج
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # حفظ Markdown
            markdown_file = f"extraction_{timestamp}.md"
            with open(markdown_file, "w", encoding="utf-8") as f:
                f.write(result.markdown_content)
            print(f"💾 تم حفظ Markdown في: {markdown_file}")
            
            # حفظ JSON
            json_file = f"extraction_{timestamp}.json"
            json_data = {
                "success": result.success,
                "processing_time": result.processing_time,
                "confidence_score": result.confidence_score,
                "total_chunks": result.total_chunks,
                "markdown_content": result.markdown_content,
                "structured_analysis": result.structured_analysis.dict() if result.structured_analysis else None,
                "timestamp": datetime.now().isoformat()
            }
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"💾 تم حفظ JSON في: {json_file}")
            
            # عرض عينة من النص
            print("\n📋 عينة من النص المستخرج:")
            print("-" * 50)
            preview = result.markdown_content[:500]
            print(preview)
            if len(result.markdown_content) > 500:
                print(f"... (و {len(result.markdown_content) - 500} حرف إضافي)")
            print("-" * 50)
            
            return result.markdown_content
        else:
            print(f"❌ فشل الاستخراج: {result.error_message}")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في اختبار LandingAI: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_gemini_direct(extracted_text):
    """اختبار مباشر لـ Gemini"""
    if not extracted_text:
        print("⚠️ لا يوجد نص لتحليله بـ Gemini")
        return None
        
    print("\n🧠 اختبار Gemini مباشرة...")
    
    try:
        from app.services.gemini_service import gemini_service
        
        # إنشاء نص مقارنة تجريبي
        test_old_text = """
        # المنهج القديم - الرياضيات للصف الثالث
        
        ## الفصل الأول: الأعداد الطبيعية
        - فهم مفهوم الأعداد من 1 إلى 100
        - العمليات الحسابية الأساسية
        - حل المسائل البسيطة
        
        ## الفصل الثاني: الهندسة
        - الأشكال الهندسية الأساسية
        - حساب المحيط والمساحة
        """
        
        test_new_text = extracted_text[:1000]  # استخدام أول 1000 حرف من النص المستخرج
        
        print("🔍 بدء المقارنة النصية باستخدام Gemini...")
        print(f"📝 طول النص القديم: {len(test_old_text)} حرف")
        print(f"📝 طول النص الجديد: {len(test_new_text)} حرف")
        
        # مقارنة النصوص
        result = await gemini_service.compare_texts(test_old_text, test_new_text)
        
        print(f"✅ اكتملت المقارنة في {result.processing_time:.2f} ثانية")
        print(f"📊 نسبة التشابه: {result.similarity_percentage:.1f}%")
        print(f"🎯 درجة الثقة: {result.confidence_score:.2f}")
        
        # حفظ نتيجة المقارنة
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_file = f"comparison_{timestamp}.json"
        
        comparison_data = {
            "similarity_percentage": result.similarity_percentage,
            "confidence_score": result.confidence_score,
            "processing_time": result.processing_time,
            "summary": result.summary,
            "recommendation": result.recommendation,
            "content_changes": result.content_changes,
            "major_differences": result.major_differences,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(comparison_file, "w", encoding="utf-8") as f:
            json.dump(comparison_data, f, ensure_ascii=False, indent=2)
        print(f"💾 تم حفظ نتيجة المقارنة في: {comparison_file}")
        
        # عرض النتائج
        print("\n📝 ملخص التحليل:")
        print(f"   {result.summary}")
        
        print("\n💡 التوصية:")
        print(f"   {result.recommendation}")
        
        if result.content_changes:
            print("\n🔄 التغييرات المكتشفة:")
            for i, change in enumerate(result.content_changes, 1):
                print(f"   {i}. {change}")
        
        if result.major_differences:
            print("\n🔍 الاختلافات الرئيسية:")
            for i, diff in enumerate(result.major_differences, 1):
                print(f"   {i}. {diff}")
        
        return result
        
    except Exception as e:
        print(f"❌ خطأ في اختبار Gemini: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """الاختبار الرئيسي"""
    print("🎯 اختبار مباشر للصورة مع LandingAI وGemini")
    print("=" * 60)
    
    # اختبار LandingAI
    extracted_text = await test_landingai_direct()
    
    if extracted_text:
        # اختبار Gemini
        comparison_result = await test_gemini_direct(extracted_text)
        
        print("\n" + "=" * 60)
        print("📊 نتائج الاختبار النهائية:")
        print("=" * 60)
        
        if comparison_result:
            print("✅ LandingAI: نجح")
            print("✅ Gemini: نجح")
            print("🎉 النظام يعمل بنجاح!")
        else:
            print("✅ LandingAI: نجح")
            print("❌ Gemini: فشل")
            print("⚠️ LandingAI يعمل لكن Gemini يحتاج مراجعة")
    else:
        print("❌ LandingAI: فشل")
        print("❌ Gemini: لم يتم اختباره")
        print("⚠️ النظام يحتاج مراجعة")

if __name__ == "__main__":
    asyncio.run(main()) 