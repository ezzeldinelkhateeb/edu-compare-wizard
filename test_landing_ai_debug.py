#!/usr/bin/env python3
"""
برنامج تشخيص مشاكل Landing AI
Landing AI Diagnostic Tool
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

# إضافة المسار الحالي إلى PYTHONPATH
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "backend"))

try:
    from backend.app.services.landing_ai_service import LandingAIService
    from backend.app.core.config import get_settings
except ImportError as e:
    print(f"❌ خطأ في استيراد الوحدات: {e}")
    sys.exit(1)

class LandingAIDebugger:
    def __init__(self):
        self.settings = get_settings()
        self.landing_ai = LandingAIService()
        
    def check_environment(self):
        """فحص البيئة والإعدادات"""
        print("🔍 فحص البيئة والإعدادات...")
        print(f"📁 مجلد العمل: {os.getcwd()}")
        print(f"🐍 إصدار Python: {sys.version}")
        
        # فحص API Key
        api_key = self.settings.VISION_AGENT_API_KEY
        if api_key:
            print(f"🔑 API Key موجود: {'*' * 20}{api_key[-8:]}")
        else:
            print("❌ API Key غير موجود")
            
        # فحص agentic_doc
        try:
            import agentic_doc
            print(f"✅ agentic_doc متاح: إصدار {getattr(agentic_doc, '__version__', 'غير معروف')}")
        except ImportError:
            print("❌ agentic_doc غير متاح")
            
        # فحص خدمة Landing AI
        print(f"🤖 خدمة Landing AI: {'مفعلة' if self.landing_ai.enabled else 'معطلة'}")
        print(f"📚 agentic_doc متاح: {'نعم' if self.landing_ai.agentic_doc_available else 'لا'}")
        
    def test_connection(self):
        """اختبار الاتصال مع Landing AI API"""
        print("\n🌐 اختبار الاتصال مع Landing AI API...")
        
        try:
            import requests
            import agentic_doc.utils
            
            # اختبار مفتاح API
            print("🔐 اختبار صحة مفتاح API...")
            
            # محاولة اختبار بسيط للاتصال
            headers = {
                'Authorization': f'Bearer {self.settings.VISION_AGENT_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # اختبار سريع للاتصال
            test_url = "https://api.va.landing.ai/v1/tools"
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ الاتصال مع API نجح")
            elif response.status_code == 401:
                print("❌ مفتاح API غير صحيح أو منتهي الصلاحية")
            elif response.status_code == 403:
                print("❌ لا يوجد صلاحية للوصول إلى API")
            else:
                print(f"⚠️ استجابة غير متوقعة: {response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            print("❌ انتهت مهلة الاتصال - مشكلة في الشبكة")
        except requests.exceptions.ConnectionError:
            print("❌ خطأ في الاتصال - تحقق من الإنترنت")
        except Exception as e:
            print(f"❌ خطأ في اختبار الاتصال: {e}")
    
    async def test_image_extraction(self, image_path: str):
        """اختبار استخراج النص من صورة محددة"""
        print(f"\n🖼️ اختبار استخراج النص من: {image_path}")
        
        if not os.path.exists(image_path):
            print(f"❌ الصورة غير موجودة: {image_path}")
            return
            
        # معلومات الصورة
        from PIL import Image
        try:
            with Image.open(image_path) as img:
                print(f"📐 أبعاد الصورة: {img.size}")
                print(f"🎨 نمط الصورة: {img.mode}")
                print(f"📊 حجم الملف: {os.path.getsize(image_path) / (1024*1024):.1f} MB")
        except Exception as e:
            print(f"❌ خطأ في قراءة معلومات الصورة: {e}")
            return
        
        # اختبار الاستخراج
        start_time = time.time()
        
        try:
            print("🚀 بدء عملية الاستخراج...")
            result = await self.landing_ai.extract_from_file(image_path)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ اكتمل الاستخراج في {processing_time:.2f} ثانية")
            print(f"📊 النتائج:")
            print(f"   - نجح: {result.success}")
            print(f"   - طول النص: {len(result.markdown_content)} حرف")
            print(f"   - مستوى الثقة: {result.confidence_score:.1%}")
            print(f"   - عدد القطع: {result.total_chunks}")
            print(f"   - نص={result.text_elements}, جداول={result.table_elements}")
            
            if result.error_message:
                print(f"⚠️ رسالة خطأ: {result.error_message}")
                
            # عرض عينة من النص
            if result.markdown_content:
                preview = result.markdown_content[:300] + "..." if len(result.markdown_content) > 300 else result.markdown_content
                print(f"📝 عينة من النص المستخرج:\n{preview}")
            else:
                print("❌ لم يتم استخراج أي نص")
                
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"❌ فشل الاستخراج بعد {processing_time:.2f} ثانية")
            print(f"💥 تفاصيل الخطأ: {e}")
            print(f"🔍 نوع الخطأ: {type(e).__name__}")
            
            # تحليل الخطأ
            error_str = str(e).lower()
            if "timeout" in error_str or "timed out" in error_str:
                print("🕒 السبب المحتمل: انتهاء مهلة الاتصال")
                print("💡 الحلول المقترحة:")
                print("   - زيادة المهلة الزمنية")
                print("   - تصغير الصورة")
                print("   - إعادة المحاولة")
            elif "connection" in error_str:
                print("🌐 السبب المحتمل: مشكلة في الاتصال")
                print("💡 الحلول المقترحة:")
                print("   - فحص الإنترنت")
                print("   - فحص API key")
                print("   - إعادة المحاولة لاحقاً")
            elif "server" in error_str or "disconnected" in error_str:
                print("🏢 السبب المحتمل: مشكلة في خادم Landing AI")
                print("💡 الحلول المقترحة:")
                print("   - إعادة المحاولة بعد قليل")
                print("   - التحقق من حالة خدمة Landing AI")
    
    def test_multiple_timeouts(self, image_path: str):
        """اختبار مهل زمنية مختلفة"""
        print(f"\n⏱️ اختبار مهل زمنية مختلفة للصورة: {Path(image_path).name}")
        
        timeouts = [60, 120, 300, 600]  # مهل مختلفة بالثواني
        
        for timeout in timeouts:
            print(f"\n🕒 اختبار مهلة {timeout} ثانية...")
            
            # تعديل المهلة في متغيرات البيئة
            os.environ['REQUESTS_TIMEOUT'] = str(timeout)
            os.environ['HTTP_TIMEOUT'] = str(timeout)
            os.environ['HTTPX_TIMEOUT'] = str(timeout)
            
            try:
                # اختبار بسيط للاتصال أولاً
                import agentic_doc
                from agentic_doc.parse import parse
                
                start_time = time.time()
                result = parse(image_path)
                end_time = time.time()
                
                print(f"✅ نجح في {end_time - start_time:.1f} ثانية مع مهلة {timeout}s")
                
                if result and len(result) > 0:
                    doc = result[0]
                    content = getattr(doc, 'markdown', '')
                    print(f"📝 طول المحتوى: {len(content)} حرف")
                    break
                else:
                    print("⚠️ نتيجة فارغة")
                    
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ فشل بعد {elapsed:.1f} ثانية: {e}")
                
                if "timeout" in str(e).lower():
                    print(f"🕒 انتهت المهلة ({timeout}s)")
                else:
                    print(f"💥 خطأ آخر: {type(e).__name__}")

async def main():
    """الدالة الرئيسية"""
    print("🔧 برنامج تشخيص مشاكل Landing AI")
    print("=" * 50)
    
    debugger = LandingAIDebugger()
    
    # 1. فحص البيئة
    debugger.check_environment()
    
    # 2. اختبار الاتصال
    debugger.test_connection()
    
    # 3. اختبار الصورة المحددة
    image_path = "d:/ezz/compair/edu-compare-wizard/101.jpg"
    await debugger.test_image_extraction(image_path)
    
    # 4. اختبار مهل مختلفة
    debugger.test_multiple_timeouts(image_path)
    
    print("\n🏁 انتهى التشخيص")

if __name__ == "__main__":
    asyncio.run(main())
