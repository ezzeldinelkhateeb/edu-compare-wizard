#!/usr/bin/env python3
"""
اختبار استخراج النص الحقيقي من الصورة
Real Image Text Extraction Test
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
import base64

# إضافة المسار للاستيراد
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
    print("✅ تم تحميل مكتبات OCR بنجاح")
except ImportError:
    HAS_OCR = False
    print("⚠️ مكتبات OCR غير متوفرة")

from app.services.gemini_service import GeminiService

async def extract_text_with_ocr(image_path: str) -> dict:
    """استخراج النص باستخدام OCR"""
    if not HAS_OCR:
        return {
            "success": False,
            "error": "مكتبات OCR غير متوفرة - pip install pytesseract pillow",
            "text": "",
            "confidence": 0
        }
    
    try:
        # قراءة الصورة
        image = Image.open(image_path)
        
        # استخراج النص باستخدام Tesseract
        # تجربة اللغة العربية أولاً
        try:
            text_ar = pytesseract.image_to_string(image, lang='ara')
            if text_ar.strip():
                confidence = 0.8
                extracted_text = text_ar
                language = "Arabic"
            else:
                raise Exception("لا يوجد نص عربي")
        except:
            # تجربة الإنجليزية كبديل
            try:
                text_en = pytesseract.image_to_string(image, lang='eng')
                extracted_text = text_en
                confidence = 0.7
                language = "English"
            except:
                # تجربة بدون تحديد لغة
                extracted_text = pytesseract.image_to_string(image)
                confidence = 0.6
                language = "Auto"
        
        # تنظيف النص
        cleaned_text = extracted_text.strip()
        
        return {
            "success": True,
            "text": cleaned_text,
            "confidence": confidence,
            "language": language,
            "character_count": len(cleaned_text),
            "word_count": len(cleaned_text.split()),
            "lines": cleaned_text.split('\n')
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "confidence": 0
        }

async def analyze_image_content(image_path: str) -> dict:
    """تحليل محتوى الصورة بصرياً"""
    try:
        image = Image.open(image_path)
        
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
            "size_bytes": os.path.getsize(image_path),
            "aspect_ratio": round(image.width / image.height, 2)
        }
    except Exception as e:
        return {"error": str(e)}

async def test_real_image_extraction():
    """اختبار استخراج النص الحقيقي من الصورة"""
    
    # مسار الصورة
    image_path = Path("../103.jpg")
    if not image_path.exists():
        print(f"❌ الصورة غير موجودة: {image_path.absolute()}")
        return False
    
    print(f"🖼️ بدء تحليل الصورة الحقيقية: {image_path.absolute()}")
    
    try:
        # 1. تحليل خصائص الصورة
        print("\n📊 تحليل خصائص الصورة...")
        image_info = await analyze_image_content(image_path)
        print(f"📐 الأبعاد: {image_info.get('width')}x{image_info.get('height')}")
        print(f"📦 الحجم: {image_info.get('size_bytes', 0) / 1024 / 1024:.2f} MB")
        print(f"🎨 الصيغة: {image_info.get('format')}")
        print(f"📏 نسبة العرض للارتفاع: {image_info.get('aspect_ratio')}")
        
        # 2. استخراج النص باستخدام OCR
        print("\n🔍 استخراج النص باستخدام OCR...")
        start_time = datetime.now()
        
        ocr_result = await extract_text_with_ocr(str(image_path.absolute()))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if not ocr_result["success"]:
            print(f"❌ فشل في استخراج النص: {ocr_result['error']}")
            return False
        
        extracted_text = ocr_result["text"]
        print(f"✅ تم استخراج النص بنجاح!")
        print(f"📄 عدد الأحرف: {ocr_result['character_count']}")
        print(f"📝 عدد الكلمات: {ocr_result['word_count']}")
        print(f"🌍 اللغة المكتشفة: {ocr_result['language']}")
        print(f"🎯 مستوى الثقة: {ocr_result['confidence']:.2f}")
        print(f"⏱️ وقت المعالجة: {processing_time:.2f} ثانية")
        
        # عرض النص المستخرج
        print(f"\n📖 النص المستخرج:")
        print("=" * 50)
        print(extracted_text)
        print("=" * 50)
        
        # حفظ النتيجة الأولية
        ocr_result_file = "real_ocr_result.json"
        full_result = {
            "image_info": image_info,
            "ocr_result": ocr_result,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "source_file": "103.jpg"
        }
        
        with open(ocr_result_file, 'w', encoding='utf-8') as f:
            json.dump(full_result, f, ensure_ascii=False, indent=2)
        print(f"💾 تم حفظ نتيجة OCR في: {ocr_result_file}")
        
        # إنشاء ملف Markdown للنص المستخرج
        markdown_content = f"""# النص المستخرج من الصورة الحقيقية

