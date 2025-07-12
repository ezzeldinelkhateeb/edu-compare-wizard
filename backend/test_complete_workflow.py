#!/usr/bin/env python3
"""
اختبار شامل لسير العمل الكامل
Complete Workflow Test
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# إضافة المسار للاستيراد
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.landing_ai_service import LandingAIService
from app.services.gemini_service import GeminiService

async def test_complete_workflow():
    """اختبار سير العمل الكامل"""
    
    # مسار الصورة
    image_path = Path("../103.jpg")
    if not image_path.exists():
        print(f"❌ الصورة غير موجودة: {image_path.absolute()}")
        return False
    
    print(f"🖼️ بدء اختبار الصورة: {image_path.absolute()}")
    
    try:
        # 1. اختبار LandingAI Service
        print("\n📡 اختبار LandingAI Service...")
        landing_ai = LandingAIService()
        
        # قراءة الصورة
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        print(f"📊 حجم الصورة: {len(image_data)} bytes")
        
        # استخراج النص من الصورة
        print("🔍 استخراج النص من الصورة...")
        extraction_result = await landing_ai.extract_from_file(
            file_path=str(image_path.absolute())
        )
        
        if not extraction_result or not extraction_result.success:
            error_msg = extraction_result.error_message if extraction_result else "فشل غير معروف"
            print(f"❌ فشل في استخراج النص من LandingAI: {error_msg}")
            return False
        
        print("✅ تم استخراج النص بنجاح من LandingAI")
        print(f"📄 عدد الأحرف المستخرجة: {len(extraction_result.markdown_content)}")
        print(f"⏱️ وقت المعالجة: {extraction_result.processing_time:.2f} ثانية")
        print(f"📊 إجمالي العناصر: {extraction_result.total_chunks}")
        
        # حفظ نتيجة LandingAI
        landing_result_file = "landing_ai_result.json"
        result_dict = extraction_result.model_dump()
        with open(landing_result_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        print(f"💾 تم حفظ نتيجة LandingAI في: {landing_result_file}")
        
        # حفظ ملف Markdown المستخرج
        markdown_file = "landing_ai_result.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(extraction_result.markdown_content)
        print(f"📝 تم حفظ ملف Markdown في: {markdown_file}")
        
        # إنشاء تقرير تفصيلي
        report_content = f"""# تقرير استخراج LandingAI - 103.jpg

## معلومات الملف
- **اسم الملف**: {extraction_result.file_name}
- **حجم الملف**: {len(image_data)} bytes
- **وقت المعالجة**: {extraction_result.processing_time:.2f} ثانية
- **حالة الاستخراج**: {'نجح' if extraction_result.success else 'فشل'}

## إحصائيات الاستخراج
- **إجمالي العناصر**: {extraction_result.total_chunks}
- **عناصر النص**: {extraction_result.text_elements}
- **عناصر الجداول**: {extraction_result.table_elements}
- **عناصر الصور**: {extraction_result.image_elements}
- **عناصر العناوين**: {extraction_result.title_elements}
- **نقاط الثقة**: {extraction_result.confidence_score:.2f}

## العناصر حسب النوع
{json.dumps(extraction_result.chunks_by_type, ensure_ascii=False, indent=2)}

## المحتوى المستخرج
{extraction_result.markdown_content}

