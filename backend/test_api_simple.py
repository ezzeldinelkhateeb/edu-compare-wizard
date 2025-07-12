#!/usr/bin/env python3
"""
اختبار بسيط لـ API
Simple API Test
"""

import requests
import json
import time

def test_api():
    base_url = "http://localhost:8000"
    
    print("🔍 اختبار صحة الخادم...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        print(f"📄 Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    print("\n🔍 اختبار إنشاء جلسة رفع...")
    try:
        payload = {
            "session_name": "test_session",
            "description": "Test session for debugging"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/upload/session",
            json=payload,
            timeout=10
        )
        
        print(f"✅ Session creation: {response.status_code}")
        if response.status_code == 200:
            session_data = response.json()
            print(f"📄 Session created: {session_data}")
            return session_data.get('session_id')
        else:
            print(f"❌ Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
    
    return None

if __name__ == "__main__":
    print("🚀 بدء اختبار API...")
    session_id = test_api()
    if session_id:
        print(f"🎉 تم إنشاء الجلسة بنجاح: {session_id}")
    else:
        print("💥 فشل في اختبار API") 