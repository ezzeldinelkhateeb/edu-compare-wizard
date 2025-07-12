"""
اختبار النظام المحسن لخدمة Gemini وحساب التشابه
Test the improved Gemini service and similarity calculation
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Set environment variable
os.environ['GEMINI_API_KEY'] = 'AIzaSyCDO-0puQQN79BJ4u503O31g16ww8CAycg'

from app.services.gemini_service import GeminiService


async def test_gemini_improvements():
    """اختبار التحسينات على خدمة Gemini"""
    
    print("🔧 اختبار النظام المحسن لخدمة Gemini\n")
    
    # إنشاء الخدمة
    service = GeminiService()
    
    # فحص الحالة
    print("1️⃣ فحص حالة Gemini:")
    health = await service.health_check()
    print(f"   الحالة: {health['status']}")
    print(f"   الوضع: {health.get('mode', 'unknown')}")
    print(f"   مفتاح API: {'موجود' if health.get('api_key_configured', False) else 'غير موجود'}")
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
    print()
    
    # اختبار نصوص مختلفة
    print("4️⃣ اختبار النصوص المختلفة:")
    different_text = """قوانين نيوتن للحركة
القانون الأول: الجسم الساكن يبقى ساكناً والجسم المتحرك يبقى متحركاً ما لم تؤثر عليه قوة خارجية."""
    
    result3 = await service.compare_texts(text_old, different_text)
    print(f"   نصان مختلفان:")
    print(f"   نسبة التشابه: {result3.similarity_percentage}%")
    print(f"   الملخص: {result3.summary}")
    print(f"   التوصية: {result3.recommendation}")
    print()
    
    # اختبار النص من التقرير الفعلي
    print("5️⃣ اختبار النص الفعلي من التقرير:")
    old_from_report = """قام العالم الفرنسى باسكال بصياغة هذه النتيجة كما يلى :
قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء.
ملاحظة
* تخضع السوائل لقاعدة باسكال بينما لا تخضع الغازات لها."""
    
    new_from_report = """* قام العالم الفرنسي باسكال بصياغة هذه النتيجة كما يلي :
قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء.
ملاحظة
تخضع السوائل لقاعدة باسكال بينما لا تخضع الغازات لها،"""
    
    result4 = await service.compare_texts(old_from_report, new_from_report)
    print(f"   النص الفعلي من التقرير:")
    print(f"   نسبة التشابه: {result4.similarity_percentage}%")
    print(f"   الملخص: {result4.summary}")
    print(f"   التوصية: {result4.recommendation}")
    print()
    
    print("✅ اكتمل الاختبار!")
    print(f"📊 ملخص النتائج:")
    print(f"   - النصوص المتطابقة: {result1.similarity_percentage}%")
    print(f"   - النصوص المتشابهة: {result2.similarity_percentage}%") 
    print(f"   - النصوص المختلفة: {result3.similarity_percentage}%")
    print(f"   - النص الفعلي: {result4.similarity_percentage}%")


if __name__ == "__main__":
    asyncio.run(test_gemini_improvements()) 