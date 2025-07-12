#!/usr/bin/env python3
"""
اختبار مفتاح Gemini بسيط
"""

import os
import requests
import json

# تعيين المفتاح الجديد
API_KEY = "AIzaSyB-2F7RdbLi3BMUb2ixF07cGS0OFnq910U"

def test_gemini_api():
    """اختبار مباشر لـ Gemini API"""
    print("🚀 اختبار مفتاح Gemini API الجديد...")
    print(f"🔑 المفتاح: {API_KEY}")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "مرحبا، هل يمكنك أن ترد بكلمة واحدة فقط؟"
                    }
                ]
            }
        ]
    }
    
    try:
        print("🔄 جاري إرسال طلب إلى Gemini...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📡 كود الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ المفتاح يعمل بشكل ممتاز!")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"📝 رد Gemini: {text}")
            else:
                print("📝 تم الحصول على استجابة ولكن بدون محتوى")
            
            return True
            
        elif response.status_code == 429:
            print("❌ تجاوزت حصة API - الحد اليومي 50 طلب")
            print("⏰ انتظر حتى اليوم التالي أو قم بترقية الخطة")
            return False
            
        elif response.status_code in [401, 403]:
            print("❌ مفتاح API غير صحيح أو غير مصرح")
            return False
            
        else:
            print(f"❌ خطأ: {response.status_code}")
            print(f"📄 التفاصيل: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ انتهت مهلة الطلب")
        return False
    except requests.exceptions.ConnectionError:
        print("🌐 مشكلة في الاتصال بالإنترنت")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 اختبار مفتاح Gemini API")
    print("=" * 60)
    
    success = test_gemini_api()
    
    if success:
        print("\n🎉 المفتاح جاهز للاستخدام!")
    else:
        print("\n❌ المفتاح لا يعمل")
    
    print("=" * 60) 