---
*تم إنشاء هذا التقرير تلقائياً في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        report_file = "landing_ai_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"📋 تم حفظ التقرير التفصيلي في: {report_file}")
        
        # 2. اختبار Gemini Service
        print("\n🤖 اختبار Gemini Service...")
        gemini = GeminiService()
        
        extracted_text = extraction_result.markdown_content
        if not extracted_text.strip():
            print("⚠️ لا يوجد نص مستخرج لإرساله إلى Gemini")
            return True  # LandingAI نجح، لكن لا يوجد نص
        
        print(f"📤 إرسال النص إلى Gemini (عدد الأحرف: {len(extracted_text)})")
        
        # تحليل النص باستخدام Gemini
        analysis_prompt = f"""
        يرجى تحليل النص التالي المستخرج من صورة:
        
        النص:
        {extracted_text}
        
        يرجى تقديم:
        1. ملخص للمحتوى
        2. الموضوع الرئيسي
        3. أي معلومات مهمة
        4. تقييم جودة النص المستخرج
        """
        
        gemini_result = await gemini.analyze_text(analysis_prompt)
        
        if not gemini_result:
            print("❌ فشل في تحليل النص باستخدام Gemini")
            return False
        
        print("✅ تم تحليل النص بنجاح باستخدام Gemini")
        
        # حفظ نتيجة Gemini
        gemini_result_data = {
            "original_text": extracted_text,
            "analysis": gemini_result,
            "timestamp": datetime.now().isoformat(),
            "source_file": "103.jpg",
            "processing_time": extraction_result.processing_time,
            "extraction_stats": {
                "total_chunks": extraction_result.total_chunks,
                "confidence_score": extraction_result.confidence_score,
                "text_elements": extraction_result.text_elements
            }
        }
        
        gemini_result_file = "gemini_analysis_result.json"
        with open(gemini_result_file, 'w', encoding='utf-8') as f:
            json.dump(gemini_result_data, f, ensure_ascii=False, indent=2)
        print(f"💾 تم حفظ نتيجة Gemini في: {gemini_result_file}")
        
        # إنشاء ملف Markdown للتحليل
        analysis_markdown = f"""# تحليل النص - Gemini AI

## معلومات المصدر
- **الملف الأصلي**: 103.jpg
- **طريقة الاستخراج**: LandingAI
- **تاريخ التحليل**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **وقت معالجة LandingAI**: {extraction_result.processing_time:.2f} ثانية
- **نقاط الثقة**: {extraction_result.confidence_score:.2f}

## إحصائيات الاستخراج
- **إجمالي العناصر**: {extraction_result.total_chunks}
- **عناصر النص**: {extraction_result.text_elements}
- **عناصر الجداول**: {extraction_result.table_elements}
- **عناصر الصور**: {extraction_result.image_elements}

## النص الأصلي المستخرج
```
{extracted_text}
```

## تحليل Gemini AI
{gemini_result}

---
*تم إنشاء هذا التقرير تلقائياً بواسطة نظام مقارن المناهج التعليمية*
"""
        
        analysis_markdown_file = "gemini_analysis_result.md"
        with open(analysis_markdown_file, 'w', encoding='utf-8') as f:
            f.write(analysis_markdown)
        print(f"📝 تم حفظ ملف تحليل Markdown في: {analysis_markdown_file}")
        
        # 3. ملخص النتائج
        print("\n🎉 تم إكمال الاختبار بنجاح!")
        print("📋 الملفات المُنشأة:")
        print(f"   - {landing_result_file}")
        print(f"   - {markdown_file}")
        print(f"   - {report_file}")
        print(f"   - {gemini_result_file}")
        print(f"   - {analysis_markdown_file}")
        
        print("\n📊 ملخص النتائج:")
        print(f"   - LandingAI: ✅ استخرج {len(extracted_text)} حرف")
        print(f"   - Gemini: ✅ حلل النص وقدم تقرير مفصل")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        print(f"🔍 التفاصيل: {traceback.format_exc()}")
        return False

async def test_services_health():
    """اختبار صحة الخدمات"""
    print("🏥 فحص صحة الخدمات...")
    
    try:
        # اختبار LandingAI
        landing_ai = LandingAIService()
        print("✅ LandingAI Service: جاهز")
        
        # اختبار Gemini
        gemini = GeminiService()
        print("✅ Gemini Service: جاهز")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في فحص الخدمات: {e}")
        return False

if __name__ == "__main__":
    print("🚀 بدء اختبار سير العمل الكامل...")
    print("=" * 50)
    
    async def main():
        # فحص صحة الخدمات أولاً
        if not await test_services_health():
            print("💥 فشل في فحص صحة الخدمات")
            return
        
        # تشغيل الاختبار الكامل
        success = await test_complete_workflow()
        
        if success:
            print("\n🎉 تم إكمال جميع الاختبارات بنجاح!")
        else:
            print("\n💥 فشل في بعض الاختبارات")
    
    asyncio.run(main()) 