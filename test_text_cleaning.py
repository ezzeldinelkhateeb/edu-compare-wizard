#!/usr/bin/env python3
"""
اختبار نظام تنظيف النصوص المحسن من Landing AI
Enhanced Text Cleaning System Test for Landing AI

يشمل:
1. تنظيف متقدم للنصوص
2. معالجة ملفات متعددة
3. إحصائيات مفصلة
4. مقارنة مع النظام المحسن
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
import time
import re

def clean_landing_ai_text(text):
    """تنظيف النصوص من تفاصيل Landing AI الزائدة - النسخة الأصلية"""
    import re
    
    # إزالة أوصاف الصور والتفاصيل التقنية
    text = re.sub(r'Summary\s*:\s*This[\s\S]*?<!-- figure[\s\S]*?-->', '', text)
    text = re.sub(r'photo:\s*[\s\S]*?Analysis\s*:[\s\S]*?<!-- figure[\s\S]*?-->', '', text)
    text = re.sub(r'illustration:\s*[\s\S]*?Analysis\s*:[\s\S]*?<!-- figure[\s\S]*?-->', '', text)
    
    # إزالة التفاصيل التقنية من Landing AI
    text = re.sub(r'<!-- text,[\s\S]*?-->', '', text)
    text = re.sub(r'<!-- figure,[\s\S]*?-->', '', text)
    text = re.sub(r'<!-- marginalia,[\s\S]*?-->', '', text)
    
    # إزالة النص الإنجليزي العام
    text = re.sub(r'Scene Overview\s*:[\s\S]*?(?=\n\n|\n[أ-ي])', '', text)
    text = re.sub(r'Technical Details\s*:[\s\S]*?(?=\n\n|\n[أ-ي])', '', text)
    text = re.sub(r'Spatial Relationships\s*:[\s\S]*?(?=\n\n|\n[أ-ي])', '', text)
    text = re.sub(r'Analysis\s*:[\s\S]*?(?=\n\n|\n[أ-ي])', '', text)
    
    # تنظيف النص من الأسطر الفارغة المتكررة
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()

def clean_landing_ai_text_enhanced(text):
    """تنظيف محسن للنصوص - النسخة المحسنة"""
    if not text:
        return ""
    
    original_length = len(text)
    
    # 1. إزالة جميع التعليقات HTML وتفاصيل Landing AI
    patterns_to_remove = [
        r'<!--[\s\S]*?-->',
        r'<!-- text,[\s\S]*?-->',
        r'<!-- figure,[\s\S]*?-->',
        r'<!-- marginalia,[\s\S]*?-->',
        r'<!-- illustration,[\s\S]*?-->',
        r'<!-- table,[\s\S]*?-->',
        
        # إزالة أقسام وصف الصور الكاملة
        r'Summary\s*:\s*This[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'photo\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'illustration\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'Scene Overview\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'Technical Details\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'Spatial Relationships\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'Analysis\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        
        # إزالة الإحداثيات والتفاصيل التقنية
        r'from page \d+ \(l=[\d.]+,t=[\d.]+,r=[\d.]+,b=[\d.]+\)',
        r'with ID [a-f0-9\-]+',
        r'\(l=[\d.]+,t=[\d.]+,r=[\d.]+,b=[\d.]+\)',
        
        # إزالة النصوص الإنجليزية غير المفيدة
        r'The image[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'This figure[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'The figure[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        r'^\s*•\s+The[\s\S]*?(?=\n)',
        r'^\s*•\s+Each[\s\S]*?(?=\n)',
        r'^\s*•\s+No scale[\s\S]*?(?=\n)',
        r'^\s*•\s+Arabic text[\s\S]*?(?=\n)',
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL)
    
    # 2. تنظيف خاص بالنص العربي
    # إزالة الأحرف الغريبة والرموز غير المرغوبة
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\w\s\.\,\!\?\:\;\(\)\[\]\{\}\-\+\=\$\%\@\#\*\/\\\|]', '', text)
    
    # تصحيح المسافات حول علامات الترقيم العربية
    text = re.sub(r'\s*([،؛؟!])\s*', r'\1 ', text)
    text = re.sub(r'\s*([:])\s*', r'\1 ', text)
    
    # 3. إزالة السطور التي تحتوي على كلمات مفتاحية فقط
    lines = text.split('\n')
    cleaned_lines = []
    
    keywords_to_skip = [
        'summary :', 'photo:', 'illustration:', 'scene overview:', 
        'technical details:', 'spatial relationships:', 'analysis :',
        '---', 'figure', 'image'
    ]
    
    for line in lines:
        line_lower = line.strip().lower()
        
        # تخطي السطور الفارغة أو التي تحتوي على كلمات مفتاحية فقط
        if not line_lower or line_lower in keywords_to_skip:
            continue
        
        # تخطي السطور التي تبدأ بـ bullet points وتحتوي على وصف إنجليزي
        if re.match(r'^\s*•\s', line) and any(word in line_lower for word in ['figure', 'image', 'scene', 'shown', 'depicts']):
            continue
        
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # 4. تنظيف المسافات والأسطر الفارغة
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)
    text = text.strip()
    
    # إحصائيات التحسن
    cleaned_length = len(text)
    improvement = ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0
    
    return text, improvement

async def test_enhanced_processing():
    """اختبار النظام المحسن"""
    print("\n" + "=" * 60)
    print("🚀 اختبار النظام المحسن لمعالجة النصوص")
    print("=" * 60)
    
    try:
        # استيراد النظام المحسن
        from enhanced_text_processing_system import AdvancedTextProcessor, process_single_file, process_directory
        
        # اختبار معالجة ملف واحد
        test_file = "d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results/extraction_20250705_172654/extracted_content.md"
        if Path(test_file).exists():
            print("📄 اختبار معالجة ملف واحد بالنظام المحسن...")
            start_time = time.time()
            
            result = await process_single_file(test_file)
            
            processing_time = time.time() - start_time
            
            print(f"✅ النظام المحسن:")
            print(f"   📏 الطول الأصلي: {result.metadata['original_length']:,} حرف")
            print(f"   📏 الطول بعد التنظيف: {result.metadata['cleaned_length']:,} حرف")
            print(f"   📊 تحسن: {result.metadata['reduction_percentage']:.1f}%")
            print(f"   ⏱️ وقت المعالجة: {processing_time:.3f}s")
            print(f"   🎯 نوع المحتوى: {result.content_type.value}")
            print(f"   🔧 أجزاء محذوفة: {len(result.chunks_removed)}")
            print(f"   ✅ أجزاء محفوظة: {len(result.chunks_kept)}")
            
            # طباعة عينة من النص المنظف
            if result.cleaned_text:
                print(f"\n📝 عينة من النص المنظف:")
                print("-" * 30)
                sample = result.cleaned_text[:300] + "..." if len(result.cleaned_text) > 300 else result.cleaned_text
                print(sample)
        
        # اختبار معالجة مجلد
        test_dir = "d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results"
        if Path(test_dir).exists():
            print(f"\n📁 اختبار معالجة مجلد بالنظام المحسن...")
            start_time = time.time()
            
            batch_result = await process_directory(test_dir, ['.md'])
            
            processing_time = time.time() - start_time
            
            print(f"✅ النظام المحسن - معالجة مجمعة:")
            print(f"   📊 إجمالي الملفات: {batch_result.total_files}")
            print(f"   ✅ تم معالجة: {batch_result.processed_files}")
            print(f"   ❌ فشل: {batch_result.failed_files}")
            print(f"   ⏱️ الوقت الإجمالي: {processing_time:.2f}s")
            print(f"   🚀 السرعة: {batch_result.summary_stats.get('files_per_second', 0):.2f} ملف/ثانية")
            print(f"   📊 متوسط التحسن: {batch_result.summary_stats.get('average_reduction_percentage', 0):.1f}%")
            
            if 'content_type_distribution' in batch_result.summary_stats:
                print(f"   🎯 توزيع أنواع المحتوى:")
                for content_type, count in batch_result.summary_stats['content_type_distribution'].items():
                    print(f"      - {content_type}: {count} ملف")
        
    except ImportError as e:
        print(f"❌ فشل استيراد النظام المحسن: {e}")
        print("💡 تأكد من وجود ملف enhanced_text_processing_system.py")

async def test_fast_folder_processing():
    """اختبار معالجة المجلدات السريعة"""
    print("\n" + "=" * 60)
    print("⚡ اختبار نظام معالجة المجلدات السريع")
    print("=" * 60)
    
    try:
        from fast_folder_processor import FastFolderProcessor, quick_process_folder
        
        test_dir = "d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results"
        if Path(test_dir).exists():
            print(f"📁 معالجة سريعة للمجلد: {test_dir}")
            
            start_time = time.time()
            result = await quick_process_folder(test_dir, max_workers=8)
            processing_time = time.time() - start_time
            
            print(f"✅ النظام السريع:")
            print(f"   📊 إجمالي الملفات: {result['processing_summary']['total_files']}")
            print(f"   ✅ تم معالجة: {result['processing_summary']['completed_files']}")
            print(f"   ❌ فشل: {result['processing_summary']['failed_files']}")
            print(f"   📈 معدل النجاح: {result['processing_summary']['success_rate']:.1f}%")
            print(f"   ⏱️ الوقت الإجمالي: {processing_time:.2f}s")
            print(f"   🚀 السرعة: {result['processing_summary']['files_per_second']:.2f} ملف/ثانية")
            
            if 'optimization_summary' in result and result['optimization_summary']:
                opt = result['optimization_summary']
                print(f"   📊 متوسط التحسن: {opt.get('average_reduction_percentage', 0):.1f}%")
                print(f"   💾 توفير مساحة: {opt.get('total_size_saved', 0):,} حرف")
            
            if 'performance_metrics' in result:
                perf = result['performance_metrics']
                print(f"   🧠 ذروة الذاكرة: {perf.get('peak_memory_mb', 0):.1f}MB")
                print(f"   ⚙️ متوسط المعالج: {perf.get('average_cpu_usage', 0):.1f}%")
        
    except ImportError as e:
        print(f"❌ فشل استيراد النظام السريع: {e}")
        print("💡 تأكد من وجود ملف fast_folder_processor.py")

def test_cleaning():
    """اختبار دالة التنظيف - النسخة المحسنة"""
    
    # نص تجريبي مشابه لما يأتي من Landing AI
    test_text = """
