#!/usr/bin/env python3
"""
اختبار رفع الصورة عبر API
Test image upload via API
"""

import requests
import json
import os
from pathlib import Path

def test_upload_image():
    """اختبار رفع الصورة"""
    
    print("🚀 بدء اختبار رفع الصورة عبر API...")
    
    # مسار الصورة
    image_path = "../103.jpg"
    if not os.path.exists(image_path):
        print(f"❌ الصورة غير موجودة: {image_path}")
        return None
    
    print(f"📄 رفع الصورة: {image_path}")
    print(f"📊 حجم الملف: {os.path.getsize(image_path) / 1024:.1f} KB")
    
    try:
        # رفع الصورة
        url = "http://localhost:8000/api/v1/upload"
        
        with open(image_path, 'rb') as f:
            files = {'files': (os.path.basename(image_path), f, 'image/jpeg')}
            data = {'category': 'old'}
            
            print("📤 رفع الملف...")
            response = requests.post(url, files=files, data=data)
        
        print(f"📊 رمز الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ تم رفع الصورة بنجاح!")
            print(f"📝 النتيجة: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            print(f"❌ فشل في رفع الصورة: {response.status_code}")
            print(f"📝 الخطأ: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في رفع الصورة: {e}")
        return None

def test_comparison():
    """اختبار بدء مقارنة"""
    
    print("\n⚖️ بدء اختبار المقارنة...")
    
    try:
        url = "http://localhost:8000/api/v1/compare/start"
        
        data = {
            "old_files": ["103.jpg"],
            "new_files": ["103.jpg"],  # نفس الملف للمقارنة
            "comparison_settings": {
                "enable_visual_comparison": True,
                "enable_text_comparison": True,
                "ai_analysis_depth": "detailed"
            }
        }
        
        print("📤 إرسال طلب المقارنة...")
        response = requests.post(url, json=data)
        
        print(f"📊 رمز الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ تم بدء المقارنة بنجاح!")
            print(f"📝 النتيجة: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            print(f"❌ فشل في بدء المقارنة: {response.status_code}")
            print(f"📝 الخطأ: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في المقارنة: {e}")
        return None

def test_health_check():
    """اختبار فحص صحة النظام"""
    
    print("🏥 اختبار فحص صحة النظام...")
    
    try:
        # فحص سريع
        response = requests.get("http://localhost:8000/health")
        print(f"📊 Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ {response.json()}")
        
        # فحص مفصل
        response = requests.get("http://localhost:8000/api/v1/health/detailed")
        print(f"📊 Detailed Health: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ فحص مفصل:")
            print(f"   الحالة العامة: {result.get('overall_status', 'غير معروف')}")
            print(f"   الرسالة: {result.get('message', 'غير معروف')}")
            
            services = result.get('services', {})
            for service_name, service_info in services.items():
                status = service_info.get('status', 'غير معروف')
                print(f"   {service_name}: {status}")
        
    except Exception as e:
        print(f"❌ خطأ في فحص الصحة: {e}")

def main():
    """الدالة الرئيسية"""
    
    print("=" * 60)
    print("🎯 اختبار API نظام مقارنة المناهج التعليمية")
    print("=" * 60)
    
    # اختبار فحص الصحة
    test_health_check()
    
    # اختبار رفع الصورة
    upload_result = test_upload_image()
    
    if upload_result:
        # اختبار المقارنة
        comparison_result = test_comparison()
        
        print("\n" + "=" * 60)
        print("📈 نتائج الاختبار النهائية:")
        print("=" * 60)
        print(f"✅ رفع الصورة: {'نجح' if upload_result else 'فشل'}")
        print(f"✅ بدء المقارنة: {'نجح' if comparison_result else 'فشل'}")
        
        if upload_result and comparison_result:
            print("🎉 API يعمل بنجاح!")
        else:
            print("⚠️ API يعمل جزئياً")
    else:
        print("\n❌ فشل الاختبار في مرحلة رفع الصورة")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 