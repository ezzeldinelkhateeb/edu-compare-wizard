#!/usr/bin/env python3
"""
اختبار النظام السريع للمقارنة المتوازية
Ultra Fast Parallel Comparison System Test
"""

import asyncio
import time
import os
import sys
from datetime import datetime
from loguru import logger

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from celery_app.optimized_tasks import (
    quick_dual_comparison,
    parallel_extract_text_batch
)
from app.services.landing_ai_service import LandingAIService
from app.services.visual_comparison_service import EnhancedVisualComparisonService


def print_separator(title):
    """طباعة فاصل مع عنوان"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def test_landing_ai_service():
    """اختبار خدمة LandingAI"""
    print_separator("🧪 اختبار خدمة LandingAI")
    
    try:
        service = LandingAIService()
        
        # فحص الصحة
        print("🔍 فحص صحة الخدمة...")
        health = await service.health_check()
        print(f"   ✅ الحالة: {health.get('status', 'غير معروف')}")
        print(f"   📋 الوضع: {health.get('mode', 'غير محدد')}")
        
        # اختبار ملف
        test_image = "103.jpg"
        if os.path.exists(test_image):
            print(f"\n📄 اختبار استخراج النص من: {test_image}")
            start_time = time.time()
            
            result = await service.extract_from_file(test_image)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"   ✅ نجح الاستخراج: {result.success}")
            print(f"   📊 عدد الأحرف: {len(result.markdown_content)}")
            print(f"   🎯 الثقة: {result.confidence_score:.2%}")
            print(f"   ⏱️ الوقت: {processing_time:.2f} ثانية")
            
            return True
        else:
            print(f"   ❌ ملف الاختبار غير موجود: {test_image}")
            return False
            
    except Exception as e:
        print(f"   ❌ خطأ في اختبار LandingAI: {e}")
        return False


async def test_visual_comparison():
    """اختبار المقارنة البصرية"""
    print_separator("🖼️ اختبار المقارنة البصرية")
    
    try:
        service = EnhancedVisualComparisonService()
        
        # ملفات اختبار
        old_image = "103.jpg"
        new_image = "104.jpg"
        
        if os.path.exists(old_image) and os.path.exists(new_image):
            print(f"📷 مقارنة: {old_image} vs {new_image}")
            start_time = time.time()
            
            result = await service.compare_images(old_image, new_image)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"   ✅ نجحت المقارنة: {result.get('success', False)}")
            print(f"   📊 التشابه: {result.get('similarity', 0):.2%}")
            print(f"   📈 SSIM: {result.get('ssim_score', 0):.2%}")
            print(f"   ⏱️ الوقت: {processing_time:.2f} ثانية")
            
            return True
        else:
            print(f"   ❌ ملفات الاختبار غير موجودة")
            return False
            
    except Exception as e:
        print(f"   ❌ خطأ في اختبار المقارنة البصرية: {e}")
        return False


def test_celery_tasks():
    """اختبار مهام Celery"""
    print_separator("⚙️ اختبار مهام Celery")
    
    try:
        # اختبار المقارنة السريعة
        old_image = "103.jpg"
        new_image = "104.jpg"
        session_id = f"test_{int(time.time())}"
        
        if os.path.exists(old_image) and os.path.exists(new_image):
            print(f"🚀 بدء المقارنة السريعة...")
            print(f"   📷 الصور: {old_image} vs {new_image}")
            print(f"   🆔 الجلسة: {session_id}")
            
            start_time = time.time()
            
            # تشغيل المهمة
            task = quick_dual_comparison.delay(session_id, old_image, new_image)
            
            print(f"   📋 معرف المهمة: {task.id}")
            print(f"   ⏳ انتظار النتيجة...")
            
            # انتظار النتيجة (حتى 5 دقائق)
            result = task.get(timeout=300)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"\n   🎉 اكتملت المقارنة!")
            print(f"   📊 التشابه الإجمالي: {result['overall_similarity']:.2%}")
            print(f"   ⏱️ وقت المعالجة الإجمالي: {total_time:.2f} ثانية")
            print(f"   ⚡ كفاءة المعالجة: {result['parallel_efficiency']:.1f}%")
            
            # تفاصيل المراحل
            print(f"\n   📋 تفاصيل المراحل:")
            print(f"      📝 استخراج النص القديم: {result['old_text_extraction']['processing_time']:.2f}s")
            print(f"      📝 استخراج النص الجديد: {result['new_text_extraction']['processing_time']:.2f}s")
            print(f"      🖼️ المقارنة البصرية: {result['visual_comparison']['processing_time']:.2f}s")
            print(f"      🤖 تحليل Gemini: {result['gemini_analysis']['processing_time']:.2f}s")
            
            return True
        else:
            print(f"   ❌ ملفات الاختبار غير موجودة")
            return False
            
    except Exception as e:
        print(f"   ❌ خطأ في اختبار Celery: {e}")
        return False


def test_parallel_extraction():
    """اختبار استخراج النص المتوازي"""
    print_separator("📄 اختبار استخراج النص المتوازي")
    
    try:
        # قائمة الصور للاختبار
        test_images = []
        for image_name in ["103.jpg", "104.jpg", "101.jpg"]:
            if os.path.exists(image_name):
                test_images.append(image_name)
        
        if len(test_images) < 2:
            print("   ❌ نحتاج إلى صورتين على الأقل للاختبار")
            return False
        
        print(f"📷 اختبار استخراج النص من {len(test_images)} صور...")
        session_id = f"parallel_test_{int(time.time())}"
        
        start_time = time.time()
        
        # تشغيل المهمة
        task = parallel_extract_text_batch.delay(test_images, session_id)
        
        print(f"   📋 معرف المهمة: {task.id}")
        print(f"   ⏳ انتظار النتيجة...")
        
        # انتظار النتيجة
        results = task.get(timeout=180)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n   🎉 اكتمل الاستخراج المتوازي!")
        print(f"   ⏱️ الوقت الإجمالي: {total_time:.2f} ثانية")
        print(f"   📊 معدل النجاح: {len([r for r in results if r.get('success')])}/{len(results)}")
        
        # تفاصيل كل صورة
        for i, (image, result) in enumerate(zip(test_images, results)):
            success = result.get('success', False)
            word_count = result.get('word_count', 0)
            processing_time = result.get('processing_time', 0)
            
            print(f"      📷 {i+1}. {image}: {'✅' if success else '❌'} "
                  f"({word_count} كلمة, {processing_time:.2f}s)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في اختبار الاستخراج المتوازي: {e}")
        return False


async def run_comprehensive_test():
    """تشغيل اختبار شامل للنظام"""
    print_separator("🧪 اختبار شامل للنظام السريع")
    
    start_time = datetime.now()
    
    tests = [
        ("خدمة LandingAI", test_landing_ai_service()),
        ("المقارنة البصرية", test_visual_comparison()),
        ("مهام Celery", lambda: test_celery_tasks()),
        ("الاستخراج المتوازي", lambda: test_parallel_extraction())
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 تشغيل اختبار: {test_name}")
        try:
            if asyncio.iscoroutine(test_func):
                result = await test_func
            else:
                result = test_func()
            results.append((test_name, result))
            print(f"   {'✅ نجح' if result else '❌ فشل'}")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            results.append((test_name, False))
    
    # النتائج النهائية
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_separator("📊 ملخص نتائج الاختبار")
    
    passed = len([r for r in results if r[1]])
    total = len(results)
    
    print(f"🎯 النتائج الإجمالية: {passed}/{total} اختبارات نجحت")
    print(f"⏱️ وقت التشغيل: {duration:.2f} ثانية")
    
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"   • {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام.")
    else:
        print(f"\n⚠️ بعض الاختبارات فشلت. يرجى مراجعة الإعدادات.")
    
    return passed == total


if __name__ == "__main__":
    print("🚀 بدء اختبار النظام السريع للمقارنة المتوازية")
    print(f"📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # تشغيل الاختبار الشامل
        success = asyncio.run(run_comprehensive_test())
        
        if success:
            print(f"\n🎊 اكتمل الاختبار بنجاح! النظام جاهز.")
            sys.exit(0)
        else:
            print(f"\n💥 فشل في بعض الاختبارات.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n🛑 تم إيقاف الاختبار بواسطة المستخدم.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ فادح في الاختبار: {e}")
        sys.exit(1) 