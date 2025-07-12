#!/usr/bin/env python3
"""
برنامج اختبار سريع لـ Landing AI مع الصورة 101.jpg
Fast Landing AI test with 101.jpg
"""

import os
import sys
import asyncio
from pathlib import Path

# إضافة المسار إلى PYTHONPATH
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "backend"))

def test_direct_agentic_doc():
    """اختبار مباشر لـ agentic_doc"""
    print("🚀 اختبار مباشر لـ agentic_doc مع الصورة 101.jpg")
    
    try:
        from agentic_doc.parse import parse
        import time
        
        image_path = "d:/ezz/compair/edu-compare-wizard/101.jpg"
        
        if not os.path.exists(image_path):
            print(f"❌ الصورة غير موجودة: {image_path}")
            return
        
        print(f"📸 معالجة الصورة: {image_path}")
        
        # تعيين مهلة أطول
        os.environ['REQUESTS_TIMEOUT'] = '600'  # 10 دقائق
        os.environ['HTTP_TIMEOUT'] = '600'
        os.environ['HTTPX_TIMEOUT'] = '600'
        
        start_time = time.time()
        
        print("🔄 بدء التحليل...")
        result = parse(image_path)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ وقت المعالجة: {processing_time:.1f} ثانية")
        
        if result and len(result) > 0:
            doc = result[0]
            content = getattr(doc, 'markdown', '')
            chunks = getattr(doc, 'chunks', [])
            
            print(f"✅ تم الاستخراج بنجاح!")
            print(f"📝 طول المحتوى: {len(content)} حرف")
            print(f"🧩 عدد القطع: {len(chunks)}")
            
            # عرض أول 300 حرف
            if content:
                preview = content[:300] + "..." if len(content) > 300 else content
                print(f"📖 معاينة المحتوى:\n{preview}")
            
            # حفظ النتيجة
            output_file = "101_extracted_content.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# النص المستخرج من 101.jpg\n\n")
                f.write(f"**وقت المعالجة:** {processing_time:.1f} ثانية\n\n")
                f.write(f"**عدد الأحرف:** {len(content)}\n\n")
                f.write(f"**عدد القطع:** {len(chunks)}\n\n")
                f.write("## المحتوى:\n\n")
                f.write(content)
            
            print(f"💾 تم حفظ النتيجة في: {output_file}")
            
        else:
            print("❌ لم يتم الحصول على نتائج")
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        print(f"🔍 نوع الخطأ: {type(e).__name__}")
        
        # تحليل الخطأ
        error_str = str(e).lower()
        if "timeout" in error_str:
            print("🕒 السبب: انتهاء المهلة الزمنية")
        elif "connection" in error_str:
            print("🌐 السبب: مشكلة في الاتصال")
        elif "server" in error_str:
            print("🏢 السبب: مشكلة في خادم Landing AI")

def test_with_smaller_image():
    """اختبار مع صورة مصغرة"""
    print("\n🖼️ اختبار مع صورة مصغرة...")
    
    try:
        from PIL import Image
        from agentic_doc.parse import parse
        import time
        import tempfile
        
        original_path = "d:/ezz/compair/edu-compare-wizard/101.jpg"
        
        # تصغير الصورة
        with Image.open(original_path) as img:
            print(f"📐 الحجم الأصلي: {img.size}")
            
            # تصغير إلى 1024px كحد أقصى
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                print(f"📏 الحجم الجديد: {img.size}")
                
                # حفظ الصورة المصغرة
                temp_path = "101_small.jpg"
                img.save(temp_path, quality=85, format='JPEG')
                print(f"💾 تم حفظ الصورة المصغرة: {temp_path}")
                
                # اختبار التحليل
                start_time = time.time()
                result = parse(temp_path)
                end_time = time.time()
                
                print(f"⏱️ وقت المعالجة للصورة المصغرة: {end_time - start_time:.1f} ثانية")
                
                if result and len(result) > 0:
                    doc = result[0]
                    content = getattr(doc, 'markdown', '')
                    print(f"✅ نجح مع الصورة المصغرة! طول المحتوى: {len(content)} حرف")
                else:
                    print("❌ فشل مع الصورة المصغرة")
                    
                # تنظيف
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            else:
                print("📏 الصورة بالفعل صغيرة بما فيه الكفاية")
                
    except Exception as e:
        print(f"❌ خطأ في اختبار الصورة المصغرة: {e}")

if __name__ == "__main__":
    print("🧪 اختبار Landing AI السريع")
    print("=" * 40)
    
    # 1. اختبار مباشر
    test_direct_agentic_doc()
    
    # 2. اختبار مع صورة مصغرة
    test_with_smaller_image()
    
    print("\n🏁 انتهى الاختبار")