## معلومات الصورة
- **الملف**: 103.jpg
- **الأبعاد**: {image_info.get('width')}x{image_info.get('height')}
- **الحجم**: {image_info.get('size_bytes', 0) / 1024 / 1024:.2f} MB
- **الصيغة**: {image_info.get('format')}

## معلومات الاستخراج
- **طريقة الاستخراج**: Tesseract OCR
- **اللغة المكتشفة**: {ocr_result['language']}
- **مستوى الثقة**: {ocr_result['confidence']:.2f}
- **وقت المعالجة**: {processing_time:.2f} ثانية
- **عدد الأحرف**: {ocr_result['character_count']}
- **عدد الكلمات**: {ocr_result['word_count']}

## النص المستخرج

```
{extracted_text}
```

---
*تم استخراج هذا النص من الصورة الحقيقية في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        markdown_file = "real_extracted_text.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"📝 تم حفظ النص في: {markdown_file}")
        
        # 3. تحليل النص باستخدام Gemini (إذا كان متوفراً)
        if extracted_text.strip():
            print("\n🤖 تحليل النص باستخدام Gemini...")
            try:
                gemini = GeminiService()
                
                analysis_prompt = f"""
                يرجى تحليل النص التالي المستخرج من صورة حقيقية:
                
                النص:
                {extracted_text}
                
                يرجى تقديم:
                1. تحديد نوع المحتوى (كتاب مدرسي، مقال، إعلان، إلخ)
                2. اللغة المستخدمة
                3. الموضوع الرئيسي
                4. النقاط المهمة
                5. تقييم جودة استخراج النص
                6. أي ملاحظات أخرى
                
                يرجى الإجابة باللغة العربية.
                """
                
                gemini_analysis = await gemini.analyze_text(extracted_text, analysis_prompt)
                
                print("✅ تم تحليل النص بنجاح باستخدام Gemini")
                
                # حفظ تحليل Gemini
                gemini_result = {
                    "original_text": extracted_text,
                    "analysis": gemini_analysis,
                    "ocr_info": ocr_result,
                    "image_info": image_info,
                    "timestamp": datetime.now().isoformat()
                }
                
                gemini_file = "real_gemini_analysis.json"
                with open(gemini_file, 'w', encoding='utf-8') as f:
                    json.dump(gemini_result, f, ensure_ascii=False, indent=2)
                print(f"💾 تم حفظ تحليل Gemini في: {gemini_file}")
                
                # تقرير تحليل Gemini
                analysis_report = f"""# تحليل النص الحقيقي - Gemini AI

## معلومات المصدر
- **الملف الأصلي**: 103.jpg (الصورة الحقيقية)
- **طريقة الاستخراج**: Tesseract OCR
- **تاريخ التحليل**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## معلومات الاستخراج
- **اللغة المكتشفة**: {ocr_result['language']}
- **مستوى الثقة**: {ocr_result['confidence']:.2f}
- **عدد الأحرف**: {ocr_result['character_count']}
- **عدد الكلمات**: {ocr_result['word_count']}

## النص الأصلي المستخرج
```
{extracted_text}
```

## تحليل Gemini AI
{gemini_analysis}

---
*تم إنشاء هذا التقرير من الصورة الحقيقية باستخدام OCR حقيقي*
"""
                
                analysis_file = "real_gemini_analysis.md"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    f.write(analysis_report)
                print(f"📋 تم حفظ تقرير التحليل في: {analysis_file}")
                
            except Exception as e:
                print(f"⚠️ خطأ في تحليل Gemini: {e}")
        
        # 4. ملخص النتائج
        print(f"\n🎉 تم إكمال تحليل الصورة الحقيقية بنجاح!")
        print("📋 الملفات المُنشأة:")
        print(f"   - {ocr_result_file}")
        print(f"   - {markdown_file}")
        if 'gemini_file' in locals():
            print(f"   - {gemini_file}")
            print(f"   - {analysis_file}")
        
        print(f"\n📊 ملخص النتائج:")
        print(f"   - OCR: ✅ استخرج {ocr_result['character_count']} حرف")
        print(f"   - اللغة: {ocr_result['language']}")
        print(f"   - الثقة: {ocr_result['confidence']:.2f}")
        if 'gemini_analysis' in locals():
            print(f"   - Gemini: ✅ حلل النص وقدم تقرير مفصل")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        print(f"🔍 التفاصيل: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 بدء اختبار استخراج النص الحقيقي من الصورة...")
    print("=" * 60)
    
    if not HAS_OCR:
        print("❌ مكتبات OCR غير متوفرة!")
        print("لتثبيت المكتبات المطلوبة:")
        print("pip install pytesseract pillow")
        print("وتحميل Tesseract من: https://github.com/UB-Mannheim/tesseract/wiki")
    else:
        asyncio.run(test_real_image_extraction()) 