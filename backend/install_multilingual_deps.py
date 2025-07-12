#!/usr/bin/env python3
"""
سكريبت تثبيت المكتبات المطلوبة للمزايا متعددة اللغات
Installation script for multilingual features dependencies
"""

import subprocess
import sys
import os

def run_command(command):
    """تشغيل أمر وإرجاع النتيجة"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_package(package):
    """تثبيت مكتبة واحدة"""
    print(f"📦 تثبيت {package}...")
    success, output = run_command(f"pip install {package}")
    if success:
        print(f"✅ تم تثبيت {package} بنجاح")
        return True
    else:
        print(f"❌ فشل في تثبيت {package}: {output}")
        return False

def main():
    """وظيفة التثبيت الرئيسية"""
    print("🚀 بدء تثبيت المكتبات المطلوبة للمزايا متعددة اللغات")
    print("=" * 60)
    
    # قائمة المكتبات المطلوبة
    packages = [
        "langdetect==1.0.9",
        "textblob==0.17.1", 
        "aiofiles==23.2.1",
        "pathlib2==2.3.7",
        "unicodedata2==15.1.0"
    ]
    
    # تثبيت المكتبات الأساسية أولاً
    basic_packages = [
        "sqlalchemy==2.0.23",
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "pydantic==2.5.0",
        "redis==5.0.1"
    ]
    
    print("📦 تثبيت المكتبات الأساسية...")
    for package in basic_packages:
        if not install_package(package):
            print(f"⚠️ فشل في تثبيت المكتبة الأساسية: {package}")
    
    print("\n📦 تثبيت مكتبات المزايا الجديدة...")
    success_count = 0
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 النتائج: تم تثبيت {success_count}/{len(packages)} مكتبة بنجاح")
    
    # محاولة تثبيت textblob corpora
    print("\n📚 تنزيل البيانات اللغوية لـ TextBlob...")
    try:
        import textblob
        print("✅ تم تثبيت TextBlob، جاري تنزيل البيانات...")
        run_command("python -m textblob.download_corpora")
        print("✅ تم تنزيل البيانات اللغوية")
    except ImportError:
        print("⚠️ TextBlob غير مثبت، تخطي تنزيل البيانات")
    
    if success_count == len(packages):
        print("\n🎉 تم تثبيت جميع المكتبات بنجاح!")
        print("يمكنك الآن تشغيل النظام باستخدام:")
        print("python simple_start.py")
    else:
        print(f"\n⚠️ فشل في تثبيت {len(packages) - success_count} مكتبة")
        print("تحقق من رسائل الخطأ أعلاه وجرب التثبيت اليدوي")

if __name__ == "__main__":
    main() 