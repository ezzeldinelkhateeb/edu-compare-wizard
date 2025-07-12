#!/usr/bin/env python3
"""
سكريبت للتحقق من حالة الخادم
"""

import requests
import time
import sys

def check_server():
    print("🔍 التحقق من حالة الخادم...")
    
    # انتظار قليل للخادم ليبدأ
    time.sleep(3)
    
    try:
        response = requests.get('http://localhost:8001/health', timeout=10)
        print(f"✅ الخادم يعمل! - كود الاستجابة: {response.status_code}")
        print(f"📊 الاستجابة: {response.text[:200]}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ الخادم غير متاح على localhost:8001")
        return False
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return False

if __name__ == "__main__":
    success = check_server()
    sys.exit(0 if success else 1) 