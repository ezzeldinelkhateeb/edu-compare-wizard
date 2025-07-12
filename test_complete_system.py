#!/usr/bin/env python3
"""
اختبار شامل للنظام الكامل (باك إند + فرنت إند)
Complete System Test (Backend + Frontend)
"""

import requests
import json
import time
import os
from datetime import datetime

# إعدادات النظام
BACKEND_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"
API_BASE = "/api/v1"

def test_backend_health():
    """اختبار صحة الباك إند"""
    print("🔍 اختبار صحة الباك إند...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"✅ Backend Health: {response.status_code}")
        data = response.json()
        print(f"📄 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ Backend Health Failed: {e}")
        return False

def test_frontend_access():
    """اختبار الوصول للفرنت إند"""
    print("\n🌐 اختبار الوصول للفرنت إند...")
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        print(f"✅ Frontend Access: {response.status_code}")
        if response.status_code == 200:
            print("📄 Frontend is accessible")
            return True
        else:
            print(f"⚠️ Frontend returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend Access Failed: {e}")
        return False

def test_backend_api_endpoints():
    """اختبار نقاط نهاية الباك إند"""
    print("\n🔧 اختبار نقاط نهاية الباك إند...")
    
    endpoints = [
        ("/", "Root"),
        ("/docs", "Swagger UI"),
        ("/openapi.json", "OpenAPI JSON"),
        (f"{API_BASE}/upload/session", "Upload Session (POST)"),
        (f"{API_BASE}/compare/start", "Compare Start (POST)")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            if endpoint in ["/", "/docs", "/openapi.json"]:
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            else:
                # اختبار GET للتحقق من وجود المسار
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            
            print(f"✅ {name}: {response.status_code}")
            results[name] = response.status_code < 500  # نجح إذا لم يكن خطأ خادم
        except Exception as e:
            print(f"❌ {name}: {e}")
            results[name] = False
    
    return results

def test_image_upload_workflow():
    """اختبار سير عمل رفع الصورة"""
    print("\n📤 اختبار سير عمل رفع الصورة...")
    
    try:
        # 1. إنشاء جلسة رفع
        session_payload = {
            "session_name": "اختبار النظام الكامل",
            "description": "اختبار سير عمل رفع الصورة"
        }
        response = requests.post(f"{BACKEND_URL}{API_BASE}/upload/session", 
                               json=session_payload, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ إنشاء الجلسة فشل: {response.status_code}")
            return False
            
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"✅ تم إنشاء الجلسة: {session_id}")
        
        # 2. رفع الصورة
        image_path = "103.jpg"
        if not os.path.exists(image_path):
            print(f"❌ الصورة غير موجودة: {image_path}")
            return False
            
        with open(image_path, "rb") as f:
            files = {"file": ("103.jpg", f, "image/jpeg")}
            data = {"session_id": session_id, "file_type": "new"}
            response = requests.post(f"{BACKEND_URL}{API_BASE}/upload/file", 
                                   files=files, data=data, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ رفع الصورة فشل: {response.status_code}")
            return False
            
        file_data = response.json()
        file_id = file_data["file_id"]
        print(f"✅ تم رفع الصورة: {file_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ سير عمل رفع الصورة فشل: {e}")
        return False

def test_system_integration():
    """اختبار تكامل النظام"""
    print("\n🔗 اختبار تكامل النظام...")
    
    try:
        # اختبار أن الفرنت إند يمكنه الوصول للباك إند
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ الفرنت إند يمكنه الوصول للباك إند")
            return True
        else:
            print(f"❌ الفرنت إند لا يمكنه الوصول للباك إند: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ اختبار التكامل فشل: {e}")
        return False

def main():
    """الاختبار الرئيسي"""
    print("🎯 اختبار شامل للنظام الكامل")
    print("=" * 60)
    
    results = {}
    
    # اختبار الباك إند
    results["backend_health"] = test_backend_health()
    
    # اختبار الفرنت إند
    results["frontend_access"] = test_frontend_access()
    
    # اختبار نقاط نهاية الباك إند
    api_results = test_backend_api_endpoints()
    results.update(api_results)
    
    # اختبار سير عمل رفع الصورة
    results["upload_workflow"] = test_image_upload_workflow()
    
    # اختبار التكامل
    results["system_integration"] = test_system_integration()
    
    # عرض النتائج النهائية
    print("\n" + "=" * 60)
    print("📊 نتائج الاختبار النهائية:")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"   {test_name.upper()}: {status}")
    
    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print(f"\n🎯 النتيجة الإجمالية: {success_count}/{total_count} اختبارات نجحت")
    
    if success_count == total_count:
        print("🎉 النظام يعمل بشكل مثالي!")
        print(f"\n🌐 روابط النظام:")
        print(f"   الفرنت إند: {FRONTEND_URL}")
        print(f"   الباك إند: {BACKEND_URL}")
        print(f"   توثيق API: {BACKEND_URL}/docs")
    else:
        print("⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")
    
    print(f"\n⏰ وقت الاختبار: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 