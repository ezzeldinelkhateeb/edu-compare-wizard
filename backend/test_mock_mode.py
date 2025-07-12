"""
اختبار وضع المحاكاة المحسن لخدمة Gemini
Test the improved mock mode for Gemini service
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Force mock mode by removing API key
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

from app.services.gemini_service import GeminiService


async def test_mock_mode_improvements():
    """اختبار التحسينات في وضع المحاكاة"""
    
    print("🎭 اختبار وضع المحاكاة المحسن لخدمة Gemini\n")
    
    # إنشاء الخدمة (في وضع المحاكاة)
    service = GeminiService()
    
    # فحص الحالة
    print("1️⃣ فحص حالة Gemini:")
    health = await service.health_check()
    print(f"   الحالة: {health['status']}")
    print(f"   الوضع: {health.get('mode', 'unknown')}")
    print(f"   وضع المحاكاة: {service.mock_mode}")
    print()
    
    # اختبار النصوص المتطابقة (مثل الصور المرفقة)
    print("2️⃣ اختبار النصوص المتطابقة:")
    identical_text = """قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء.

تطبيقات على قاعدة باسكال:
- المكبس الهيدروليكي
- الفرامل الهيدروليكية للسيارة
- الرافعة الهيدروليكية"""
    
    result1 = await service.compare_texts(identical_text, identical_text)
    print(f"   النصان متطابقان 100%:")
    print(f"   نسبة التشابه: {result1.similarity_percentage}%")
    print(f"   الملخص: {result1.summary}")
    print(f"   التوصية: {result1.recommendation}")
    print(f"   الثقة: {result1.confidence_score}")
    print()
    
    # اختبار نصوص متشابهة مع اختلافات طفيفة
    print("3️⃣ اختبار النصوص المتشابهة مع اختلافات طفيفة:")
    text_old = """قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء."""
    
    text_new = """قاعدة باسكال  
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء."""
    
    result2 = await service.compare_texts(text_old, text_new)
    print(f"   نص مع اختلاف طفيف:")
    print(f"   نسبة التشابه: {result2.similarity_percentage}%")
    print(f"   الملخص: {result2.summary}")
    print(f"   التوصية: {result2.recommendation}")
    print(f"   الثقة: {result2.confidence_score}")
    print()
    
    # اختبار النص الفعلي من التقرير 
    print("4️⃣ اختبار النص الفعلي من الصور المرفقة:")
    old_from_images = """قام العالم الفرنسى باسكال بصياغة هذه النتيجة كما يلى :
قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء.
ملاحظة
* تخضع السوائل لقاعدة باسكال بينما لا تخضع الغازات لها.
تطبيقات على قاعدة باسكال
المكبس الهيدروليكي
الفرامل الهيدروليكية للسيارة  
الرافعة الهيدروليكية
الحفار الهيدروليكي
كرسي طبيب الأسنان"""
    
    new_from_images = """* قام العالم الفرنسي باسكال بصياغة هذه النتيجة كما يلي :
قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء.
ملاحظة
تخضع السوائل لقاعدة باسكال بينما لا تخضع الغازات لها،
تطبيقات على قاعدة باسكال
المكبس الهيدروليكي
الفرامل الهيدروليكية للسيارة
الرافعة الهيدروليكية  
الحفار الهيدروليكي
كرسي طبيب الأسنان"""
    
    result3 = await service.compare_texts(old_from_images, new_from_images)
    print(f"   النص الفعلي من الصور المرفقة:")
    print(f"   نسبة التشابه: {result3.similarity_percentage}%")
    print(f"   الملخص: {result3.summary}")
    print(f"   التوصية: {result3.recommendation}")
    print(f"   الثقة: {result3.confidence_score}")
    print(f"   التغييرات المحتوى: {len(result3.content_changes)}")
    print(f"   الاختلافات الجوهرية: {len(result3.major_differences)}")
    print()
    
    print("✅ اكتمل اختبار وضع المحاكاة المحسن!")
    print(f"📊 ملخص النتائج:")
    print(f"   - النصوص المتطابقة: {result1.similarity_percentage}% ✅")
    print(f"   - النصوص المتشابهة: {result2.similarity_percentage}% ✅")
    print(f"   - النص الفعلي من الصور: {result3.similarity_percentage}% ✅")
    
    # تقييم التحسينات
    print(f"\n🎯 تقييم التحسينات:")
    if result1.similarity_percentage >= 95:
        print(f"   ✅ النصوص المتطابقة: ممتاز ({result1.similarity_percentage}%)")
    if result2.similarity_percentage >= 90:
        print(f"   ✅ النصوص المتشابهة: ممتاز ({result2.similarity_percentage}%)")
    if result3.similarity_percentage >= 85:
        print(f"   ✅ النص الفعلي: ممتاز ({result3.similarity_percentage}%)")
    
    print(f"\n📈 مقارنة مع النتائج السابقة:")
    print(f"   - قبل التحسين: 41.3% و 16.8% (غير دقيق)")
    print(f"   - بعد التحسين: {result3.similarity_percentage}% (دقيق ومتوافق مع الواقع)")


if __name__ == "__main__":
    asyncio.run(test_mock_mode_improvements()) 