#!/usr/bin/env python3
"""
Script لتشغيل Celery worker
"""

import os
import sys
import subprocess
from pathlib import Path

def start_celery_worker():
    """تشغيل Celery worker مع 6 workers"""
    try:
        # التأكد من أننا في مجلد backend
        backend_path = Path(__file__).parent
        os.chdir(backend_path)
        
        # تشغيل celery worker
        cmd = [
            sys.executable, "-m", "celery", 
            "-A", "celery_app.worker", 
            "worker", 
            "--loglevel=info", 
            "--concurrency=6"
        ]
        
        print("🚀 بدء تشغيل Celery worker مع 6 workers...")
        print(f"📂 المجلد الحالي: {os.getcwd()}")
        print(f"💻 الأمر: {' '.join(cmd)}")
        
        # تشغيل الأمر
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تشغيل Celery: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف Celery worker")
        sys.exit(0)
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_worker() 