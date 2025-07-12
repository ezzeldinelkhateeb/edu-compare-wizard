# اختبار استخراج النص من الصور باستخدام Gemini 2.0

## نظرة عامة

هذا الكود يقوم باختبار استخراج النص من الصور باستخدام Google Gemini 2.0 Flash Exp. الكود مصمم لاستخراج النص من الصورتين المحددتين:
- `103.jpg`
- `Scan_0037.jpg`

## المتطلبات

### 1. تثبيت المكتبات المطلوبة

```bash
pip install google-generativeai pillow
```

### 2. إعداد مفتاح API لـ Gemini

قم بتعيين متغير البيئة `GEMINI_API_KEY`:

#### في Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

#### في Windows (Command Prompt):
```cmd
set GEMINI_API_KEY=your-api-key-here
```

#### في Linux/Mac:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. الحصول على مفتاح API

1. اذهب إلى [Google AI Studio](https://makersuite.google.com/app/apikey)
2. قم بإنشاء حساب أو تسجيل الدخول
3. انقر على "Create API Key"
4. انسخ المفتاح واستخدمه في المتغير البيئي

## كيفية التشغيل

### 1. تشغيل الاختبار

```bash
python test_gemini_text_extraction.py
```

### 2. ما يحدث عند التشغيل

1. **فحص المكتبات**: يتأكد من وجود المكتبات المطلوبة
2. **فحص مفتاح API**: يتأكد من وجود مفتاح Gemini API
3. **معالجة الصور**: يقوم بمعالجة كل صورة على حدة
4. **استخراج النص**: يرسل الصورة إلى Gemini 2.0 ويستخرج النص
5. **حفظ النتائج**: يحفظ النتائج في ملفات JSON و Markdown

## المخرجات

### 1. ملفات النتائج

سيتم إنشاء مجلد `gemini_extraction_results` يحتوي على:

- `gemini_extraction_YYYYMMDD_HHMMSS.json`: ملف JSON يحتوي على جميع النتائج
- `103.jpg_extracted_YYYYMMDD_HHMMSS.md`: ملف Markdown للنص المستخرج من الصورة الأولى
- `Scan_0037.jpg_extracted_YYYYMMDD_HHMMSS.md`: ملف Markdown للنص المستخرج من الصورة الثانية

### 2. معلومات النتيجة

كل نتيجة تحتوي على:

```json
{
  "success": true,
  "text": "النص المستخرج من الصورة",
  "confidence": 0.85,
  "character_count": 500,
  "word_count": 100,
  "processing_time": 2.5,
  "image_info": {
    "width": 1920,
    "height": 1080,
    "format": "JPEG",
    "mode": "RGB",
    "size_bytes": 1024000
  },
  "service": "Gemini_2.0_Flash_Exp",
  "model": "gemini-2.0-flash-exp"
}
```

## ميزات الكود

### 1. معالجة متقدمة للصور
- دعم للصور عالية الدقة
- تحليل معلومات الصورة (الأبعاد، الحجم، الصيغة)
- تقدير مستوى الثقة بناءً على جودة النص والصورة

### 2. دعم متعدد اللغات
- دعم كامل للغة العربية
- دعم للغة الإنجليزية
- الحفاظ على الأرقام والرموز الرياضية

### 3. معالجة الأخطاء
- فحص وجود الصور
- معالجة أخطاء API
- رسائل خطأ واضحة ومفيدة

### 4. حفظ النتائج
- حفظ بتنسيق JSON للتحليل البرمجي
- حفظ بتنسيق Markdown للقراءة البشرية
- تنظيم النتائج حسب التاريخ والوقت

## مثال على الاستخدام

```python
from test_gemini_text_extraction import GeminiTextExtractor
import asyncio

async def main():
    extractor = GeminiTextExtractor()
    result = await extractor.extract_text_from_image("path/to/image.jpg")
    
    if result["success"]:
        print(f"النص المستخرج: {result['text']}")
        print(f"مستوى الثقة: {result['confidence']}")
    else:
        print(f"خطأ: {result['error']}")

asyncio.run(main())
```

## استكشاف الأخطاء

### 1. خطأ "مكتبات Gemini غير متوفرة"
```bash
pip install google-generativeai pillow
```

### 2. خطأ "GEMINI_API_KEY غير موجود"
تأكد من تعيين متغير البيئة بشكل صحيح

### 3. خطأ "الصورة غير موجودة"
تأكد من وجود الصور في المسارات المحددة

### 4. خطأ في API
- تحقق من صحة مفتاح API
- تحقق من اتصال الإنترنت
- تحقق من حدود الاستخدام في Google AI Studio

## ملاحظات مهمة

1. **تكلفة API**: استخدام Gemini API يتطلب رصيد في Google AI Studio
2. **حدود الاستخدام**: هناك حدود على عدد الطلبات في الدقيقة والساعة
3. **جودة النص**: جودة النص المستخرج تعتمد على جودة الصورة الأصلية
4. **الخصوصية**: الصور تُرسل إلى خوادم Google للمعالجة

## الدعم

إذا واجهت أي مشاكل، تأكد من:
1. تثبيت جميع المكتبات المطلوبة
2. تعيين مفتاح API بشكل صحيح
3. وجود الصور في المسارات المحددة
4. اتصال الإنترنت المستقر 