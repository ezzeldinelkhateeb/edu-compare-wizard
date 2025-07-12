#!/usr/bin/env python3
"""
اختبار مباشر لـ LandingAI API بدون استخدام Tesseract
Direct LandingAI API Test - No Tesseract Fallback
"""

import asyncio
import aiohttp
import aiofiles
import json
import os
from datetime import datetime
import sys
import logging

# Add the parent directory to the path so we can import from config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.services.landing_ai_service import LandingAIService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the API key is set in environment variables
VISION_AGENT_API_KEY = os.environ.get("VISION_AGENT_API_KEY", "")
# Temporarily bypass API key check for testing
# if not VISION_AGENT_API_KEY:
#     logger.warning("VISION_AGENT_API_KEY not set. Please set it before running the test.")
#     exit(1)

def test_landingai_extraction():
    """Test direct extraction using LandingAI API with agentic-doc library."""
    logger.info("Starting LandingAI direct API test")
    
    # Initialize the service
    service = LandingAIService()
    if not service.is_enabled():
        logger.error("LandingAI service is not enabled. Check API key and agentic-doc installation.")
        return
    
    # Test files provided by the user
    test_files = [
        r"D:\ezz\compair\edu-compare-wizard\backend\103.jpg",
        r"C:\Users\ezz\Downloads\elkheta-content-compare-pro-main\elkheta-content-compare-pro-main\مقدمة تمهيدية.pdf"
    ]
    
    # Create a temporary directory for results
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_landingai_direct_output")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory created at: {output_dir}")
    
    # Process each file
    for file_path in test_files:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            continue
        
        logger.info(f"Processing file: {file_path}")
        result = service.extract_text_from_image(file_path, output_dir)
        
        if "error" in result:
            logger.error(f"Failed to process {file_path}: {result['error']}")
        else:
            logger.info(f"Successfully processed {file_path}")
            # Save the result to a JSON file
            output_file = os.path.join(output_dir, f"result_{os.path.basename(file_path).replace('.', '_')}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to: {output_file}")
    
    logger.info("LandingAI direct API test completed")

