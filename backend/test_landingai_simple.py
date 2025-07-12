#!/usr/bin/env python3
"""
اختبار بسيط لـ LandingAI مع طرق مختلفة للمصادقة
Simple LandingAI Test with Different Authentication Methods
"""

import asyncio
import aiohttp
import aiofiles
import json
import os
import base64
from datetime import datetime

async def test_with_bearer_auth():
    """اختبار مع Bearer token"""
    
    print("="*50)
    print("🧪 اختبار LandingAI - Bearer Token")
    print("="*50)
    
    api_key = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"
    api_endpoint = "https://api.va.landing.ai/v1/tools/agentic-document-analysis"
    test_image = "103.jpg"
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        data = aiohttp.FormData()
        data.add_field('include_marginalia', 'false')
        data.add_field('include_metadata_in_markdown', 'true')
        
        async with aiofiles.open(test_image, 'rb') as f:
            file_content = await f.read()
            data.add_field('file', file_content, filename=test_image)
        
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_endpoint, headers=headers, data=data) as response:
                print(f"📡 Status: {response.status}")
                text = await response.text()
                print(f"📝 Response: {text[:200]}...")
                
                if response.status == 200:
                    return True, await response.json()
                else:
                    return False, text
                    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False, str(e)

async def test_with_basic_auth():
    """اختبار مع Basic authentication"""
    
    print("="*50)
    print("🧪 اختبار LandingAI - Basic Auth")
    print("="*50)
    
    api_key = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"
    api_endpoint = "https://api.va.landing.ai/v1/tools/agentic-document-analysis"
    test_image = "103.jpg"
    
    try:
        headers = {
            'Authorization': f'Basic {api_key}'
        }
        
        data = aiohttp.FormData()
        data.add_field('include_marginalia', 'false')
        
        async with aiofiles.open(test_image, 'rb') as f:
            file_content = await f.read()
            data.add_field('file', file_content, filename=test_image)
        
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_endpoint, headers=headers, data=data) as response:
                print(f"📡 Status: {response.status}")
                text = await response.text()
                print(f"📝 Response: {text[:200]}...")
                
                if response.status == 200:
                    return True, await response.json()
                else:
                    return False, text
                    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False, str(e)

async def test_with_curl_equivalent():
    """اختبار مماثل لـ curl من الوثائق"""
    
    print("="*50)
    print("🧪 اختبار LandingAI - cURL مماثل")
    print("="*50)
    
    api_key = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"
    api_endpoint = "https://api.va.landing.ai/v1/tools/agentic-document-analysis"
    test_image = "103.jpg"
    
    try:
        # استخدام نفس headers من الوثائق
        headers = {
            'Authorization': f'Basic {api_key}',
            # لا نضع Content-Type للـ multipart/form-data لأن aiohttp سيضعه تلقائياً
        }
        
        # إعداد البيانات كما في الوثائق
        data = aiohttp.FormData()
        data.add_field('include_marginalia', 'true')
        data.add_field('include_metadata_in_markdown', 'true')
        
        # قراءة الملف
        async with aiofiles.open(test_image, 'rb') as f:
            file_content = await f.read()
            # محاولة بـ content-type مختلف
            data.add_field('file', file_content, filename='103.jpg', content_type='image/jpeg')
        
        print(f"📤 إرسال {len(file_content)} بايت إلى {api_endpoint}")
        
        timeout = aiohttp.ClientTimeout(total=480)  # كما في الوثائق
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_endpoint, headers=headers, data=data) as response:
                print(f"📡 HTTP Status: {response.status}")
                print(f"📋 Headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"📝 Response Length: {len(response_text)} chars")
                print(f"📄 Response Preview: {response_text[:300]}...")
                
                if response.status == 200:
                    try:
                        json_data = json.loads(response_text)
                        return True, json_data
                    except json.JSONDecodeError as e:
                        print(f"❌ خطأ في JSON: {e}")
                        return False, response_text
                else:
                    return False, response_text
                    
    except Exception as e:
        print(f"❌ خطأ في الطلب: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

async def test_simple_get():
    """اختبار GET بسيط للتحقق من الاتصال"""
    
    print("="*50)
    print("🧪 اختبار GET بسيط")
    print("="*50)
    
    api_key = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"
    
    try:
        # اختبار endpoint أساسي
        base_url = "https://api.va.landing.ai"
        
        headers = {
            'Authorization': f'Basic {api_key}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, headers=headers) as response:
                print(f"📡 Base URL Status: {response.status}")
                text = await response.text()
                print(f"📝 Response: {text[:200]}...")
                
                return response.status < 500, text
                
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False, str(e)

async def main():
    """تشغيل جميع الاختبارات"""
    
    print("🎯 اختبارات متعددة لـ LandingAI API")
    print("🔧 سنجرب طرق مصادقة مختلفة")
    
    if not os.path.exists("103.jpg"):
        print("❌ لا يوجد ملف 103.jpg للاختبار")
        return False
    
    tests = [
        ("GET بسيط", test_simple_get),
        ("Bearer Token", test_with_bearer_auth),
        ("Basic Auth", test_with_basic_auth),  
        ("cURL مماثل", test_with_curl_equivalent),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
        
        try:
            success, data = await test_func()
            results.append((test_name, success, data))
            
            if success:
                print(f"✅ {test_name} نجح!")
                if isinstance(data, dict):
                    print(f"📊 تم الحصول على بيانات JSON")
                    # حفظ البيانات للفحص
                    with open(f"landingai_{test_name.replace(' ', '_')}_result.json", 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                break  # إذا نجح اختبار، توقف
            else:
                print(f"❌ {test_name} فشل")
                
        except Exception as e:
            print(f"❌ خطأ في {test_name}: {e}")
            results.append((test_name, False, str(e)))
        
        await asyncio.sleep(2)  # استراحة بين الاختبارات
    
    # تقرير النتائج
    print(f"\n{'='*60}")
    print("📋 تقرير النتائج")
    print(f"{'='*60}")
    
    any_success = False
    for test_name, success, data in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if success:
            any_success = True
    
    if any_success:
        print("\n🎉 نجح على الأقل اختبار واحد!")
        print("🚀 LandingAI API يعمل!")
    else:
        print("\n⚠️ جميع الاختبارات فشلت")
        print("🔍 تحقق من API key أو اتصال الإنترنت")
    
    return any_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 