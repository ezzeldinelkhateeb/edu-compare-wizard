#!/usr/bin/env python3
"""
مشغل اختبار التشابه البصري
Visual Similarity Test Runner
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """تثبيت المتطلبات اللازمة"""
    requirements = [
        'opencv-python',
        'scikit-image', 
        'pillow',
        'imagehash',
        'matplotlib',
        'numpy'
    ]
    
    for req in requirements:
        try:
            __import__(req.replace('-', '_'))
            print(f"✅ {req} موجود")
        except ImportError:
            print(f"📦 تثبيت {req}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])

def run_test():
    """تشغيل اختبار التشابه البصري"""
    print("🔧 التحقق من المتطلبات...")
    install_requirements()
    
    print("\n🚀 تشغيل اختبار التشابه البصري...")
    
    # تشغيل الاختبار
    test_script = Path(__file__).parent / "visual_similarity_test.py"
    subprocess.run([sys.executable, str(test_script)])

if __name__ == "__main__":
    run_test() 