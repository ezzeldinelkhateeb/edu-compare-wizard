#!/usr/bin/env python3
"""
اختبار سريع للنظام المحسن - Quick Enhanced System Test
اختبار سريع لجميع المكونات والتحسينات الجديدة

الاستخدام:
python quick_system_test.py
"""

import asyncio
import time
from pathlib import Path
import json
import sys

def test_basic_cleaning():
    """اختبار تنظيف النصوص الأساسي"""
    print("🧹 اختبار تنظيف النصوص الأساسي...")
    
    # نص تجريبي مشابه لمخرجات Landing AI
    test_text = """
قاعدة باسكال <!-- text, from page 0 (l=0.468,t=0.075,r=0.939,b=0.132), with ID e6447f7d-320c-45b4-bdb5-304d769ede56 -->

عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل.

Summary : This image shows a hydraulic system with Arabic labels.

photo:
Scene Overview :
  • The image depicts a hydraulic press system.
  • Arabic text is visible labeling components.

Technical Details :
  • No scale bars present.
  • Clear visibility of hydraulic components.

Analysis :
  • The figure demonstrates Pascal's principle in hydraulic applications. <!-- figure, from page 0 (l=0.579,t=0.406,r=0.921,b=0.585), with ID 571f38a7 -->

$10.4$ <!-- marginalia, from page 0 (l=0.869,t=0.921,r=0.923,b=0.950), with ID 4ea3448d -->
"""
    
    # تجربة التنظيف الأساسي
    try:
        from test_text_cleaning import clean_landing_ai_text_enhanced
        
        start_time = time.time()
        cleaned_text, improvement = clean_landing_ai_text_enhanced(test_text)
        processing_time = time.time() - start_time
        
        print(f"   ✅ نجح التنظيف")
        print(f"   📏 النص الأصلي: {len(test_text)} حرف")
        print(f"   📏 النص المنظف: {len(cleaned_text)} حرف")
        print(f"   📊 التحسن: {improvement:.1f}%")
        print(f"   ⏱️ الوقت: {processing_time:.4f}s")
        print(f"   📝 عينة من النتيجة: {cleaned_text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ فشل التنظيف: {e}")
        return False

async def test_enhanced_processing():
    """اختبار النظام المحسن"""
    print("\n⚡ اختبار النظام المحسن...")
    
    try:
        from enhanced_text_processing_system import AdvancedTextProcessor
        
        # إنشاء معالج
        processor = AdvancedTextProcessor(num_workers=2)
        
        # إنشاء ملف تجريبي
        test_file = Path("temp_test_file.md")
        test_content = """
قاعدة باسكال <!-- text, with ID abc123 -->
هذا نص تعليمي مهم.

Summary : This is a test image.
photo:
Scene Overview :
  • Test image description.
<!-- figure, with ID def456 -->
"""
        
        # كتابة الملف التجريبي
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # معالجة الملف
        start_time = time.time()
        result = await processor.process_file_async(test_file)
        processing_time = time.time() - start_time
        
        # حذف الملف التجريبي
        test_file.unlink(missing_ok=True)
        
        print(f"   ✅ نجحت المعالجة المحسنة")
        print(f"   🎯 نوع المحتوى: {result.content_type.value}")
        print(f"   📊 التحسن: {result.metadata['reduction_percentage']:.1f}%")
        print(f"   ⏱️ الوقت: {processing_time:.4f}s")
        print(f"   🔧 أجزاء محذوفة: {len(result.chunks_removed)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ فشل النظام المحسن: {e}")
        return False

async def test_fast_processing():
    """اختبار المعالجة السريعة"""
    print("\n🚀 اختبار المعالجة السريعة...")
    
    try:
        from fast_folder_processor import FastFolderProcessor
        
        # إنشاء مجلد تجريبي مع ملفات
        test_dir = Path("temp_test_dir")
        test_dir.mkdir(exist_ok=True)
        
        # إنشاء ملفات تجريبية
        for i in range(3):
            test_file = test_dir / f"test_{i}.md"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(f"""
ملف اختبار {i}
محتوى تعليمي مهم.

Summary : Test content {i}.
<!-- technical details -->
""")
        
        # معالجة المجلد
        processor = FastFolderProcessor(max_workers=2, chunk_size=2)
        
        start_time = time.time()
        result = await processor.process_folder_structure(
            test_dir, 
            output_path=test_dir / "processed"
        )
        processing_time = time.time() - start_time
        
        # تنظيف الملفات التجريبية
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        
        print(f"   ✅ نجحت المعالجة السريعة")
        print(f"   📊 إجمالي الملفات: {result['processing_summary']['total_files']}")
        print(f"   ✅ تم معالجة: {result['processing_summary']['completed_files']}")
        print(f"   📈 معدل النجاح: {result['processing_summary']['success_rate']:.1f}%")
        print(f"   ⏱️ الوقت الإجمالي: {processing_time:.4f}s")
        print(f"   🚀 السرعة: {result['processing_summary']['files_per_second']:.2f} ملف/ثانية")
        
        return True
        
    except Exception as e:
        print(f"   ❌ فشل المعالجة السريعة: {e}")
        return False

