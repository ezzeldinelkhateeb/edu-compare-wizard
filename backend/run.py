#!/usr/bin/env python3
"""
سكريبت تشغيل سريع لنظام مقارن المناهج التعليمية
Quick start script for Educational Content Comparison System
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
        print("💡 تشغيل Redis باستخدام: docker run -d -p 6379:6379 redis:7-alpine")
        return False

def install_dependencies():
    """تثبيت التبعيات"""
    print("📦 تثبيت التبعيات...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ تم تثبيت التبعيات")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل في تثبيت التبعيات: {e}")
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
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]
    return subprocess.Popen(cmd)

def start_celery_worker():
    """تشغيل Celery Worker"""
    print("👷 تشغيل Celery Worker...")
    cmd = [
        sys.executable, "-m", "celery", 
        "-A", "celery_app.worker", 
        "worker", 
        "--loglevel=info",
        "--concurrency=2"
    ]
    return subprocess.Popen(cmd)

def start_celery_flower():
    """تشغيل Celery Flower"""
    print("🌸 تشغيل Celery Flower...")
    cmd = [
        sys.executable, "-m", "celery", 
        "-A", "celery_app.worker", 
        "flower", 
        "--port=5555"
    ]
    return subprocess.Popen(cmd)

def main():
    """الدالة الرئيسية"""
    print("🎓 بدء تشغيل نظام مقارن المناهج التعليمية")
    print("=" * 50)
    
    # فحص Redis
    if not check_redis():
        return False
    
    # إنشاء المجلدات
    create_directories()
    
    # تثبيت التبعيات
    if not install_dependencies():
        return False
    
    print("\n🚀 بدء تشغيل الخدمات...")
    print("=" * 50)
    
    processes = []
    
    try:
        # تشغيل FastAPI
        fastapi_process = start_fastapi()
        processes.append(("FastAPI", fastapi_process))
        time.sleep(3)  # انتظار تشغيل FastAPI
        
        # تشغيل Celery Worker
        celery_process = start_celery_worker()
        processes.append(("Celery Worker", celery_process))
        time.sleep(2)
        
        # تشغيل Celery Flower
        flower_process = start_celery_flower()
        processes.append(("Celery Flower", flower_process))
        
        print("\n✅ تم تشغيل جميع الخدمات!")
        print("=" * 50)
        print("🌐 FastAPI: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("🌸 Celery Flower: http://localhost:5555")
        print("❤️  Health Check: http://localhost:8000/health")
        print("=" * 50)
        print("اضغط Ctrl+C للإيقاف")
        
        # انتظار إيقاف المستخدم
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 إيقاف الخدمات...")
        for name, process in processes:
            print(f"⏹️  إيقاف {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ تم إيقاف جميع الخدمات")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 