#!/usr/bin/env python3
"""
اختبار شامل لـ API نظام مقارنة المناهج التعليمية
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:8001"
API_BASE = "/api/v1"

# 1. إنشاء جلسة رفع
def test_create_upload_session():
    print("\n🆕 اختبار إنشاء جلسة رفع...")
    try:
        payload = {
            "session_name": "اختبار جلسة رفع",
            "description": "جلسة رفع لاختبار النظام"
        }
        response = requests.post(f"{BASE_URL}{API_BASE}/upload/session", json=payload, timeout=10)
        print(f"✅ Session Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Session Result: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data["session_id"]
        else:
            print(f"❌ Session Failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Session Test Failed: {e}")
        return None

# 2. رفع ملف إلى الجلسة

def test_upload_image(session_id, file_type="new"):
    print("\n📤 اختبار رفع الصورة...")
    try:
        image_path = "../103.jpg"
        if not os.path.exists(image_path):
            print(f"❌ الصورة غير موجودة: {image_path}")
            return None
        with open(image_path, "rb") as f:
            files = {"file": ("103.jpg", f, "image/jpeg")}
            data = {"session_id": session_id, "file_type": file_type}
            response = requests.post(f"{BASE_URL}{API_BASE}/upload/file", files=files, data=data, timeout=60)
        print(f"✅ Upload Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Upload Result: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data["file_id"]
        else:
            print(f"❌ Upload Failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Upload Test Failed: {e}")
        return None

# 3. بدء مقارنة (تجريبية)
def test_start_comparison(session_id, old_file_id, new_file_id):
    print("\n🔍 اختبار بدء المقارنة...")
    try:
        payload = {
            "session_id": session_id,
            "old_files": [old_file_id],
            "new_files": [new_file_id],
            "comparison_settings": {}
        }
        response = requests.post(f"{BASE_URL}{API_BASE}/compare/start", json=payload, timeout=60)
        print(f"✅ Compare Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Compare Result: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data["job_id"]
        else:
            print(f"❌ Compare Failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Compare Test Failed: {e}")
        return None

# 4. اختبار Health وDocs كما هي

def test_health():
    print("🔍 اختبار Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"📄 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_documentation():
    print("\n📚 اختبار التوثيق...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"✅ Swagger UI: {response.status_code}")
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        print(f"✅ OpenAPI JSON: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Documentation Test Failed: {e}")
        return False

def main():
    print("🚀 بدء الاختبار الشامل لـ API...")
    print("=" * 60)
    results = {}
    # Health
    results["health"] = test_health()
    # إنشاء جلسة رفع
    session_id = test_create_upload_session()
    results["session"] = session_id is not None
    # رفع ملف قديم وجديد (نفس الصورة للاختبار)
    old_file_id = test_upload_image(session_id, file_type="old")
    new_file_id = test_upload_image(session_id, file_type="new")
    results["upload_old"] = old_file_id is not None
    results["upload_new"] = new_file_id is not None
    # بدء مقارنة
    job_id = test_start_comparison(session_id, old_file_id, new_file_id)
    results["compare"] = job_id is not None
    # Docs
    results["documentation"] = test_documentation()
    print("\n" + "=" * 60)
    print("📊 نتائج الاختبار النهائية:")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"   {test_name.upper()}: {status}")
    success_count = sum(results.values())
    total_count = len(results)
    print(f"\n🎯 النتيجة الإجمالية: {success_count}/{total_count} اختبارات نجحت")
    if success_count == total_count:
        print("🎉 جميع الاختبارات نجحت! النظام يعمل بشكل مثالي!")
    else:
        print("⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")

if __name__ == "__main__":
    main() 