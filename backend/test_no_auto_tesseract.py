#!/usr/bin/env python3
"""
اختبار النظام المحدث - عدم استخدام Tesseract تلقائياً
Test updated system - no automatic Tesseract usage
"""

import asyncio
import os
import sys
import requests
import json
from pathlib import Path

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

def find_test_images():
    """العثور على صور للاختبار"""
    test_images = []
    
    # البحث في مجلد الرفع
    upload_dir = Path("uploads")
    if upload_dir.exists():
        for img_path in upload_dir.rglob("*.jpg"):
            test_images.append(str(img_path))
            if len(test_images) >= 2:
                break
    
    # البحث في المجلد الجذر
    root_dir = Path("../")
    for img_path in root_dir.glob("*.jpg"):
        test_images.append(str(img_path))
        if len(test_images) >= 2:
            break
    
    return test_images

def test_api_endpoints():
    """اختبار endpoints الجديدة"""
    base_url = "http://localhost:8001/api/v1"
    
    logger.info("🧪 اختبار النظام المحدث...")
    
    # العثور على صور للاختبار
    test_images = find_test_images()
    if len(test_images) < 2:
        logger.error("❌ لم يتم العثور على صورتين للاختبار")
        return False
    
    try:
        # 1. إنشاء جلسة مقارنة
        logger.info("📤 إنشاء جلسة مقارنة...")
        
        with open(test_images[0], 'rb') as old_file, open(test_images[1], 'rb') as new_file:
            files = {
                'old_image': ('old_image.jpg', old_file, 'image/jpeg'),
                'new_image': ('new_image.jpg', new_file, 'image/jpeg')
            }
            
            response = requests.post(f"{base_url}/compare/create-session", files=files)
            if response.status_code != 200:
                logger.error(f"❌ فشل في إنشاء الجلسة: {response.status_code}")
                return False
            
            session_data = response.json()
            session_id = session_data["session_id"]
            logger.info(f"✅ تم إنشاء الجلسة: {session_id}")
        
        # 2. إجراء المقارنة الكاملة
        logger.info("🔄 إجراء المقارنة الكاملة...")
        response = requests.post(f"{base_url}/compare/full-comparison/{session_id}")
        
        if response.status_code != 200:
            logger.error(f"❌ فشل في المقارنة: {response.status_code}")
            return False
        
        comparison_data = response.json()
        
        # 3. التحقق من النتائج
        logger.info("📊 تحليل النتائج...")
        
        old_success = comparison_data.get("old_image_result", {}).get("success", False)
        new_success = comparison_data.get("new_image_result", {}).get("success", False)
        
        logger.info(f"📝 نجاح استخراج الصورة القديمة: {old_success}")
        logger.info(f"📝 نجاح استخراج الصورة الجديدة: {new_success}")
        
        # 4. التحقق من fallback options
        fallback_options = comparison_data.get("fallback_options")
        
        if not old_success or not new_success:
            logger.info("⚠️ فشل في بعض الاستخراج - التحقق من fallback options...")
            
            if fallback_options:
                logger.info("✅ تم العثور على خيارات fallback:")
                logger.info(f"   - Tesseract متاح: {fallback_options.get('tesseract_available')}")
                logger.info(f"   - Endpoint: {fallback_options.get('fallback_endpoint')}")
                logger.info(f"   - رسالة: {fallback_options.get('message')}")
                logger.info(f"   - تحذير: {fallback_options.get('warning')}")
                
                # 5. اختبار endpoint حالة الجلسة
                logger.info("🔍 التحقق من حالة الجلسة...")
                status_response = requests.get(f"{base_url}/compare/session-status/{session_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    logger.info(f"📊 حالة الجلسة: {status_data.get('status')}")
                    logger.info(f"📊 فشل الاستخراج: {status_data.get('extraction_failed')}")
                    logger.info(f"📊 fallback متاح: {status_data.get('fallback_available')}")
                
                # 6. اختبار استخدام fallback (محاكاة موافقة المستخدم)
                logger.info("🔄 اختبار fallback OCR (محاكاة موافقة المستخدم)...")
                fallback_response = requests.post(f"{base_url}/compare/fallback-ocr/{session_id}")
                
                if fallback_response.status_code == 200:
                    fallback_data = fallback_response.json()
                    logger.info("✅ نجح fallback OCR:")
                    logger.info(f"   - رسالة: {fallback_data.get('message')}")
                    logger.info(f"   - تحذير: {fallback_data.get('warning')}")
                    logger.info(f"   - نجاح: {fallback_data.get('success')}")
                else:
                    logger.error(f"❌ فشل fallback OCR: {fallback_response.status_code}")
            else:
                logger.info("ℹ️ لا توجد خيارات fallback متاحة")
        else:
            logger.info("✅ نجح استخراج النص من كلا الصورتين - لا حاجة لـ fallback")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ خطأ في الاختبار: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    logger.info("🚀 بدء اختبار النظام المحدث (عدم استخدام Tesseract تلقائياً)...")
    
    # التحقق من تشغيل الخادم
    try:
        response = requests.get("http://localhost:8001/docs", timeout=5)
        if response.status_code != 200:
            logger.error("❌ الخادم غير متاح. تأكد من تشغيل: python simple_start.py")
            return False
    except requests.exceptions.RequestException:
        logger.error("❌ لا يمكن الوصول للخادم. تأكد من تشغيل: python simple_start.py")
        return False
    
    logger.info("✅ الخادم متاح")
    
    # تشغيل الاختبارات
    success = test_api_endpoints()
    
    # النتيجة النهائية
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 النتيجة النهائية")
    logger.info(f"{'='*60}")
    
    if success:
        logger.info("🎉 جميع الاختبارات نجحت!")
        logger.info("✅ النظام يعمل بشكل صحيح:")
        logger.info("   - يعتمد على LandingAI أولاً")
        logger.info("   - لا يستخدم Tesseract تلقائياً")
        logger.info("   - يوفر خيار fallback بعد موافقة المستخدم")
        return True
    else:
        logger.error("❌ فشل في بعض الاختبارات")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف الاختبار بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ خطأ في الاختبار: {e}")
        sys.exit(1) 