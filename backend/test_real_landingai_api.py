#!/usr/bin/env python3
"""
اختبار شامل لخدمة LandingAI الحقيقية
Comprehensive Test for Real LandingAI Service
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# إضافة مجلد app إلى مسار Python
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.services.landing_ai_service import LandingAIService

def print_separator(title: str):
    """طباعة فاصل مع عنوان"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

async def test_real_landingai_extraction():
    """اختبار استخراج النص الحقيقي باستخدام LandingAI API"""
    
    print_separator("🧪 اختبار LandingAI API الحقيقي")
    
    # إنشاء خدمة LandingAI
    service = LandingAIService()
    
    # التحقق من وجود API key
    if service.mock_mode:
        print("❌ الخدمة في وضع المحاكاة - تحقق من API key")
        return False
    
    print(f"✅ تم تكوين LandingAI بنجاح")
    print(f"📡 API Endpoint: {service.api_endpoint}")
    print(f"🔑 API Key: {service.api_key[:20]}...")
    
    # البحث عن ملف اختبار
    test_image = "103.jpg"
    if not os.path.exists(test_image):
        print(f"❌ لم يتم العثور على ملف الاختبار: {test_image}")
        return False
    
    print(f"📁 ملف الاختبار: {test_image}")
    print(f"📏 حجم الملف: {os.path.getsize(test_image) / 1024:.1f} KB")
    
    # إنشاء مجلد للنتائج
    session_dir = f"test_landingai_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(session_dir, exist_ok=True)
    
    try:
        print("\n🚀 بدء عملية الاستخراج...")
        start_time = datetime.now()
        
        # تشغيل الاستخراج
        result = await service.extract_from_file(
            file_path=test_image,
            output_dir=session_dir
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print_separator("📊 نتائج الاستخراج")
        
        if result.success:
            print("✅ نجح الاستخراج!")
            print(f"⏱️  وقت المعالجة: {processing_time:.2f} ثانية")
            print(f"📄 طول المحتوى: {len(result.markdown_content)} حرف")
            print(f"🔢 عدد القطع: {result.total_chunks}")
            print(f"📈 نقاط الثقة: {result.confidence_score:.2%}")
            
            print(f"\n📋 توزيع العناصر:")
            print(f"  • نصوص: {result.text_elements}")
            print(f"  • جداول: {result.table_elements}")
            print(f"  • صور: {result.image_elements}")
            print(f"  • عناوين: {result.title_elements}")
            
            # عرض عينة من المحتوى
            print(f"\n📝 عينة من المحتوى المستخرج:")
            content_preview = result.markdown_content[:500]
            print(f"{'─'*50}")
            print(content_preview)
            if len(result.markdown_content) > 500:
                print(f"... (و {len(result.markdown_content) - 500} حرف إضافي)")
            print(f"{'─'*50}")
            
            # تحليل المحتوى التعليمي
            if result.structured_analysis:
                print(f"\n🎓 التحليل التعليمي:")
                analysis = result.structured_analysis
                print(f"  • الموضوع: {getattr(analysis, 'subject', 'غير محدد')}")
                print(f"  • عدد الأهداف: {len(getattr(analysis, 'objectives', []))}")
                print(f"  • عدد المواضيع: {len(getattr(analysis, 'topics', []))}")
                print(f"  • المفاهيم الرئيسية: {len(getattr(analysis, 'key_concepts', []))}")
                
                if hasattr(analysis, 'objectives') and analysis.objectives:
                    print(f"\n🎯 الأهداف التعليمية:")
                    for i, obj in enumerate(analysis.objectives[:3], 1):
                        print(f"  {i}. {obj}")
            
            # معلومات الملفات المحفوظة
            print(f"\n💾 الملفات المحفوظة:")
            if result.raw_json_path and os.path.exists(result.raw_json_path):
                print(f"  • JSON الخام: {result.raw_json_path}")
                print(f"    حجم: {os.path.getsize(result.raw_json_path)} بايت")
            
            markdown_file = os.path.join(session_dir, "extracted_content.md")
            if os.path.exists(markdown_file):
                print(f"  • ملف Markdown: {markdown_file}")
                print(f"    حجم: {os.path.getsize(markdown_file)} بايت")
            
            print_separator("✅ نجح الاختبار!")
            return True
            
        else:
            print("❌ فشل في الاستخراج")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_gemini_real_api():
    """اختبار Gemini API الحقيقي"""
    
    print_separator("🧪 اختبار Gemini AI الحقيقي")
    
    # استيراد خدمة Gemini
    from app.services.gemini_service import GeminiService
    
    service = GeminiService()
    
    if service.mock_mode:
        print("❌ خدمة Gemini في وضع المحاكاة - تحقق من API key")
        return False
    
    print(f"✅ تم تكوين Gemini بنجاح")
    print(f"🤖 النموذج: {service.model_name}")
    print(f"🌡️  درجة الحرارة: {service.temperature}")
    
    # نصوص تجريبية للمقارنة
    old_text = """
    الوحدة الأولى: الفيزياء
    الهدف الأول: فهم قوانين نيوتن
    الهدف الثاني: دراسة الحركة
    
    المفاهيم الأساسية:
    - القوة والكتلة
    - التسارع
    - قانون الجاذبية
    """
    
    new_text = """
    الوحدة الأولى: الفيزياء التطبيقية
    الهدف الأول: إتقان قوانين نيوتن الثلاثة
    الهدف الثاني: تحليل أنواع الحركة المختلفة
    الهدف الثالث: تطبيق المفاهيم عملياً
    
    المفاهيم الأساسية:
    - القوة والكتلة والتسارع
    - قوانين الحركة
    - الجاذبية والوزن
    - التطبيقات العملية
    """
    
    try:
        print("\n🚀 بدء عملية المقارنة...")
        start_time = datetime.now()
        
        result = await service.compare_texts(old_text, new_text)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print_separator("📊 نتائج المقارنة")
        
        if result:
            print("✅ نجحت المقارنة!")
            print(f"⏱️  وقت المعالجة: {processing_time:.2f} ثانية")
            print(f"📊 نسبة التشابه: {result.similarity_percentage:.1f}%")
            print(f"🔧 الخدمة المستخدمة: {result.service_used}")
            
            print(f"\n📝 ملخص التغييرات:")
            print(f"  • التغييرات في المحتوى: {len(result.content_changes)}")
            print(f"  • التغييرات في الأسئلة: {len(result.questions_changes)}")
            print(f"  • التغييرات في الأمثلة: {len(result.examples_changes)}")
            print(f"  • الاختلافات الكبيرة: {len(result.major_differences)}")
            
            if result.content_changes:
                print(f"\n🔄 أهم التغييرات:")
                for i, change in enumerate(result.content_changes[:3], 1):
                    print(f"  {i}. {change}")
            
            if result.recommendation:
                print(f"\n💡 التوصية:")
                print(f"  {result.recommendation}")
            
            if result.summary:
                print(f"\n📋 ملخص:")
                print(f"  {result.summary}")
            
            print_separator("✅ نجح اختبار Gemini!")
            return True
            
        else:
            print("❌ فشل في المقارنة")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في اختبار Gemini: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """تشغيل جميع الاختبارات"""
    
    print_separator("🎯 اختبار شامل للخدمات الحقيقية")
    print("🔧 اختبار LandingAI و Gemini مع API Keys حقيقية")
    
    results = []
    
    # اختبار LandingAI
    landingai_success = await test_real_landingai_extraction()
    results.append(("LandingAI API", landingai_success))
    
    await asyncio.sleep(2)  # استراحة قصيرة
    
    # اختبار Gemini
    gemini_success = await test_gemini_real_api()
    results.append(("Gemini AI", gemini_success))
    
    # تقرير النتائج النهائي
    print_separator("📋 تقرير النتائج النهائي")
    
    all_success = True
    for service_name, success in results:
        status = "✅ نجح" if success else "❌ فشل"
        print(f"{status} {service_name}")
        if not success:
            all_success = False
    
    print(f"\n{'='*60}")
    if all_success:
        print("🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام مع APIs حقيقية")
    else:
        print("⚠️  بعض الاختبارات فشلت - تحقق من التفاصيل أعلاه")
    print(f"{'='*60}")
    
    return all_success

if __name__ == "__main__":
    # تشغيل الاختبارات
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 