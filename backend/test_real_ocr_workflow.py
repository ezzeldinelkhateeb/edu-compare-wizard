#!/usr/bin/env python3
"""
اختبار شامل لسير العمل الحقيقي للـ OCR
Comprehensive test for real OCR workflow
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.landing_ai_service import LandingAIService
from app.services.gemini_service import GeminiService
from loguru import logger

# إعداد التسجيل
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

async def test_real_ocr_workflow():
    """اختبار سير العمل الحقيقي للـ OCR"""
    
    print("🚀 بدء اختبار سير العمل الحقيقي للـ OCR")
    print("=" * 60)
    
    # مسار الصورة الحقيقية
    image_path = "103.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ الصورة غير موجودة: {image_path}")
        return
    
    print(f"📸 استخدام الصورة: {image_path}")
    print(f"📊 حجم الملف: {os.path.getsize(image_path)} بايت")
    
    try:
        # 1. اختبار خدمة LandingAI
        print("\n🔍 الخطوة 1: اختبار استخراج النص باستخدام LandingAI")
        print("-" * 50)
        
        landing_service = LandingAIService()
        
        # فحص حالة الخدمة
        health = await landing_service.health_check()
        print(f"🏥 حالة LandingAI: {health['status']}")
        print(f"🎭 الوضع: {health.get('mode', 'unknown')}")
        
        # استخراج النص
        print("\n📝 بدء استخراج النص...")
        extraction_result = await landing_service.extract_from_file(image_path)
        
        if extraction_result.success:
            print(f"✅ نجح الاستخراج!")
            print(f"⏱️ وقت المعالجة: {extraction_result.processing_time:.2f} ثانية")
            print(f"🎯 مستوى الثقة: {extraction_result.confidence_score:.1%}")
            print(f"📊 عدد الكلمات: {extraction_result.text_elements}")
            print(f"📄 عدد الأجزاء: {extraction_result.total_chunks}")
            
            # عرض النص المستخرج
            print(f"\n📖 النص المستخرج ({len(extraction_result.markdown_content)} حرف):")
            print("-" * 40)
            print(extraction_result.markdown_content[:500] + "..." if len(extraction_result.markdown_content) > 500 else extraction_result.markdown_content)
            
            # عرض التحليل المنظم
            if extraction_result.structured_analysis:
                analysis = extraction_result.structured_analysis
                print(f"\n🧠 التحليل المنظم:")
                print(f"   📚 الموضوع: {analysis.subject}")
                print(f"   🎓 المستوى: {analysis.grade_level}")
                print(f"   📖 عنوان الفصل: {analysis.chapter_title}")
                print(f"   🎯 الأهداف: {len(analysis.learning_objectives)} هدف")
                print(f"   📝 المواضيع: {len(analysis.topics)} موضوع")
                print(f"   🔑 المفاهيم: {len(analysis.key_concepts)} مفهوم")
                print(f"   📊 مستوى الصعوبة: {analysis.difficulty_level}")
                print(f"   🌐 اللغة: {analysis.language}")
            
        else:
            print(f"❌ فشل الاستخراج: {extraction_result.error_message}")
            return
        
        # 2. اختبار خدمة Gemini
        print("\n🤖 الخطوة 2: اختبار تحليل النص باستخدام Gemini")
        print("-" * 50)
        
        gemini_service = GeminiService()
        
        # فحص حالة الخدمة
        gemini_health = await gemini_service.health_check()
        print(f"🏥 حالة Gemini: {gemini_health['status']}")
        print(f"🎭 الوضع: {gemini_health.get('mode', 'unknown')}")
        
        # تحليل النص المستخرج
        print("\n🧠 بدء تحليل النص...")
        
        # إنشاء نص مرجعي للمقارنة (نص مشابه)
        reference_text = """
        الفصل الأول: مقدمة في الرياضيات
        
        الأهداف التعليمية:
        - فهم مفهوم الأعداد الطبيعية
        - تطبيق العمليات الحسابية الأساسية
        - حل المسائل الرياضية البسيطة
        
        المحتوى:
        يتناول هذا الفصل المفاهيم الأساسية في الرياضيات والعمليات الحسابية.
        سنتعلم الجمع والطرح والضرب والقسمة مع أمثلة عملية.
        
        التمارين:
        1. احسب مجموع الأعداد من 1 إلى 10
        2. اوجد ناتج 15 × 7
        3. حل المعادلة س + 5 = 12
        """
        
        # مقارنة النص المستخرج مع النص المرجعي
        comparison_result = await gemini_service.compare_texts(
            reference_text,
            extraction_result.markdown_content
        )
        
        print(f"✅ اكتمل التحليل!")
        print(f"⏱️ وقت المعالجة: {comparison_result.processing_time:.2f} ثانية")
        print(f"🎯 نسبة التشابه: {comparison_result.similarity_percentage:.1f}%")
        print(f"📊 مستوى الثقة: {comparison_result.confidence_score:.1%}")
        
        # عرض الملخص
        print(f"\n📋 ملخص التحليل:")
        print("-" * 40)
        print(comparison_result.summary)
        
        # عرض التوصيات
        print(f"\n💡 التوصيات:")
        print("-" * 40)
        print(comparison_result.recommendation)
        
        # عرض التغييرات الرئيسية
        if comparison_result.major_differences:
            print(f"\n🔄 الاختلافات الرئيسية:")
            print("-" * 40)
            for i, diff in enumerate(comparison_result.major_differences[:5], 1):
                print(f"{i}. {diff}")
        
        # 3. حفظ النتائج
        print("\n💾 الخطوة 3: حفظ النتائج")
        print("-" * 50)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = f"test_results_{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        
        # حفظ النص المستخرج
        extracted_text_path = os.path.join(results_dir, "extracted_text.txt")
        with open(extracted_text_path, 'w', encoding='utf-8') as f:
            f.write(extraction_result.markdown_content)
        print(f"📄 النص المستخرج: {extracted_text_path}")
        
        # حفظ التحليل المنظم
        if extraction_result.structured_analysis:
            analysis_path = os.path.join(results_dir, "structured_analysis.json")
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(extraction_result.structured_analysis.model_dump(), f, ensure_ascii=False, indent=2)
            print(f"🧠 التحليل المنظم: {analysis_path}")
        
        # حفظ نتائج المقارنة
        comparison_path = os.path.join(results_dir, "comparison_results.json")
        with open(comparison_path, 'w', encoding='utf-8') as f:
            json.dump({
                "similarity_percentage": comparison_result.similarity_percentage,
                "confidence_score": comparison_result.confidence_score,
                "processing_time": comparison_result.processing_time,
                "summary": comparison_result.summary,
                "recommendation": comparison_result.recommendation,
                "major_differences": comparison_result.major_differences,
                "content_changes": comparison_result.content_changes,
                "statistics": {
                    "old_text_length": comparison_result.old_text_length,
                    "new_text_length": comparison_result.new_text_length,
                    "common_words_count": comparison_result.common_words_count,
                    "unique_old_words": comparison_result.unique_old_words,
                    "unique_new_words": comparison_result.unique_new_words
                }
            }, f, ensure_ascii=False, indent=2)
        print(f"🔄 نتائج المقارنة: {comparison_path}")
        
        # حفظ التقرير الكامل
        report_path = os.path.join(results_dir, "complete_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"""# تقرير اختبار سير العمل الحقيقي للـ OCR