def test_real_files():
    """اختبار على ملفات حقيقية إن وجدت"""
    print("\n📂 اختبار على ملفات حقيقية...")
    
    # البحث عن ملفات Landing AI
    search_paths = [
        "backend/uploads/landingai_results",
        "d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results"
    ]
    
    for search_path in search_paths:
        path = Path(search_path)
        if path.exists():
            md_files = list(path.rglob("*.md"))
            json_files = list(path.rglob("*.json"))
            
            print(f"   📁 تم العثور على مجلد: {path}")
            print(f"   📄 ملفات .md: {len(md_files)}")
            print(f"   📄 ملفات .json: {len(json_files)}")
            
            if md_files or json_files:
                print(f"   ✅ ملفات متاحة للاختبار")
                return True
    
    print(f"   ⚠️ لم يتم العثور على ملفات حقيقية للاختبار")
    return False

def check_dependencies():
    """فحص التبعيات المطلوبة"""
    print("🔍 فحص التبعيات...")
    
    required_modules = [
        'asyncio', 'pathlib', 'json', 'time', 're',
        'multiprocessing', 'concurrent.futures'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"   ❌ {module} غير متوفر")
    
    # فحص المكونات المخصصة
    custom_modules = [
        'enhanced_text_processing_system',
        'fast_folder_processor',
        'test_text_cleaning'
    ]
    
    for module in custom_modules:
        try:
            __import__(module)
            print(f"   ✅ {module} (مخصص)")
        except ImportError:
            print(f"   ⚠️ {module} (مخصص) غير متوفر")
    
    return len(missing_modules) == 0

async def run_comprehensive_test():
    """تشغيل اختبار شامل"""
    print("🚀 بدء الاختبار الشامل للنظام المحسن")
    print("=" * 60)
    
    # 1. فحص التبعيات
    deps_ok = check_dependencies()
    
    # 2. اختبار تنظيف النصوص الأساسي
    basic_ok = test_basic_cleaning()
    
    # 3. اختبار النظام المحسن
    enhanced_ok = await test_enhanced_processing()
    
    # 4. اختبار المعالجة السريعة
    fast_ok = await test_fast_processing()
    
    # 5. فحص الملفات الحقيقية
    real_files_ok = test_real_files()
    
    # النتائج النهائية
    print(f"\n📊 نتائج الاختبار:")
    print(f"   {'✅' if deps_ok else '❌'} التبعيات")
    print(f"   {'✅' if basic_ok else '❌'} التنظيف الأساسي")
    print(f"   {'✅' if enhanced_ok else '❌'} النظام المحسن") 
    print(f"   {'✅' if fast_ok else '❌'} المعالجة السريعة")
    print(f"   {'✅' if real_files_ok else '⚠️'} الملفات الحقيقية")
    
    total_score = sum([deps_ok, basic_ok, enhanced_ok, fast_ok])
    max_score = 4
    
    print(f"\n🎯 النتيجة الإجمالية: {total_score}/{max_score} ({total_score/max_score*100:.1f}%)")
    
    if total_score == max_score:
        print("🎉 النظام يعمل بشكل مثالي!")
    elif total_score >= 3:
        print("✅ النظام يعمل جيداً مع بعض المشاكل البسيطة")
    elif total_score >= 2:
        print("⚠️ النظام يعمل جزئياً - يحتاج إصلاحات")
    else:
        print("❌ النظام يحتاج إعداد وإصلاحات جذرية")
    
    return total_score >= 3

def print_usage_examples():
    """طباعة أمثلة الاستخدام"""
    print(f"\n💡 أمثلة الاستخدام:")
    print("-" * 30)
    
    print("1. تنظيف نص واحد:")
    print("```python")
    print("from test_text_cleaning import clean_landing_ai_text_enhanced")
    print("cleaned, improvement = clean_landing_ai_text_enhanced(text)")
    print("```")
    
    print("\n2. معالجة ملف واحد:")
    print("```python")
    print("from enhanced_text_processing_system import process_single_file")
    print("result = await process_single_file('file.md')")
    print("```")
    
    print("\n3. معالجة مجلد:")
    print("```python")
    print("from fast_folder_processor import quick_process_folder")
    print("result = await quick_process_folder('folder_path')")
    print("```")
    
    print("\n4. تشغيل الاختبار الشامل:")
    print("```bash")
    print("python test_text_cleaning.py")
    print("```")

async def main():
    """الدالة الرئيسية"""
    print("🔧 اختبار سريع للنظام المحسن")
    print("Quick Enhanced System Test")
    print("=" * 60)
    
    try:
        # تشغيل الاختبار الشامل
        success = await run_comprehensive_test()
        
        # طباعة أمثلة الاستخدام
        print_usage_examples()
        
        # النصائح النهائية
        print(f"\n📝 نصائح:")
        if success:
            print("   ✅ النظام جاهز للاستخدام")
            print("   🚀 جرب الملفات الحقيقية الآن")
            print("   📊 راقب الأداء مع الملفات الكبيرة")
        else:
            print("   🔧 تأكد من وجود جميع الملفات المطلوبة")
            print("   📦 تحقق من تثبيت جميع التبعيات")
            print("   🐛 راجع رسائل الأخطاء للتفاصيل")
        
        print(f"\n📚 للمزيد من التفاصيل:")
        print("   📖 اقرأ ENHANCED_SYSTEM_README.md")
        print("   🧪 شغل test_text_cleaning.py للاختبار الكامل")
        
        return success
        
    except KeyboardInterrupt:
        print(f"\n⏸️ تم إيقاف الاختبار بواسطة المستخدم")
        return False
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        return False

if __name__ == "__main__":
    # تشغيل الاختبار
    result = asyncio.run(main())
    
    # رمز الخروج
    sys.exit(0 if result else 1)
