#!/usr/bin/env python3
"""
اختبار مفتاح Gemini API الجديد
Test the new Gemini API key
"""

import os
import sys
import asyncio
from pathlib import Path

# إضافة مجلد app إلى path
sys.path.append(str(Path(__file__).parent / "app"))

# تعيين مفتاح API الجديد
os.environ["GEMINI_API_KEY"] = "AIzaSyB-2F7RdbLi3BMUb2ixF07cGS0OFnq910U"

from app.services.gemini_service import GeminiService


async def test_gemini_api():
    """اختبار اتصال Gemini API"""
    print("🚀 اختبار مفتاح Gemini API الجديد...")
    print(f"🔑 المفتاح: {os.environ.get('GEMINI_API_KEY', 'غير موجود')}")
    
    try:
        # إنشاء خدمة Gemini
        gemini_service = GeminiService()
        print(f"✅ تم إنشاء خدمة Gemini: {gemini_service.service_type}")
        
        # اختبار بسيط
        old_text = "النص القديم: هذا نص تجريبي للاختبار"
        new_text = "النص الجديد: هذا نص تجريبي محدث للاختبار"
        
        print("🔄 جاري اختبار المقارنة...")
        result = await gemini_service.compare_texts(old_text, new_text)
        
        if result:
            print("✅ نجح الاختبار!")
            print(f"📊 نسبة التشابه: {result.get('similarity_percentage', 'غير محدد')}%")
            print(f"📝 الملخص: {result.get('summary', 'غير متوفر')}")
            print(f"🤖 الخدمة المستخدمة: {result.get('service_used', 'غير محدد')}")
            return True
        else:
            print("❌ فشل في الحصول على نتائج")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {str(e)}")
        return False


async def test_quota_check():
    """اختبار حالة الحصة"""
    print("\n🔍 اختبار حالة حصة API...")
    
    try:
        gemini_service = GeminiService()
        
        # اختبار بسيط جداً لمعرفة حالة الحصة
        simple_old = "مرحبا"
        simple_new = "أهلا"
        
        result = await gemini_service.compare_texts(simple_old, simple_new)
        
        if result:
            print("✅ الحصة متوفرة - API يعمل بشكل طبيعي")
            return True
        else:
            print("⚠️ قد تكون الحصة منتهية أو هناك مشكلة أخرى")
            return False
            
    except Exception as e:
        error_str = str(e).lower()
        if "quota" in error_str or "429" in error_str:
            print("❌ انتهت حصة API - تجاوزت الحد المسموح")
            return False
        elif "401" in error_str or "403" in error_str:
            print("❌ مفتاح API غير صحيح أو غير مصرح")
            return False
        else:
            print(f"❌ خطأ آخر: {str(e)}")
            return False


async def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🧪 اختبار مفتاح Gemini API الجديد")
    print("=" * 60)
    
    # اختبار الحصة أولاً
    quota_ok = await test_quota_check()
    
    if quota_ok:
        # اختبار شامل
        test_ok = await test_gemini_api()
        if test_ok:
            print("\n🎉 المفتاح يعمل بشكل ممتاز!")
        else:
            print("\n❌ هناك مشكلة في المفتاح")
    else:
        print("\n⚠️ مشكلة في الحصة أو المفتاح")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main()) 