3
الفصل <!-- text, from page 0 (l=0.851,t=0.033,r=0.924,b=0.075), with ID 321af0af-bb97-4061-b683-7f701f6c448e -->

* قام العالم الفرنسي باسكال بصياغة هذه النتيجة كما يلي : <!-- text, from page 0 (l=0.462,t=0.087,r=0.931,b=0.113), with ID 221532e8-d6f1-4918-b3f3-cf9026d8fffb -->

قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل، كما ينتقل إلى جدران الإناء. <!-- text, from page 0 (l=0.071,t=0.118,r=0.928,b=0.194), with ID bfaa5219-276c-4a50-ae54-520cabdc6758 -->

ملاحظة

تخضع السوائل لقاعدة باسكال بينما لا تخضع الغازات لها،
لأن السوائل غير قابلة للانضغاط فينتقل الضغط المؤثر عليها بكامله إلى جميع أجزاء السائل، أما الغازات فهي قابلة للانضغاط لوجود مسافات بينية كبيرة نسبياً بين جزيئات الغاز فيستهلك جزء من الشغل المبذول لضغط جزيئات الغاز وبالتالي ينتقل الضغط جزئياً خلال الغازات. <!-- text, from page 0 (l=0.071,t=0.208,r=0.940,b=0.345), with ID 35c1e55d-d146-4eaa-afdc-ad13453669f6 -->

