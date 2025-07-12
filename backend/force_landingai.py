#!/usr/bin/env python3
"""
خدمة محسنة لإجبار استخدام LandingAI فقط مع تحسينات السرعة
Optimized service to force LandingAI usage only with speed improvements
"""

import os
import sys
import asyncio
from pathlib import Path

# إضافة مسار المشروع
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

# تعيين متغيرات البيئة قبل الاستيراد
os.environ["GEMINI_API_KEY"] = "AIzaSyCDO-0puQQN79BJ4u503O31g16ww8CAycg"
os.environ["VISION_AGENT_API_KEY"] = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"

# إعدادات LandingAI محسنة للسرعة
os.environ["LANDINGAI_BATCH_SIZE"] = "4"
os.environ["LANDINGAI_MAX_WORKERS"] = "6" 
os.environ["LANDINGAI_MAX_RETRIES"] = "1"  # تقليل المحاولات
os.environ["LANDINGAI_INCLUDE_MARGINALIA"] = "false"  # تسريع المعالجة
os.environ["LANDINGAI_INCLUDE_METADATA"] = "true"
os.environ["LANDINGAI_SAVE_VISUAL_GROUNDINGS"] = "false"  # توفير مساحة ووقت

from loguru import logger
import tempfile


class FastLandingAIService:
    """خدمة LandingAI محسنة للسرعة فقط"""
    
    def __init__(self):
        from app.services.landing_ai_service import LandingAIService
        self.service = LandingAIService()
        
        # إجبار استخدام LandingAI فقط
        self.service.ocr_available = False  # تعطيل Tesseract backup
        
        logger.info("🚀 تم تكوين FastLandingAI - LandingAI فقط، لا tesseract backup")
        logger.info(f"🔑 API Key configured: {'✅' if self.service.api_key else '❌'}")
    
    async def extract_text_fast(self, image_path: str) -> dict:
        """استخراج سريع باستخدام LandingAI فقط"""
        try:
            logger.info(f"⚡ بدء الاستخراج السريع من: {Path(image_path).name}")
            
            # استخدام مجلد مؤقت
            with tempfile.TemporaryDirectory() as temp_dir:
                result = await self.service._real_landingai_extraction(
                    image_path, 
                    temp_dir, 
                    Path(image_path).name
                )
                
                if result.success:
                    logger.info(f"✅ اكتمل في {result.processing_time:.1f}s - {len(result.markdown_content)} حرف")
                    return {
                        "success": True,
                        "text": result.markdown_content,
                        "confidence": result.confidence_score,
                        "processing_time": result.processing_time,
                        "service": "LandingAI_Fast"
                    }
                else:
                    raise Exception(result.error_message)
                    
        except Exception as e:
            logger.error(f"❌ فشل LandingAI: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "confidence": 0,
                "processing_time": 0,
                "service": "LandingAI_Error"
            }


async def test_fast_extraction():
    """اختبار الاستخراج السريع"""
    service = FastLandingAIService()
    
    # ملفات اختبار
    test_files = ["101.jpg", "103.jpg", "104.jpg"]
    
    for file_name in test_files:
        if Path(file_name).exists():
            logger.info(f"\n🔬 اختبار: {file_name}")
            
            start_time = asyncio.get_event_loop().time()
            result = await service.extract_text_fast(file_name)
            total_time = asyncio.get_event_loop().time() - start_time
            
            if result["success"]:
                logger.info(f"✅ نجح في {total_time:.1f}s")
                logger.info(f"📝 النص: {result['text'][:100]}...")
                logger.info(f"🎯 الثقة: {result['confidence']:.1%}")
            else:
                logger.error(f"❌ فشل: {result['error']}")
            
            break  # اختبار ملف واحد فقط
        else:
            logger.warning(f"⚠️ ملف غير موجود: {file_name}")


async def patch_landing_ai_service():
    """تطبيق patch لجعل LandingAI أسرع وأكثر اعتمادية"""
    try:
        from app.services import landing_ai_service
        
        # Monkey patch للخدمة
        original_extract = landing_ai_service.LandingAIService.extract_from_file
        
        async def fast_extract_from_file(self, file_path: str, output_dir=None, job_id=None):
            """نسخة سريعة من extract_from_file - LandingAI فقط"""
            
            # تجاهل Tesseract تماماً
            old_ocr_available = self.ocr_available
            self.ocr_available = False
            
            try:
                # إنشاء مجلد مؤقت
                if not output_dir:
                    output_dir = tempfile.mkdtemp()
                
                timestamp = Path(file_path).stem
                session_dir = Path(output_dir) / f"fast_extraction_{timestamp}"
                session_dir.mkdir(exist_ok=True)
                
                # محاولة LandingAI فقط
                result = await self._real_landingai_extraction(
                    file_path, 
                    str(session_dir), 
                    Path(file_path).name
                )
                
                logger.info(f"🚀 استخراج سريع مكتمل: {Path(file_path).name}")
                return result
                
            finally:
                # استعادة الإعداد الأصلي (اختياري)
                self.ocr_available = old_ocr_available
        
        # تطبيق الـ patch
        landing_ai_service.LandingAIService.extract_from_file = fast_extract_from_file
        
        logger.info("🔧 تم تطبيق Fast LandingAI patch بنجاح!")
        return True
        
    except Exception as e:
        logger.error(f"❌ فشل تطبيق patch: {e}")
        return False


if __name__ == "__main__":
    async def main():
        logger.info("🚀 بدء اختبار Fast LandingAI Service")
        
        # تطبيق patch
        patched = await patch_landing_ai_service()
        if patched:
            logger.info("✅ Patch applied successfully")
            
            # اختبار الخدمة
            await test_fast_extraction()
        else:
            logger.error("❌ فشل في تطبيق patch")
    
    asyncio.run(main()) 