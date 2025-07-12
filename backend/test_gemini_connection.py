#!/usr/bin/env python3
"""
اختبار اتصال Gemini
Test Gemini Connection
"""

import os
import sys
import asyncio

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.gemini_service import GeminiService
from app.core.config import get_settings

async def test_gemini():
    """اختبار اتصال Gemini مع تحليل النص"""
    print("🧪 بدء اختبار اتصال Gemini...")
    
    # نص تجريبي للاختبار
    test_old_text = """
    الوحدة الأولى: مقدمة في الرياضيات
    الدرس الأول: الأعداد الطبيعية
    الأهداف:
    - تعريف الأعداد الطبيعية
    - العمليات الحسابية الأساسية
    - حل المسائل الكلامية
    
    التمارين:
    1. اكتب الأعداد من 1 إلى 10
    2. احسب مجموع العددين 5 + 3
    3. حل المسألة: في الفصل 20 طالب، كم طالباً إذا غاب 3 طلاب؟
    """
    
    test_new_text = """
    الوحدة الأولى: أساسيات الرياضيات
    الدرس الأول: الأعداد الطبيعية والصحيحة
    الأهداف التعليمية:
    - فهم مفهوم الأعداد الطبيعية والصحيحة
    - إتقان العمليات الحسابية الأساسية الأربع
    - تطبيق المهارات في حل المسائل الحياتية
    - استخدام التكنولوجيا في الحسابات
    
    الأنشطة والتمارين:
    1. اكتب الأعداد من 1 إلى 20 واستخدم الآلة الحاسبة
    2. احسب مجموع وفرق العددين 5 + 3 و 8 - 2
    3. حل المسألة: في الفصل 25 طالب، إذا غاب 4 طلاب وانضم 2 طلاب جدد، كم العدد النهائي؟
    4. مشروع جماعي: حساب المصروفات اليومية
    """
    
    try:
        # إنشاء خدمة Gemini
        settings = get_settings()
        gemini_service = GeminiService()
        
        print("🔍 تحقق من API Key...")
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            print("✅ API Key موجود")
        else:
            print("⚠️ API Key غير موجود - سيتم استخدام المحاكاة")
        
        print("🚀 بدء تحليل النصوص...")
        print(f"📝 النص القديم: {len(test_old_text)} حرف")
        print(f"📝 النص الجديد: {len(test_new_text)} حرف")
        
        # تحليل المقارنة
        result = await gemini_service.compare_texts(test_old_text, test_new_text)
        
        print("\n📊 نتائج التحليل:")
        print(f"   🎯 نسبة التشابه: {result.similarity_percentage:.1f}%")
        print(f"   ⏱️ وقت المعالجة: {result.processing_time:.2f}s")
        print(f"   🎯 نقاط الثقة: {result.confidence_score:.2%}")
        
        # التغييرات في المحتوى
        content_changes = result.content_changes
        print(f"\n📝 التغييرات في المحتوى ({len(content_changes)} تغيير):")
        for i, change in enumerate(content_changes[:3], 1):
            print(f"   {i}. {change}")
        
        # التغييرات في الأسئلة
        question_changes = result.questions_changes
        print(f"\n❓ التغييرات في الأسئلة ({len(question_changes)} تغيير):")
        for i, change in enumerate(question_changes[:3], 1):
            print(f"   {i}. {change}")
        
        # الاختلافات الرئيسية
        major_diffs = result.major_differences
        print(f"\n🔍 الاختلافات الرئيسية ({len(major_diffs)} اختلاف):")
        for i, diff in enumerate(major_diffs[:3], 1):
            print(f"   {i}. {diff}")
        
        # المحتوى المضاف
        added_content = result.added_content
        print(f"\n➕ المحتوى المضاف ({len(added_content)} إضافة):")
        for i, addition in enumerate(added_content[:3], 1):
            print(f"   {i}. {addition}")
        
        # المحتوى المحذوف
        removed_content = result.removed_content
        print(f"\n➖ المحتوى المحذوف ({len(removed_content)} حذف):")
        for i, removal in enumerate(removed_content[:3], 1):
            print(f"   {i}. {removal}")
        
        # الملخص والتوصية
        print(f"\n📋 الملخص: {result.summary}")
        print(f"💡 التوصية: {result.recommendation}")
        
        # إحصائيات النص
        print(f"\n📊 إحصائيات النص:")
        print(f"   📏 طول النص القديم: {result.old_text_length} حرف")
        print(f"   📏 طول النص الجديد: {result.new_text_length} حرف")
        print(f"   🔗 الكلمات المشتركة: {result.common_words_count}")
        print(f"   🆕 كلمات جديدة فقط: {result.unique_new_words}")
        print(f"   🗑️ كلمات محذوفة: {result.unique_old_words}")
        
        # اختبار تحليل متقدم إذا كان متوفراً
        print("\n🔬 اختبار التحليل المتقدم...")
        try:
            advanced_result = await gemini_service.analyze_text(test_new_text)
            print("✅ التحليل المتقدم نجح")
            print(f"   📊 طول التحليل: {len(advanced_result)} حرف")
        except Exception as e:
            print(f"⚠️ التحليل المتقدم غير متوفر: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار Gemini: {e}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 اختبار اتصال Gemini")
    print("=" * 50)
    
    success = asyncio.run(test_gemini())
    
    print("\n" + "=" * 50)
    if success:
        print("✅ اختبار Gemini مكتمل بنجاح!")
    else:
        print("❌ فشل اختبار Gemini!")
    print("=" * 50) 