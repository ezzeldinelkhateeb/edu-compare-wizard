#!/usr/bin/env python3
"""
سكريبت اختبار شامل للتكامل بين الفرنت إند والباك إند
Comprehensive Frontend-Backend Integration Test Script
"""

import requests
import json
import time
import os
from pathlib import Path

class FrontendBackendIntegrationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:8081"
        self.test_image_path = "103.jpg"
        
    def test_backend_health(self):
        """اختبار صحة الباك إند"""
        print("🔍 اختبار صحة الباك إند...")
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ الباك إند يعمل بشكل صحيح")
                print(f"   الحالة: {data.get('status')}")
                print(f"   الإصدار: {data.get('version')}")
                return True
            else:
                print(f"❌ الباك إند غير متاح - رمز الحالة: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ فشل في الاتصال بالباك إند: {e}")
            return False
    
    def test_frontend_availability(self):
        """اختبار توفر الفرنت إند"""
        print("🔍 اختبار توفر الفرنت إند...")
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ الفرنت إند يعمل بشكل صحيح على {self.frontend_url}")
                return True
            else:
                print(f"❌ الفرنت إند غير متاح - رمز الحالة: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ فشل في الاتصال بالفرنت إند: {e}")
            return False
    
    def test_backend_api_endpoints(self):
        """اختبار نقاط نهاية API الباك إند"""
        print("🔍 اختبار نقاط نهاية API الباك إند...")
        
        endpoints = [
            ("/api/v1/upload/session", "POST"),
            ("/api/v1/upload/file", "POST"),
            ("/api/v1/compare/start", "POST"),
            ("/api/v1/compare/status/{job_id}", "GET"),
            ("/api/v1/compare/result/{job_id}", "GET"),
        ]
        
        all_working = True
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    # اختبار GET مع job_id وهمي
                    test_endpoint = endpoint.replace("{job_id}", "test-123")
                    response = requests.get(f"{self.backend_url}{test_endpoint}", timeout=5)
                else:
                    # اختبار POST
                    response = requests.post(f"{self.backend_url}{endpoint}", timeout=5)
                
                # نتوقع 422 (Unprocessable Entity) أو 404 للاختبارات بدون بيانات صحيحة
                if response.status_code in [200, 422, 404]:
                    print(f"✅ {method} {endpoint} - متاح")
                else:
                    print(f"⚠️  {method} {endpoint} - رمز غير متوقع: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {method} {endpoint} - فشل: {e}")
                all_working = False
        
        return all_working
    
    def test_file_upload_workflow(self):
        """اختبار سير عمل رفع الملفات"""
        print("🔍 اختبار سير عمل رفع الملفات...")
        
        if not os.path.exists(self.test_image_path):
            print(f"❌ ملف الاختبار غير موجود: {self.test_image_path}")
            return False
        
        try:
            # 1. إنشاء جلسة رفع
            print("   📝 إنشاء جلسة رفع...")
            session_data = {
                "session_name": "test_session",
                "description": "جلسة اختبار"
            }
            response = requests.post(
                f"{self.backend_url}/api/v1/upload/session",
                json=session_data,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"   ❌ فشل في إنشاء الجلسة: {response.status_code}")
                print(f"   الاستجابة: {response.text}")
                return False
            
            session_info = response.json()
            session_id = session_info.get("session_id")
            print(f"   ✅ تم إنشاء الجلسة: {session_id}")
            
            # 2. رفع ملف
            print("   📤 رفع ملف...")
            with open(self.test_image_path, 'rb') as f:
                files = {'file': (os.path.basename(self.test_image_path), f, 'image/jpeg')}
                data = {
                    'session_id': session_id,
                    'file_type': 'old'
                }
                response = requests.post(
                    f"{self.backend_url}/api/v1/upload/file",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code != 200:
                print(f"   ❌ فشل في رفع الملف: {response.status_code}")
                print(f"   الاستجابة: {response.text}")
                return False
            
            file_info = response.json()
            file_id = file_info.get("file_id")
            print(f"   ✅ تم رفع الملف: {file_id}")
            
            # 3. رفع ملف ثاني للجديد
            print("   📤 رفع ملف جديد...")
            with open(self.test_image_path, 'rb') as f:
                files = {'file': (os.path.basename(self.test_image_path), f, 'image/jpeg')}
                data = {
                    'session_id': session_id,
                    'file_type': 'new'
                }
                response = requests.post(
                    f"{self.backend_url}/api/v1/upload/file",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code != 200:
                print(f"   ❌ فشل في رفع الملف الجديد: {response.status_code}")
                print(f"   الاستجابة: {response.text}")
                return False
            
            new_file_info = response.json()
            new_file_id = new_file_info.get("file_id")
            print(f"   ✅ تم رفع الملف الجديد: {new_file_id}")
            
            # 4. بدء المقارنة
            print("   🔄 بدء المقارنة...")
            comparison_data = {
                "session_id": session_id,
                "old_files": [file_id],
                "new_files": [new_file_id],
                "comparison_settings": {}
            }
            response = requests.post(
                f"{self.backend_url}/api/v1/compare/start",
                json=comparison_data,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"   ❌ فشل في بدء المقارنة: {response.status_code}")
                print(f"   الاستجابة: {response.text}")
                return False
            
            job_info = response.json()
            job_id = job_info.get("job_id")
            print(f"   ✅ تم بدء المقارنة: {job_id}")
            
            # 5. انتظار النتائج
            print("   ⏳ انتظار النتائج...")
            max_wait = 30
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    response = requests.get(
                        f"{self.backend_url}/api/v1/compare/result/{job_id}",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   ✅ تم الحصول على النتائج")
                        print(f"      نسبة التشابه: {result.get('similarity_percentage', 'غير متاح')}%")
                        return True
                    elif response.status_code == 202:
                        print(f"   ⏳ المعالجة جارية... ({wait_time}s)")
                        time.sleep(2)
                        wait_time += 2
                    else:
                        print(f"   ❌ خطأ في جلب النتائج: {response.status_code}")
                        print(f"   الاستجابة: {response.text}")
                        return False
                        
                except Exception as e:
                    print(f"   ❌ فشل في جلب النتائج: {e}")
                    return False
            
            print(f"   ❌ انتهت مهلة الانتظار ({max_wait}s)")
            return False
            
        except Exception as e:
            print(f"❌ فشل في سير عمل رفع الملفات: {e}")
            return False
    
    def test_cors_configuration(self):
        """اختبار إعدادات CORS"""
        print("🔍 اختبار إعدادات CORS...")
        try:
            # اختبار طلب OPTIONS (preflight)
            response = requests.options(f"{self.backend_url}/api/v1/upload/session")
            
            # التحقق من وجود headers CORS
            cors_headers = response.headers.get('Access-Control-Allow-Origin')
            if cors_headers:
                print(f"✅ إعدادات CORS صحيحة")
                print(f"   Access-Control-Allow-Origin: {cors_headers}")
                return True
            else:
                print(f"⚠️  إعدادات CORS غير واضحة")
                return False
                
        except Exception as e:
            print(f"❌ فشل في اختبار CORS: {e}")
            return False
    
    def run_comprehensive_test(self):
        """تشغيل اختبار شامل"""
        print("🚀 بدء الاختبار الشامل للتكامل بين الفرنت إند والباك إند")
        print("=" * 60)
        
        tests = [
            ("صحة الباك إند", self.test_backend_health),
            ("توفر الفرنت إند", self.test_frontend_availability),
            ("نقاط نهاية API", self.test_backend_api_endpoints),
            ("إعدادات CORS", self.test_cors_configuration),
            ("سير عمل رفع الملفات", self.test_file_upload_workflow),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 40)
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ فشل في تشغيل الاختبار: {e}")
                results[test_name] = False
        
        # ملخص النتائج
        print("\n" + "=" * 60)
        print("📊 ملخص النتائج")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ نجح" if result else "❌ فشل"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 النتيجة الإجمالية: {passed}/{total} اختبارات نجحت")
        
        if passed == total:
            print("🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام")
            print(f"\n🌐 روابط النظام:")
            print(f"   الفرنت إند: {self.frontend_url}")
            print(f"   الباك إند: {self.backend_url}")
            print(f"   وثائق API: {self.backend_url}/docs")
        else:
            print("⚠️  بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه")
        
        return passed == total

if __name__ == "__main__":
    tester = FrontendBackendIntegrationTest()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1) 