## معلومات الاختبار
- **التاريخ**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **الصورة**: {image_path}
- **حجم الملف**: {os.path.getsize(image_path)} بايت

## نتائج استخراج النص (LandingAI)
- **الحالة**: {'نجح' if extraction_result.success else 'فشل'}
- **وقت المعالجة**: {extraction_result.processing_time:.2f} ثانية
- **مستوى الثقة**: {extraction_result.confidence_score:.1%}
- **عدد الكلمات**: {extraction_result.text_elements}
- **عدد الأجزاء**: {extraction_result.total_chunks}

### النص المستخرج
```
{extraction_result.markdown_content}
```

## نتائج تحليل النص (Gemini)
- **نسبة التشابه**: {comparison_result.similarity_percentage:.1f}%
- **مستوى الثقة**: {comparison_result.confidence_score:.1%}
- **وقت المعالجة**: {comparison_result.processing_time:.2f} ثانية

### الملخص
{comparison_result.summary}

### التوصيات
{comparison_result.recommendation}

### الاختلافات الرئيسية
""")
            
            for i, diff in enumerate(comparison_result.major_differences, 1):
                f.write(f"{i}. {diff}\n")
        
        print(f"📊 التقرير الكامل: {report_path}")
        
        print(f"\n🎉 تم حفظ جميع النتائج في: {results_dir}")
        
        # 4. ملخص النتائج
        print("\n📊 ملخص النتائج")
        print("=" * 60)
        print(f"✅ استخراج النص: {'نجح' if extraction_result.success else 'فشل'}")
        print(f"✅ تحليل النص: {'نجح' if comparison_result else 'فشل'}")
        print(f"📈 نسبة التشابه: {comparison_result.similarity_percentage:.1f}%")
        print(f"🎯 متوسط الثقة: {(extraction_result.confidence_score + comparison_result.confidence_score) / 2:.1%}")
        print(f"⏱️ إجمالي وقت المعالجة: {extraction_result.processing_time + comparison_result.processing_time:.2f} ثانية")
        
        return {
            "extraction_result": extraction_result,
            "comparison_result": comparison_result,
            "results_dir": results_dir
        }
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        logger.exception("خطأ في اختبار سير العمل")
        return None

async def main():
    """الدالة الرئيسية"""
    print("🔬 اختبار سير العمل الحقيقي للـ OCR مع الصورة 103.jpg")
    print("=" * 80)
    
    result = await test_real_ocr_workflow()
    
    if result:
        print("\n🎉 تم إكمال الاختبار بنجاح!")
        print(f"📁 النتائج محفوظة في: {result['results_dir']}")
    else:
        print("\n❌ فشل في الاختبار")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 