تطبيقات على قاعدة باسكال <!-- text, from page 0 (l=0.616,t=0.360,r=0.930,b=0.400), with ID 9c1126ff-68bf-4d00-a4ad-774eaceb4fbe -->

Summary : This image presents two examples of hydraulic systems in use, specifically highlighting a hydraulic jack and hydraulic car brakes, with accompanying photographs and Arabic labels.

photo:
Scene Overview :
  • The image is divided into two circular sections, each showing a different hydraulic application.
  • Left circle: Close-up photo of a car's hydraulic brake system, showing the brake disc and caliper.
  • Right circle: Photo of a hydraulic jack lifting a heavy vehicle (likely a truck or construction vehicle) at a worksite.
  • Each section is numbered (1 and 2) and has a colored arc above it (red for 1, green for 2).

Technical Details :
  • Arabic text under the right image: "المكبس الهيدروليكي" (The hydraulic jack).
  • Arabic text under the left image: "الفرامل الهيدروليكية للسيارة" (The hydraulic brakes for the car).
  • No scale bars or magnification indicators are present.
  • The images are clear, with the main hydraulic components in focus.

Spatial Relationships :
  • The two images are presented side by side, separated by a dotted vertical line.
  • The hydraulic jack (right) is shown in an outdoor, industrial context; the car brake (left) is shown in a mechanical/garage context.
  • Both images use a circular crop, emphasizing the main subject.

