"""
اختبار مبسط للنظام الذكي
Simple test for the smart system
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.text_optimizer import text_optimizer


def simple_test():
    """اختبار مبسط للنظام الذكي"""
    
    print("🧠 اختبار مبسط للنظام الذكي\n")
    
    # نص تجريبي من LandingAI
    landingai_text = """قام العالم الفرنسى باسكال بصياغة هذه النتيجة كما يلى :
قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء.

Scene Overview:
• The image shows technical diagrams
• Multiple components are visible
• Arabic labels present

ملاحظة
* تخضع السوائل لقاعدة باسكال بينما لا تخضع الغازات لها.

تطبيقات على قاعدة باسكال:
- المكبس الهيدروليكي
- الفرامل الهيدروليكية للسيارة
- الرافعة الهيدروليكية"""
    
    try:
        # اختبار تحسين النص
        result = text_optimizer.optimize_for_ai_analysis(landingai_text, max_tokens=200)
        
        print("✅ نجح اختبار تحسين النص!")
        print(f"📊 النص الأصلي: {result['original_length']} حرف")
        print(f"✂️ النص المحسن: {result['optimized_length']} حرف")
        print(f"📉 تقليل: {result['reduction_percentage']}%")
        print()
        
        print("📝 النص المحسن:")
        print("-" * 40)
        print(result['optimized_text'])
        print("-" * 40)
        print()
        
        # حساب التوفير
        tokens_saved = (result['original_length'] - result['optimized_length']) // 4
        print(f"🧠 توكنز محفوظة: ~{tokens_saved}")
        
        # تقدير التوفير لـ 100 مقارنة
        monthly_savings = tokens_saved * 100 * 2  # 2 نص لكل مقارنة
        print(f"💰 توفير شهري (100 مقارنة): ~{monthly_savings} توكن")
        
        # النظام التدريجي
        print("\n🎯 محاكاة النظام التدريجي:")
        scenarios = [
            {"name": "صور متطابقة", "visual_sim": 98, "api_calls": 0},
            {"name": "صور متشابهة", "visual_sim": 87, "api_calls": 1}, 
            {"name": "صور مختلفة", "visual_sim": 65, "api_calls": 2}
        ]
        
        total_old_calls = 0
        total_new_calls = 0
        
        for scenario in scenarios:
            old_calls = 3  # النظام القديم: LandingAI + Gemini دائماً
            new_calls = scenario["api_calls"]
            
            total_old_calls += old_calls
            total_new_calls += new_calls
            
            print(f"   {scenario['name']}: {old_calls} -> {new_calls} calls (توفير: {old_calls - new_calls})")
        
        efficiency = ((total_old_calls - total_new_calls) / total_old_calls) * 100
        print(f"\n📈 كفاءة النظام: {efficiency:.1f}% توفير في API calls")
        
        print("\n🎉 النتيجة النهائية:")
        print(f"   ✅ تقليل النص: {result['reduction_percentage']:.1f}%")
        print(f"   ✅ توفير API: {efficiency:.1f}%")
        print(f"   ✅ الهدف: نظام ذكي بسيط وفعال! 🚀")
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    simple_test() 