async def test_landingai_direct():
    """اختبار LandingAI API مباشرة"""
    
    print("="*60)
    print("🧪 اختبار LandingAI API مباشر")
    print("="*60)
    
    # المعلومات الأساسية
    api_key = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"
    api_endpoint = "https://api.va.landing.ai/v1/tools/agentic-document-analysis"
    test_image = "103.jpg"
    
    print(f"🔑 API Key: {api_key[:30]}...")
    print(f"🌐 Endpoint: {api_endpoint}")
    print(f"📁 Test Image: {test_image}")
    
    # التحقق من وجود الملف
    if not os.path.exists(test_image):
        print(f"❌ لا يوجد ملف الاختبار: {test_image}")
        return False
    
    file_size = os.path.getsize(test_image) / 1024  # KB
    print(f"📏 حجم الملف: {file_size:.1f} KB")
    
    try:
        print("\n🚀 بدء عملية الاستخراج...")
        start_time = datetime.now()
        
        # إعداد headers
        headers = {
            'Authorization': f'Basic {api_key}'
        }
        
        # إعداد البيانات
        data = aiohttp.FormData()
        data.add_field('include_marginalia', 'true')
        data.add_field('include_metadata_in_markdown', 'true')
        
        # قراءة وإضافة الملف
        async with aiofiles.open(test_image, 'rb') as f:
            file_content = await f.read()
            data.add_field('file', file_content, filename=test_image, content_type='application/octet-stream')
        
        print(f"📤 إرسال الطلب إلى LandingAI...")
        
        # إرسال الطلب
        timeout = aiohttp.ClientTimeout(total=600)  # 10 دقائق
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_endpoint, headers=headers, data=data) as response:
                print(f"📡 استجابة الخادم: {response.status}")
                
                if response.status == 200:
                    result_data = await response.json()
                    end_time = datetime.now()
                    processing_time = (end_time - start_time).total_seconds()
                    
                    print("✅ نجح الاستخراج!")
                    print(f"⏱️  وقت المعالجة: {processing_time:.2f} ثانية")
                    
                    # استخراج البيانات
                    data_section = result_data.get('data', {})
                    markdown_content = data_section.get('markdown', '')
                    chunks = data_section.get('chunks', [])
                    extracted_schema = data_section.get('extracted_schema', {})
                    
                    print(f"📄 طول المحتوى: {len(markdown_content)} حرف")
                    print(f"🔢 عدد القطع: {len(chunks)}")
                    
                    # إحصائيات القطع
                    chunk_types = {}
                    for chunk in chunks:
                        chunk_type = chunk.get('chunk_type', 'unknown')
                        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                    
                    print(f"\n📊 توزيع القطع:")
                    for chunk_type, count in chunk_types.items():
                        print(f"  • {chunk_type}: {count}")
                    
                    # عرض عينة من المحتوى
                    if markdown_content:
                        print(f"\n📝 عينة من المحتوى المستخرج:")
                        print("─" * 50)
                        preview = markdown_content[:300] + "..." if len(markdown_content) > 300 else markdown_content
                        print(preview)
                        print("─" * 50)
                    
                    # حفظ النتائج
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    results_dir = f"landingai_test_{timestamp}"
                    os.makedirs(results_dir, exist_ok=True)
                    
                    # حفظ JSON الكامل
                    json_file = os.path.join(results_dir, "full_result.json")
                    async with aiofiles.open(json_file, 'w', encoding='utf-8') as f:
                        await f.write(json.dumps(result_data, ensure_ascii=False, indent=2))
                    
                    # حفظ Markdown
                    if markdown_content:
                        md_file = os.path.join(results_dir, "extracted_content.md")
                        async with aiofiles.open(md_file, 'w', encoding='utf-8') as f:
                            await f.write(markdown_content)
                    
                    print(f"\n💾 النتائج محفوظة في: {results_dir}")
                    print(f"  • JSON: {json_file}")
                    if markdown_content:
                        print(f"  • Markdown: {md_file}")
                    
                    print("\n" + "="*60)
                    print("🎉 نجح اختبار LandingAI API!")
                    print("="*60)
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ خطأ من LandingAI: {response.status}")
                    print(f"📝 تفاصيل الخطأ: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_gemini_direct():
    """اختبار Gemini API مباشر"""
    
    print("="*60)
    print("🧪 اختبار Gemini API مباشر") 
    print("="*60)
    
    import google.generativeai as genai
    
    api_key = "AIzaSyCDO-0puQQN79BJ4u503O31g16ww8CAycg"
    model_name = "gemini-1.5-flash"  # نموذج أسرع مع حدود أكبر
    
    print(f"🔑 API Key: {api_key[:30]}...")
    print(f"🤖 Model: {model_name}")
    
    try:
        # تكوين Gemini
        genai.configure(api_key=api_key)
        
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )
        
        print("✅ تم تكوين Gemini بنجاح")
        
        # اختبار بسيط أولاً
        print("\n🧪 اختبار اتصال بسيط...")
        simple_prompt = "قل مرحباً بالعربية"
        
        start_time = datetime.now()
        response = await asyncio.to_thread(model.generate_content, simple_prompt)
        end_time = datetime.now()
        
        if response.text:
            print(f"✅ نجح الاختبار البسيط!")
            print(f"⏱️  وقت الاستجابة: {(end_time - start_time).total_seconds():.2f} ثانية")
            print(f"📝 الاستجابة: {response.text}")
            
            # اختبار مقارنة النصوص
            print("\n🔍 اختبار مقارنة النصوص...")
            
            comparison_prompt = """
قارن بين النصين التاليين واكتب تحليلاً مختصراً:

النص الأول:
الوحدة الأولى: الفيزياء
- مفهوم القوة
- قانون نيوتن الأول

النص الثاني:  
الوحدة الأولى: الفيزياء التطبيقية
- مفهوم القوة والكتلة
- قانون نيوتن الأول والثاني
- تطبيقات عملية

اكتب ملخصاً قصيراً للاختلافات.
"""
            
            start_time = datetime.now()
            comparison_response = await asyncio.to_thread(model.generate_content, comparison_prompt)
            end_time = datetime.now()
            
            if comparison_response.text:
                print(f"✅ نجحت مقارنة النصوص!")
                print(f"⏱️  وقت المقارنة: {(end_time - start_time).total_seconds():.2f} ثانية")
                print(f"📊 طول الاستجابة: {len(comparison_response.text)} حرف")
                
                print(f"\n📝 نتيجة المقارنة:")
                print("─" * 50)
                print(comparison_response.text)
                print("─" * 50)
                
                print("\n" + "="*60)
                print("🎉 نجح اختبار Gemini API!")
                print("="*60)
                
                return True
            else:
                print("❌ لم يتم الحصول على استجابة للمقارنة")
                return False
        else:
            print("❌ لم يتم الحصول على استجابة للاختبار البسيط")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في Gemini: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """تشغيل جميع الاختبارات المباشرة"""
    
    print("🎯 اختبار APIs مباشرة - بدون Tesseract")
    print("🔧 LandingAI + Gemini فقط")
    
    results = []
    
    # اختبار LandingAI مباشر
    print("\n" + "🔷" * 20 + " LANDINGAI " + "🔷" * 20)
    landingai_success = await test_landingai_direct()
    results.append(("LandingAI API", landingai_success))
    
    await asyncio.sleep(3)  # استراحة
    
    # اختبار Gemini مباشر
    print("\n" + "🔶" * 20 + " GEMINI " + "🔶" * 20)
    gemini_success = await test_gemini_direct()
    results.append(("Gemini API", gemini_success))
    
    # تقرير النتائج
    print("\n" + "="*60)
    print("📋 تقرير النتائج النهائي")
    print("="*60)
    
    all_success = True
    for service_name, success in results:
        status = "✅ نجح" if success else "❌ فشل"
        print(f"{status} {service_name}")
        if not success:
            all_success = False
    
    print("\n" + "="*60)
    if all_success:
        print("🎉 جميع APIs تعمل بنجاح! لا حاجة لـ Tesseract")
        print("🚀 النظام جاهز للاستخدام مع الخدمات الحقيقية")
    else:
        print("⚠️ بعض APIs فشلت - تحقق من المفاتيح والاتصال")
    print("="*60)
    
    return all_success

if __name__ == "__main__":
    test_landingai_extraction()
    success = asyncio.run(main())
    exit(0 if success else 1) 