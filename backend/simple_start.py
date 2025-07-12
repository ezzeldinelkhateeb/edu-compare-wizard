#!/usr/bin/env python3
"""
سكريبت تشغيل مباشر للباك إند - بدون تثبيت تبعيات
Direct backend start script - without dependency installation
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_redis():
    """فحص اتصال Redis"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis متصل")
        return True
    except Exception as e:
        print(f"❌ Redis غير متصل: {e}")
        print("💡 تشغيل Redis باستخدام: redis-server.exe redis.windows.conf")
        return False

def create_directories():
    """إنشاء المجلدات المطلوبة"""
    directories = ["uploads", "logs", "uploads/old", "uploads/new", "uploads/temp", "uploads/results"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ تم إنشاء المجلدات")

def start_fastapi():
    """تشغيل FastAPI"""
    print("🚀 تشغيل FastAPI Server...")
    try:
        import uvicorn
        print("📡 بدء الخادم على http://localhost:8001")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=False)
    except ImportError as e:
        print(f"❌ خطأ في الاستيراد: {e}")
        print("💡 تحقق من تثبيت المكتبات المطلوبة")
        return False
    except Exception as e:
        print(f"❌ خطأ في تشغيل الخادم: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🎓 بدء تشغيل نظام مقارن المناهج التعليمية")
    print("=" * 50)
    
    # إنشاء المجلدات
    create_directories()
    
    # فحص Redis (اختياري)
    redis_connected = check_redis()
    if not redis_connected:
        print("⚠️  Redis غير متصل - بعض الميزات قد لا تعمل")
    
    print("\n🚀 بدء تشغيل FastAPI...")
    print("=" * 50)
    
    try:
        start_fastapi()
    except KeyboardInterrupt:
        print("\n🛑 إيقاف الخدمة...")
        print("✅ تم إيقاف الخدمة")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 