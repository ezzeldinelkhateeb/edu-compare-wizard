#!/usr/bin/env python3
"""
إصلاح LandingAI API مع إعدادات صحيحة
Fix LandingAI API with correct settings
"""

import os
import sys
import asyncio
import aiohttp
import aiofiles
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

# إضافة مسار المشروع
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

# تعيين متغيرات البيئة
os.environ["VISION_AGENT_API_KEY"] = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"

class FixedLandingAIService:
    """خدمة LandingAI محسنة مع API صحيح"""
    
    def __init__(self):
        self.api_key = os.environ.get("VISION_AGENT_API_KEY")
        
        # استخدام API endpoint الصحيح لـ document extraction
        # يبدو أن النظام يستخدم agentic_doc library
        self.use_agentic_doc = True
        
        if not self.api_key:
            raise Exception("VISION_AGENT_API_KEY not set")
            
        logger.info("🔧 تم تكوين Fixed LandingAI Service")
        logger.info(f"🔑 API Key: {self.api_key[:10]}...{self.api_key[-5:]}")
    
    async def extract_with_agentic_doc(self, image_path: str) -> dict:
        """استخراج باستخدام agentic_doc library المباشرة"""
        try:
            # استيراد agentic_doc
            from agentic_doc.vision_agent import VisionAgent
            
            # إنشاء VisionAgent
            agent = VisionAgent(api_key=self.api_key)
            
            logger.info(f"🤖 بدء الاستخراج باستخدام agentic_doc: {Path(image_path).name}")
            
            # استخراج المحتوى
            result = await agent.extract_document(
                file_path=image_path,
                include_marginalia=False,  # أسرع
                include_metadata_in_markdown=True
            )
            
            # تحويل النتيجة
            return {
                "success": True,
                "markdown": result.get("data", {}).get("markdown", ""),
                "chunks": result.get("data", {}).get("chunks", []),
                "processing_time": 0,  # سيتم حسابه لاحقاً
                "service": "agentic_doc",
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"❌ فشل agentic_doc: {e}")
            return {
                "success": False,
                "error": str(e),
                "service": "agentic_doc_error"
            }
    
    async def extract_with_direct_api(self, image_path: str) -> dict:
        """استخراج باستخدام API مباشر"""
        try:
            # استخدام API endpoint الصحيح
            api_url = "https://api.landing.ai/v1/vision/predict"
            
            headers = {
                'apikey': self.api_key,
                'Content-Type': 'multipart/form-data'
            }
            
            # قراءة الملف
            async with aiofiles.open(image_path, 'rb') as f:
                file_content = await f.read()
            
            # إعداد form data
            data = aiohttp.FormData()
            data.add_field('file', file_content, 
                          filename=Path(image_path).name,
                          content_type='image/jpeg')
            
            logger.info(f"🌐 إرسال طلب إلى: {api_url}")
            
            # إرسال الطلب
            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(api_url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ نجح الطلب المباشر")
                        
                        return {
                            "success": True,
                            "result": result,
                            "service": "direct_api",
                            "confidence": 0.85
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"API Error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ فشل Direct API: {e}")
            return {
                "success": False,
                "error": str(e),
                "service": "direct_api_error"
            }
    
    async def extract_fast(self, image_path: str) -> dict:
        """استخراج سريع مع تجربة طرق متعددة"""
        start_time = datetime.now()
        
        logger.info(f"⚡ بدء استخراج سريع: {Path(image_path).name}")
        
        # تجربة agentic_doc أولاً
        result = await self.extract_with_agentic_doc(image_path)
        
        if not result["success"]:
            logger.warning("⚠️ فشل agentic_doc، محاولة Direct API...")
            result = await self.extract_with_direct_api(image_path)
        
        # حساب الوقت
        processing_time = (datetime.now() - start_time).total_seconds()
        result["processing_time"] = processing_time
        
        if result["success"]:
            logger.info(f"✅ اكتمل في {processing_time:.1f}s")
        else:
            logger.error(f"❌ فشل في {processing_time:.1f}s: {result.get('error', 'Unknown error')}")
        
        return result


async def test_fixed_service():
    """اختبار الخدمة المحسنة"""
    try:
        service = FixedLandingAIService()
        
        # ملفات اختبار
        test_files = ["101.jpg", "103.jpg", "104.jpg"]
        
        for file_name in test_files:
            if Path(file_name).exists():
                logger.info(f"\n🧪 اختبار: {file_name}")
                
                result = await service.extract_fast(file_name)
                
                if result["success"]:
                    logger.info(f"✅ نجح الاستخراج!")
                    logger.info(f"🔧 الخدمة: {result['service']}")
                    logger.info(f"⏱️ الوقت: {result['processing_time']:.1f}s")
                    
                    if "markdown" in result:
                        logger.info(f"📝 النص: {result['markdown'][:100]}...")
                    elif "result" in result:
                        logger.info(f"📊 النتيجة: {str(result['result'])[:100]}...")
                        
                else:
                    logger.error(f"❌ فشل: {result['error']}")
                
                break  # اختبار ملف واحد فقط
        
    except Exception as e:
        logger.error(f"❌ خطأ في الاختبار: {e}")


if __name__ == "__main__":
    asyncio.run(test_fixed_service()) 