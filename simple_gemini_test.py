#!/usr/bin/env python3
"""
اختبار سريع لاستخراج النص من الصور باستخدام Gemini 2.0
Quick Test for Text Extraction from Images using Gemini 2.0
"""

import os
import asyncio
from pathlib import Path

try:
    from PIL import Image
    import google.generativeai as genai
    print("✅ تم تحميل مكتبات Gemini بنجاح")
except ImportError as e:
    print(f"❌ مكتبات Gemini غير متوفرة: {e}")
    print("قم بتثبيت: pip install google-generativeai pillow")
    exit(1)

async def extract_text_with_gemini(image_path: str, api_key: str) -> dict:
    """استخراج النص من الصورة باستخدام Gemini 2.0"""
    
    try:
        # تكوين Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print(f"🖼️ معالجة الصورة: {Path(image_path).name}")
        
        # تحميل الصورة
        image = Image.open(image_path)
        
        # إنشاء البرومبت
        prompt = """
        استخرج النص من هذه الصورة بدقة عالية.
        
        التعليمات:
        1. استخرج جميع النصوص المرئية في الصورة
        2. احافظ على التنسيق الأصلي للنص
        3. إذا كان النص باللغة العربية، تأكد من كتابته بشكل صحيح
        4. احتفظ بالأرقام والرموز الرياضية كما هي
        
        أعد النص المستخرج فقط بدون أي تعليقات إضافية.
        """
        
        # استخراج النص
        print("🤖 إرسال الصورة إلى Gemini 2.0...")
        response = await asyncio.to_thread(model.generate_content, [prompt, image])
        
        if not response.text:
            return {"success": False, "error": "لم يتم الحصول على استجابة من Gemini"}
        
        extracted_text = response.text.strip()
        
        return {
            "success": True,
            "text": extracted_text,
            "character_count": len(extracted_text),
            "word_count": len(extracted_text.split())
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

async def main():
    """الدالة الرئيسية"""
    
    print("🚀 اختبار سريع لاستخراج النص باستخدام Gemini 2.0")
    print("=" * 50)
    
    # الحصول على مفتاح API
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY غير موجود")
        print("قم بتعيين المتغير البيئي: export GEMINI_API_KEY='your-api-key'")
        return
    
    # مسارات الصور
    image_paths = {
        "103.jpg": "D:/ezz/compair/edu-compare-wizard/103.jpg",
        "Scan_0037.jpg": "D:/ezz/compair/edu-compare-wizard/Scan_0037.jpg"
    }
    
    # معالجة كل صورة
    for image_name, image_path in image_paths.items():
        print(f"\n📸 معالجة: {image_name}")
        print("-" * 30)
        
        if not os.path.exists(image_path):
            print(f"❌ الصورة غير موجودة: {image_path}")
            continue
        
        # استخراج النص
        result = await extract_text_with_gemini(image_path, api_key)
        
        if result["success"]:
            print(f"✅ تم استخراج النص بنجاح!")
            print(f"📄 عدد الأحرف: {result['character_count']}")
            print(f"📝 عدد الكلمات: {result['word_count']}")
            print(f"\n📖 النص المستخرج:")
            print("=" * 40)
            print(result["text"])
            print("=" * 40)
        else:
            print(f"❌ فشل في استخراج النص: {result['error']}")
    
    print(f"\n✅ اكتمل الاختبار")

if __name__ == "__main__":
    asyncio.run(main()) 