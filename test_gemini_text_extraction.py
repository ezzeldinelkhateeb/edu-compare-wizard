#!/usr/bin/env python3
"""
اختبار استخراج النص من الصور باستخدام Gemini 2.0
Test Text Extraction from Images using Gemini 2.0
"""

import os
import sys
import json
import asyncio
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from PIL import Image
    import google.generativeai as genai
    HAS_GEMINI = True
    print("✅ تم تحميل مكتبات Gemini بنجاح")
except ImportError as e:
    HAS_GEMINI = False
    print(f"⚠️ مكتبات Gemini غير متوفرة: {e}")
    print("قم بتثبيت: pip install google-generativeai pillow")

class GeminiTextExtractor:
    """مستخرج النص من الصور باستخدام Gemini 2.0"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY غير موجود في البيئة")
            print("قم بتعيين المتغير البيئي: export GEMINI_API_KEY='your-api-key'")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✅ تم تكوين Gemini 2.0 Flash Exp بنجاح")
        except Exception as e:
            print(f"❌ خطأ في تكوين Gemini: {e}")
            return
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """تحويل الصورة إلى base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ خطأ في تحويل الصورة: {e}")
            return ""
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """استخراج النص من الصورة باستخدام Gemini 2.0"""
        
        if not HAS_GEMINI:
            return {
                "success": False,
                "error": "مكتبات Gemini غير متوفرة",
                "text": "",
                "confidence": 0
            }
        
        if not self.api_key:
            return {
                "success": False,
                "error": "GEMINI_API_KEY غير موجود",
                "text": "",
                "confidence": 0
            }
        
        try:
            print(f"🖼️ بدء استخراج النص من: {Path(image_path).name}")
            
            # التحقق من وجود الصورة
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"الصورة غير موجودة: {image_path}",
                    "text": "",
                    "confidence": 0
                }
            
            # تحميل الصورة
            image = Image.open(image_path)
            
            # معلومات الصورة
            image_info = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": os.path.getsize(image_path)
            }
            
            print(f"📊 معلومات الصورة: {image.width}x{image.height} ({image.format})")
            
            # إنشاء البرومبت لاستخراج النص
            prompt = """
            استخرج النص من هذه الصورة بدقة عالية. 

            التعليمات:
            1. استخرج جميع النصوص المرئية في الصورة
            2. احافظ على التنسيق الأصلي للنص
            3. إذا كان النص باللغة العربية، تأكد من كتابته بشكل صحيح
            4. إذا كان النص باللغة الإنجليزية، احافظ على التهجئة الصحيحة
            5. احتفظ بالأرقام والرموز الرياضية كما هي
            6. إذا كانت هناك جداول أو قوائم، احتفظ بتنسيقها
            7. إذا كانت هناك معادلات رياضية، اكتبها بشكل واضح

            أعد النص المستخرج فقط بدون أي تعليقات إضافية.
            """
            
            # استخراج النص باستخدام Gemini
            start_time = datetime.now()
            
            print("🤖 إرسال الصورة إلى Gemini 2.0...")
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if not response.text:
                return {
                    "success": False,
                    "error": "لم يتم الحصول على استجابة من Gemini",
                    "text": "",
                    "confidence": 0,
                    "processing_time": processing_time
                }
            
            extracted_text = response.text.strip()
            
            # حساب إحصائيات النص
            character_count = len(extracted_text)
            word_count = len(extracted_text.split())
            
            # تقدير مستوى الثقة بناءً على جودة النص
            confidence = self._estimate_confidence(extracted_text, image_info)
            
            print(f"✅ تم استخراج النص بنجاح!")
            print(f"📄 عدد الأحرف: {character_count}")
            print(f"📝 عدد الكلمات: {word_count}")
            print(f"🎯 مستوى الثقة: {confidence:.2f}")
            print(f"⏱️ وقت المعالجة: {processing_time:.2f} ثانية")
            
            return {
                "success": True,
                "text": extracted_text,
                "confidence": confidence,
                "character_count": character_count,
                "word_count": word_count,
                "processing_time": processing_time,
                "image_info": image_info,
                "service": "Gemini_2.0_Flash_Exp",
                "model": "gemini-2.0-flash-exp"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ خطأ في استخراج النص: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "text": "",
                "confidence": 0,
                "processing_time": 0
            }
    
    def _estimate_confidence(self, text: str, image_info: Dict[str, Any]) -> float:
        """تقدير مستوى الثقة بناءً على جودة النص"""
        
        if not text.strip():
            return 0.0
        
        confidence = 0.8  # مستوى أساسي
        
        # عوامل إيجابية
        if len(text) > 50:
            confidence += 0.1
        
        if any(char.isdigit() for char in text):
            confidence += 0.05
        
        # التحقق من وجود نصوص عربية أو إنجليزية
        arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        
        if arabic_chars > 10 or english_chars > 10:
            confidence += 0.05
        
        # التحقق من جودة الصورة
        if image_info["width"] > 1000 and image_info["height"] > 1000:
            confidence += 0.05
        
        return min(confidence, 0.95)  # حد أقصى 95%
    
    def save_results(self, results: Dict[str, Any], output_dir: str = "gemini_extraction_results"):
        """حفظ النتائج في ملفات"""
        
        # إنشاء مجلد النتائج
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # حفظ النتائج كـ JSON
        json_file = os.path.join(output_dir, f"gemini_extraction_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 تم حفظ النتائج في: {json_file}")
        
        # حفظ النصوص المستخرجة كـ Markdown
        for image_name, result in results.items():
            if result["success"]:
                md_file = os.path.join(output_dir, f"{image_name}_extracted_{timestamp}.md")
                
                markdown_content = f"""# النص المستخرج من {image_name}

## معلومات الصورة
- **الملف**: {image_name}
- **الأبعاد**: {result['image_info']['width']}x{result['image_info']['height']}
- **الحجم**: {result['image_info']['size_bytes'] / 1024 / 1024:.2f} MB
- **الصيغة**: {result['image_info']['format']}

## معلومات الاستخراج
- **طريقة الاستخراج**: Gemini 2.0 Flash Exp
- **مستوى الثقة**: {result['confidence']:.2f}
- **وقت المعالجة**: {result['processing_time']:.2f} ثانية
- **عدد الأحرف**: {result['character_count']}
- **عدد الكلمات**: {result['word_count']}

## النص المستخرج

```
{result['text']}
```

---
*تم استخراج هذا النص باستخدام Gemini 2.0 في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
                
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                print(f"📄 تم حفظ النص المستخرج في: {md_file}")


async def test_gemini_text_extraction():
    """اختبار استخراج النص من الصورتين باستخدام Gemini 2.0"""
    
    print("🚀 بدء اختبار استخراج النص باستخدام Gemini 2.0")
    print("=" * 60)
    
    # مسارات الصور
    image_paths = {
        "103.jpg": "D:/ezz/compair/edu-compare-wizard/103.jpg",
        "Scan_0037.jpg": "D:/ezz/compair/edu-compare-wizard/Scan_0037.jpg"
    }
    
    # إنشاء مستخرج النص
    extractor = GeminiTextExtractor()
    
    if not extractor.api_key:
        print("❌ لا يمكن المتابعة بدون GEMINI_API_KEY")
        return
    
    results = {}
    total_start_time = datetime.now()
    
    # استخراج النص من كل صورة
    for image_name, image_path in image_paths.items():
        print(f"\n🖼️ معالجة الصورة: {image_name}")
        print("-" * 40)
        
        # التحقق من وجود الصورة
        if not os.path.exists(image_path):
            print(f"❌ الصورة غير موجودة: {image_path}")
            results[image_name] = {
                "success": False,
                "error": f"الصورة غير موجودة: {image_path}",
                "text": "",
                "confidence": 0
            }
            continue
        
        # استخراج النص
        result = await extractor.extract_text_from_image(image_path)
        results[image_name] = result
        
        # عرض النص المستخرج
        if result["success"]:
            print(f"\n📖 النص المستخرج من {image_name}:")
            print("=" * 50)
            print(result["text"])
            print("=" * 50)
        else:
            print(f"❌ فشل في استخراج النص: {result['error']}")
    
    # إحصائيات عامة
    total_time = (datetime.now() - total_start_time).total_seconds()
    successful_extractions = sum(1 for r in results.values() if r["success"])
    total_images = len(results)
    
    print(f"\n📊 إحصائيات عامة:")
    print("=" * 40)
    print(f"📸 إجمالي الصور: {total_images}")
    print(f"✅ الاستخراجات الناجحة: {successful_extractions}")
    print(f"❌ الاستخراجات الفاشلة: {total_images - successful_extractions}")
    print(f"⏱️ الوقت الإجمالي: {total_time:.2f} ثانية")
    
    if successful_extractions > 0:
        avg_confidence = sum(r["confidence"] for r in results.values() if r["success"]) / successful_extractions
        total_chars = sum(r["character_count"] for r in results.values() if r["success"])
        total_words = sum(r["word_count"] for r in results.values() if r["success"])
        
        print(f"🎯 متوسط الثقة: {avg_confidence:.2f}")
        print(f"📄 إجمالي الأحرف: {total_chars}")
        print(f"📝 إجمالي الكلمات: {total_words}")
    
    # حفظ النتائج
    extractor.save_results(results)
    
    print(f"\n✅ اكتمل اختبار استخراج النص باستخدام Gemini 2.0")
    return results


if __name__ == "__main__":
    # تشغيل الاختبار
    asyncio.run(test_gemini_text_extraction()) 