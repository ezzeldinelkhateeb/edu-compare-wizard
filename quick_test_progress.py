#!/usr/bin/env python3
"""
اختبار سريع لتحديثات التقدم في المعالجة المجمعة
Quick test for batch processing progress updates
"""

import requests
import json
import time

def test_progress_fix():
    """اختبار سريع لإصلاح التقدم"""
    try:
        print("🔬 اختبار سريع لإصلاح التقدم...")
        
        # 1. إنشاء جلسة
        url = "http://localhost:8001/api/v1/advanced-processing/create-session"
        data = {"session_name": "quick_progress_test", "processing_type": "batch_comparison"}
        
        print("📝 إنشاء جلسة...")
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            session_id = result["session_id"]
            print(f"✅ نجح إنشاء الجلسة: {session_id}")
            
            # 2. اختبار الحالة عدة مرات
            status_url = f"http://localhost:8001/api/v1/advanced-processing/{session_id}/status"
            
            print("📊 اختبار تحديثات التقدم...")
            for i in range(3):
                time.sleep(1)
                status_response = requests.get(status_url, timeout=10)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    progress = status_data.get('progress', 0)
                    status = status_data.get('status', 'unknown')
                    
                    print(f"   📈 اختبار {i+1}: التقدم = {progress:.1f}% | الحالة = {status}")
                    
                    if progress > 0:
                        print("   ✅ التقدم يعمل!")
                        break
                else:
                    print(f"   ❌ خطأ في الحالة: {status_response.status_code}")
            
            if progress > 0:
                print("\n🎉 نجح الإصلاح! التقدم يظهر بشكل صحيح")
                return True
            else:
                print("\n❌ فشل الإصلاح! التقدم لا يزال عند 0%")
                return False
                
        else:
            print(f"❌ فشل في إنشاء الجلسة: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        return False

if __name__ == "__main__":
    success = test_progress_fix()
    if success:
        print("\n✅ جميع الاختبارات نجحت! المشكلة تم حلها.")
    else:
        print("\n❌ بعض الاختبارات فشلت. يرجى مراجعة الخادم.") 