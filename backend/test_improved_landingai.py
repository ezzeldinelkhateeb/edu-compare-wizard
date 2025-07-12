#!/usr/bin/env python3
"""
اختبار النظام المحسن لـ LandingAI مع آلية fallback
Test improved LandingAI system with fallback mechanism
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.landing_ai_service import LandingAIService
from loguru import logger

def test_image_paths():
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

async def test_improved_extraction():
    """اختبار الاستخراج المحسن"""
    logger.info("🧪 بدء اختبار النظام المحسن لـ LandingAI...")
    
    # إنشاء خدمة LandingAI
    service = LandingAIService()
    
    # العثور على صور للاختبار
    test_images = test_image_paths()
    
    if not test_images:
        logger.error("❌ لم يتم العثور على صور للاختبار")
        return False
    
    logger.info(f"🖼️ تم العثور على {len(test_images)} صورة للاختبار")
    
    success_count = 0
    total_tests = 0
    
    for i, image_path in enumerate(test_images[:2]):  # اختبار أول صورتين فقط
        total_tests += 1
        logger.info(f"\n{'='*50}")
        logger.info(f"🔍 اختبار الصورة {i+1}: {Path(image_path).name}")
        logger.info(f"{'='*50}")
        
        try:
            start_time = time.time()
            
            # اختبار الاستخراج
            result = await service.extract_from_file(image_path)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if result.success:
                logger.info(f"✅ نجح الاستخراج في {processing_time:.2f} ثانية")
                logger.info(f"📊 النتائج:")
                logger.info(f"   - النص: {len(result.markdown_content)} حرف")
                logger.info(f"   - الثقة: {result.confidence_score:.2f}")
                logger.info(f"   - الأجزاء: {result.total_chunks}")
                logger.info(f"   - وقت المعالجة: {result.processing_time:.2f}s")
                
                # عرض عينة من النص
                if result.markdown_content:
                    sample_text = result.markdown_content[:200] + "..." if len(result.markdown_content) > 200 else result.markdown_content
                    logger.info(f"📝 عينة من النص: {sample_text}")
                
                success_count += 1
                
            else:
                logger.error(f"❌ فشل الاستخراج: {result.error_message}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في اختبار الصورة {i+1}: {e}")
    
    # تقرير النتائج
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 تقرير النتائج النهائي")
    logger.info(f"{'='*50}")
    logger.info(f"✅ نجح: {success_count}/{total_tests}")
    logger.info(f"❌ فشل: {total_tests - success_count}/{total_tests}")
    logger.info(f"📈 نسبة النجاح: {(success_count/total_tests)*100:.1f}%")
    
    return success_count > 0

async def test_fallback_mechanism():
    """اختبار آلية fallback"""
    logger.info("\n🔄 اختبار آلية fallback...")
    
    service = LandingAIService()
    
    # محاولة محاكاة فشل LandingAI
    original_agentic_available = service.agentic_doc_available
    
    try:
        # تعطيل agentic_doc مؤقتاً لاختبار fallback
        service.agentic_doc_available = False
        
        test_images = test_image_paths()
        if not test_images:
            logger.warning("⚠️ لم يتم العثور على صور لاختبار fallback")
            return False
        
        image_path = test_images[0]
        logger.info(f"🔄 اختبار fallback مع الصورة: {Path(image_path).name}")
        
        result = await service.extract_from_file(image_path)
        
        if result.success:
            logger.info("✅ نجح fallback mechanism")
            logger.info(f"📊 النتائج: {len(result.markdown_content)} حرف")
            return True
        else:
            logger.error(f"❌ فشل fallback mechanism: {result.error_message}")
            return False
            
    finally:
        # استعادة الإعداد الأصلي
        service.agentic_doc_available = original_agentic_available

async def main():
    """الدالة الرئيسية للاختبار"""
    logger.info("🚀 بدء اختبار النظام المحسن...")
    
    # اختبار الاستخراج العادي
    extraction_success = await test_improved_extraction()
    
    # اختبار آلية fallback
    fallback_success = await test_fallback_mechanism()
    
    # النتيجة النهائية
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 النتيجة النهائية")
    logger.info(f"{'='*60}")
    
    if extraction_success and fallback_success:
        logger.info("🎉 جميع الاختبارات نجحت!")
        return True
    elif extraction_success:
        logger.info("✅ الاستخراج العادي نجح، لكن fallback فشل")
        return True
    else:
        logger.error("❌ فشل في جميع الاختبارات")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف الاختبار بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ خطأ في الاختبار: {e}")
        sys.exit(1) 