Analysis :
  • The figure visually contrasts two common uses of hydraulic systems: lifting heavy vehicles and stopping cars.
  • The layout and numbering suggest a comparison or categorization of hydraulic applications.
  • The use of clear, labeled photographs aids in understanding the practical implementation of hydraulic technology. <!-- figure, from page 0 (l=0.579,t=0.406,r=0.921,b=0.585), with ID 571f38a7-8703-4517-bfae-c7a9d79f8bb2 -->

وفيما يلي ستتعرض بشيء من التفصيل للمكبس الهيدروليكي. <!-- text, from page 0 (l=0.438,t=0.595,r=0.931,b=0.625), with ID 85a5d707-ad5d-4bab-bbf8-f3d3699d4429 -->

Hydraulic press المكبس الهيدروليكي <!-- text, from page 0 (l=0.513,t=0.635,r=0.931,b=0.670), with ID e1c1a790-4c1f-49e9-94ea-0303e9f93160 -->

أنبوبة موصلة بمكبسَين أحدهما صغير مساحة مقطعه a  
والآخر كبير مساحة مقطعه A ويمتلئ الحيز بين المكبسين  
بسائل مناسب (سائل هيدروليكي) كما بالشكل. <!-- text, from page 0 (l=0.405,t=0.676,r=0.949,b=0.781), with ID 6a5beaf4-68a8-4e89-ae48-20c2fc6c65eb -->

$10.4$ <!-- marginalia, from page 0 (l=0.869,t=0.921,r=0.923,b=0.950), with ID 4ea3448d-3d90-42b0-8735-1d4e9a3370f8 -->
"""

    print("🔍 مقارنة طرق التنظيف:")
    print("=" * 60)
    
    # 1. الطريقة الأصلية
    start_time = time.time()
    cleaned_original = clean_landing_ai_text(test_text)
    time_original = time.time() - start_time
    
    # 2. الطريقة المحسنة
    start_time = time.time()
    cleaned_enhanced, improvement = clean_landing_ai_text_enhanced(test_text)
    time_enhanced = time.time() - start_time
    
    print(f"📊 إحصائيات المقارنة:")
    print(f"   📏 النص الأصلي: {len(test_text):,} حرف")
    print()
    print(f"🔧 الطريقة الأصلية:")
    print(f"   📏 النتيجة: {len(cleaned_original):,} حرف")
    print(f"   📊 التحسن: {((len(test_text) - len(cleaned_original)) / len(test_text) * 100):.1f}%")
    print(f"   ⏱️ الوقت: {time_original:.6f}s")
    print()
    print(f"⚡ الطريقة المحسنة:")
    print(f"   📏 النتيجة: {len(cleaned_enhanced):,} حرف")
    print(f"   📊 التحسن: {improvement:.1f}%")
    print(f"   ⏱️ الوقت: {time_enhanced:.6f}s")
    print()
    
    # حساب مقدار التحسن الإضافي
    additional_improvement = len(cleaned_original) - len(cleaned_enhanced)
    additional_percentage = (additional_improvement / len(cleaned_original) * 100) if len(cleaned_original) > 0 else 0
    
    print(f"🎯 التحسن الإضافي بالطريقة المحسنة:")
    print(f"   📉 حروف إضافية محذوفة: {additional_improvement:,}")
    print(f"   📊 تحسن إضافي: {additional_percentage:.1f}%")
    print(f"   ⚡ تسريع: {(time_original / time_enhanced):.1f}x" if time_enhanced > 0 else "∞")
    
    print(f"\n📝 النص النهائي المحسن:")
    print("-" * 50)
    print(cleaned_enhanced)
    print("-" * 50)

    # إضافة اختبار ملفات حقيقية هنا مباشرة (غير async)
    print(f"\n📂 اختبار على ملفات حقيقية:")
    print("-" * 50)
    
    # البحث عن ملفات Landing AI
    base_dir = Path("d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results")
    
    if not base_dir.exists():
        print(f"❌ المجلد غير موجود: {base_dir}")
        return
    
    # البحث عن ملفات extracted_content.md
    md_files = list(base_dir.rglob("extracted_content.md"))
    json_files = list(base_dir.rglob("agentic_doc_result.json"))
    
    print(f"📊 تم العثور على:")
    print(f"   📄 {len(md_files)} ملف .md")
    print(f"   📄 {len(json_files)} ملف .json")
    
    # اختبار عينة من الملفات
    test_files = (md_files + json_files)[:5]  # أول 5 ملفات
    
    if not test_files:
        print("❌ لم يتم العثور على ملفات للاختبار")
        return
    
    print(f"\n🧪 اختبار {len(test_files)} ملف:")
    
    total_original = 0
    total_cleaned_old = 0
    total_cleaned_new = 0
    total_time_old = 0
    total_time_new = 0
    
    for i, file_path in enumerate(test_files, 1):
        try:
            print(f"\n{i}. 📄 {file_path.name}")
            
            # قراءة الملف
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    text = data.get('markdown', '') or data.get('text', '')
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            
            if not text:
                print("   ⚠️ الملف فارغ")
                continue
            
            # الطريقة الأصلية
            start_time = time.time()
            cleaned_old = clean_landing_ai_text(text)
            time_old = time.time() - start_time
            
            # الطريقة المحسنة
            start_time = time.time()
            cleaned_new, improvement = clean_landing_ai_text_enhanced(text)
            time_new = time.time() - start_time
            
            # إحصائيات
            print(f"   📏 الأصلي: {len(text):,} → القديم: {len(cleaned_old):,} → المحسن: {len(cleaned_new):,}")
            print(f"   📊 تحسن قديم: {((len(text) - len(cleaned_old)) / len(text) * 100):.1f}% → جديد: {improvement:.1f}%")
            print(f"   ⏱️ وقت قديم: {time_old:.4f}s → جديد: {time_new:.4f}s")
            
            # جمع الإحصائيات
            total_original += len(text)
            total_cleaned_old += len(cleaned_old)
            total_cleaned_new += len(cleaned_new)
            total_time_old += time_old
            total_time_new += time_new
            
        except Exception as e:
            print(f"   ❌ خطأ في معالجة {file_path.name}: {e}")
    
    # إحصائيات إجمالية
    if total_original > 0:
        print(f"\n📊 الإحصائيات الإجمالية:")
        print(f"   📏 إجمالي النص الأصلي: {total_original:,} حرف")
        print(f"   📏 النتيجة القديمة: {total_cleaned_old:,} حرف ({((total_original - total_cleaned_old) / total_original * 100):.1f}% تحسن)")
        print(f"   📏 النتيجة المحسنة: {total_cleaned_new:,} حرف ({((total_original - total_cleaned_new) / total_original * 100):.1f}% تحسن)")
        print(f"   ⏱️ الوقت الإجمالي القديم: {total_time_old:.4f}s")
        print(f"   ⏱️ الوقت الإجمالي المحسن: {total_time_new:.4f}s")
        print(f"   🚀 تسريع: {(total_time_old / total_time_new):.1f}x" if total_time_new > 0 else "∞")
        
        # تحسن إضافي
        additional_improvement = total_cleaned_old - total_cleaned_new
        additional_percentage = (additional_improvement / total_cleaned_old * 100) if total_cleaned_old > 0 else 0
        print(f"   🎯 تحسن إضافي: {additional_improvement:,} حرف ({additional_percentage:.1f}%)")

async def test_real_files():
    """اختبار على ملفات حقيقية"""
    print(f"\n📂 اختبار على ملفات حقيقية:")
    print("-" * 50)
    
    # البحث عن ملفات Landing AI
    base_dir = Path("d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results")
    
    if not base_dir.exists():
        print(f"❌ المجلد غير موجود: {base_dir}")
        return
    
    # البحث عن ملفات extracted_content.md
    md_files = list(base_dir.rglob("extracted_content.md"))
    json_files = list(base_dir.rglob("agentic_doc_result.json"))
    
    print(f"📊 تم العثور على:")
    print(f"   📄 {len(md_files)} ملف .md")
    print(f"   📄 {len(json_files)} ملف .json")
    
    # اختبار عينة من الملفات
    test_files = (md_files + json_files)[:5]  # أول 5 ملفات
    
    if not test_files:
        print("❌ لم يتم العثور على ملفات للاختبار")
        return
    
    print(f"\n🧪 اختبار {len(test_files)} ملف:")
    
    total_original = 0
    total_cleaned_old = 0
    total_cleaned_new = 0
    total_time_old = 0
    total_time_new = 0
    
    for i, file_path in enumerate(test_files, 1):
        try:
            print(f"\n{i}. 📄 {file_path.name}")
            
            # قراءة الملف
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    text = data.get('markdown', '') or data.get('text', '')
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            
            if not text:
                print("   ⚠️ الملف فارغ")
                continue
            
            # الطريقة الأصلية
            start_time = time.time()
            cleaned_old = clean_landing_ai_text(text)
            time_old = time.time() - start_time
            
            # الطريقة المحسنة
            start_time = time.time()
            cleaned_new, improvement = clean_landing_ai_text_enhanced(text)
            time_new = time.time() - start_time
            
            # إحصائيات
            print(f"   📏 الأصلي: {len(text):,} → القديم: {len(cleaned_old):,} → المحسن: {len(cleaned_new):,}")
            print(f"   📊 تحسن قديم: {((len(text) - len(cleaned_old)) / len(text) * 100):.1f}% → جديد: {improvement:.1f}%")
            print(f"   ⏱️ وقت قديم: {time_old:.4f}s → جديد: {time_new:.4f}s")
            
            # جمع الإحصائيات
            total_original += len(text)
            total_cleaned_old += len(cleaned_old)
            total_cleaned_new += len(cleaned_new)
            total_time_old += time_old
            total_time_new += time_new
            
        except Exception as e:
            print(f"   ❌ خطأ في معالجة {file_path.name}: {e}")
    
    # إحصائيات إجمالية
    if total_original > 0:
        print(f"\n📊 الإحصائيات الإجمالية:")
        print(f"   📏 إجمالي النص الأصلي: {total_original:,} حرف")
        print(f"   📏 النتيجة القديمة: {total_cleaned_old:,} حرف ({((total_original - total_cleaned_old) / total_original * 100):.1f}% تحسن)")
        print(f"   📏 النتيجة المحسنة: {total_cleaned_new:,} حرف ({((total_original - total_cleaned_new) / total_original * 100):.1f}% تحسن)")
        print(f"   ⏱️ الوقت الإجمالي القديم: {total_time_old:.4f}s")
        print(f"   ⏱️ الوقت الإجمالي المحسن: {total_time_new:.4f}s")
        print(f"   🚀 تسريع: {(total_time_old / total_time_new):.1f}x" if total_time_new > 0 else "∞")
        
        # تحسن إضافي
        additional_improvement = total_cleaned_old - total_cleaned_new
        additional_percentage = (additional_improvement / total_cleaned_old * 100) if total_cleaned_old > 0 else 0
        print(f"   🎯 تحسن إضافي: {additional_improvement:,} حرف ({additional_percentage:.1f}%)")

async def main():
    """الدالة الرئيسية"""
    print("🚀 نظام اختبار تنظيف النصوص المحسن")
    print("=" * 60)
    
    # اختبار التنظيف الأساسي
    test_cleaning()
    
    # اختبار النظام المحسن
    await test_enhanced_processing()
    
    # اختبار المعالجة السريعة
    await test_fast_folder_processing()
    
    print(f"\n🎉 اكتمل الاختبار!")
    print(f"💡 توصيات:")
    print(f"   1. استخدم النظام المحسن للحصول على أفضل جودة تنظيف")
    print(f"   2. استخدم النظام السريع لمعالجة مجلدات كبيرة")
    print(f"   3. اجمع بين النظامين للحصول على أفضل النتائج")

if __name__ == "__main__":
    asyncio.run(main())
