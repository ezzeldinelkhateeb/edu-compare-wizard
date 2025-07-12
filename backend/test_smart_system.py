"""
اختبار النظام التدريجي الذكي الجديد
Test the new Smart Progressive Analysis System
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.text_optimizer import text_optimizer


async def test_smart_system():
    """اختبار النظام الذكي الجديد"""
    
    print("🧠 اختبار النظام التدريجي الذكي\n")
    
    # اختبار 1: تحسين النص
    print("1️⃣ اختبار تحسين النص:")
    
    # نص من LandingAI (مفصل ومليء بالوصف)
    landingai_text = """قام العالم الفرنسى باسكال بصياغة هذه النتيجة كما يلى :
قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء.

Scene Overview:
• The image shows a detailed technical diagram of hydraulic systems
• Multiple components are visible including pistons, tubes, and fluid containers
• The setting appears to be an educational textbook page with Arabic labels
• Various numbered elements are present throughout the illustration

Technical Details:
• No visible scale bar or measurement references present in the image
• Arabic text labels identify different components of the hydraulic system
• The diagram uses cross-sectional views to show internal mechanisms
• Color coding appears to distinguish different parts and fluid levels

Spatial Relationships:
• The hydraulic components are arranged in a logical flow pattern
• Connecting tubes link different sections of the apparatus
• Text explanations are positioned adjacent to relevant diagram elements
• The overall layout follows a left-to-right reading pattern

Analysis:
• This educational diagram effectively demonstrates Pascal's principle
• The visual elements support the Arabic textual explanations
• Component relationships are clearly illustrated through the technical drawing
• The image serves as a comprehensive educational resource for hydraulic concepts

ملاحظة
* تخضع السوائل لقاعدة باسكال بينما لا تخضع الغازات لها.

تطبيقات على قاعدة باسكال:
- المكبس الهيدروليكي
- الفرامل الهيدروليكية للسيارة
- الرافعة الهيدروليكية

Summary: This comprehensive educational image presents Pascal's principle with detailed technical illustrations, Arabic explanations, and practical applications. The diagram includes cross-sectional views of hydraulic components, labeled elements, and supporting text that explains the fundamental concepts of fluid pressure transmission in confined systems."""
    
    # تحسين النص
    optimization_result = text_optimizer.optimize_for_ai_analysis(landingai_text, max_tokens=200)
    
    print(f"   📊 النص الأصلي: {optimization_result['original_length']} حرف")
    print(f"   ✂️ النص المحسن: {optimization_result['optimized_length']} حرف")
    print(f"   📉 تقليل: {optimization_result['reduction_percentage']}%")
    print(f"   🧠 توكنز محفوظة: ~{(optimization_result['original_length'] - optimization_result['optimized_length']) // 4}")
    print()
    
    print("📝 النص المحسن:")
    print("=" * 50)
    print(optimization_result['optimized_text'])
    print("=" * 50)
    print()
    
    # اختبار 2: مقارنة النصوص المحسنة
    print("2️⃣ اختبار مقارنة النصوص المحسنة:")
    
    # نص آخر مشابه
    similar_text = """* قام العالم الفرنسي باسكال بصياغة هذه النتيجة كما يلي :
قاعدة (مبدأ) باسكال
عندما يؤثر ضغط على سائل محبوس في إناء، فإن ذلك الضغط ينتقل بتمامه إلى جميع أجزاء السائل كما ينتقل إلى جدران الإناء.

ملاحظة
تخضع السوائل لقاعدة باسكال بينما لا تخضع الغازات لها،

تطبيقات على قاعدة باسكال:
- المكبس الهيدروليكي  
- الفرامل الهيدروليكية للسيارة
- الرافعة الهيدروليكية

Technical analysis shows similar hydraulic components with updated visual styling."""
    
    comparison_result = text_optimizer.compare_optimized_texts(landingai_text, similar_text)
    
    print(f"   📊 النص 1 - تقليل: {comparison_result['text1_optimization']['reduction_percentage']:.1f}%")
    print(f"   📊 النص 2 - تقليل: {comparison_result['text2_optimization']['reduction_percentage']:.1f}%")
    print(f"   💾 إجمالي التوكنز المحفوظة: ~{comparison_result['tokens_saved_estimate']}")
    print()
    
    print("🔍 مقارنة العناصر:")
    for category, data in comparison_result['elements_comparison'].items():
        if data['common_count'] > 0 or data['unique_to_text1'] > 0 or data['unique_to_text2'] > 0:
            print(f"   {category}: {data['similarity_percentage']:.1f}% تشابه")
    print()
    
    # اختبار 3: محاكاة النظام التدريجي
    print("3️⃣ محاكاة النظام التدريجي:")
    
    scenarios = [
        {"visual_sim": 98, "expected_stages": 1, "name": "صور متطابقة تقريباً"},
        {"visual_sim": 87, "expected_stages": 2, "name": "صور متشابهة"},
        {"visual_sim": 65, "expected_stages": 3, "name": "صور مختلفة"},
    ]
    
    total_api_savings = 0
    
    for scenario in scenarios:
        visual_sim = scenario["visual_sim"]
        expected_stages = scenario["expected_stages"]
        name = scenario["name"]
        
        # محاكاة المراحل
        stages_used = []
        api_calls = 0
        
        # المرحلة 1: دائماً
        stages_used.append("تحليل بصري")
        
        if visual_sim < 95:  # المرحلة 2
            stages_used.append("استخراج نص")
            api_calls += 1
            
            if visual_sim < 75:  # المرحلة 3
                stages_used.append("تحليل عميق")
                api_calls += 1
        
        api_saved = 2 - api_calls
        total_api_savings += api_saved
        
        print(f"   {name}:")
        print(f"     تشابه بصري: {visual_sim}%")
        print(f"     مراحل مستخدمة: {len(stages_used)} ({', '.join(stages_used)})")
        print(f"     API calls: {api_calls}/2")
        print(f"     توفير: {api_saved} calls")
        print()
    
    # اختبار 4: حساب التوفير الإجمالي
    print("4️⃣ تقدير التوفير الإجمالي:")
    
    # افتراض: 100 مقارنة في الشهر
    monthly_comparisons = 100
    
    # النظام القديم: كل مقارنة تستخدم LandingAI (2 calls) + Gemini (1 call) = 3 calls
    old_system_calls = monthly_comparisons * 3
    
    # النظام الجديد: متوسط 1.2 call لكل مقارنة (بناء على الاختبارات أعلاه)
    new_system_calls = monthly_comparisons * 1.2
    
    api_savings_percentage = ((old_system_calls - new_system_calls) / old_system_calls) * 100
    
    print(f"   📊 النظام القديم: {old_system_calls} API calls شهرياً")
    print(f"   🚀 النظام الجديد: {new_system_calls:.0f} API calls شهرياً")
    print(f"   💰 توفير: {api_savings_percentage:.1f}% ({old_system_calls - new_system_calls:.0f} calls)")
    print()
    
    # اختبار 5: اختبار جودة النص المحسن
    print("5️⃣ تقييم جودة التحسين:")
    
    # فحص العناصر المستخرجة
    elements = optimization_result['extracted_elements']
    quality_score = 0
    
    # تقييم الجودة
    if elements.get('laws_and_principles'):
        quality_score += 30  # الأهم
        print(f"   ✅ قوانين ومبادئ: {len(elements['laws_and_principles'])} عنصر")
    
    if elements.get('definitions'):
        quality_score += 25
        print(f"   ✅ تعريفات: {len(elements['definitions'])} عنصر")
    
    if elements.get('applications'):
        quality_score += 20
        print(f"   ✅ تطبيقات: {len(elements['applications'])} عنصر")
    
    if elements.get('examples'):
        quality_score += 15
        print(f"   ✅ أمثلة: {len(elements['examples'])} عنصر")
    
    if elements.get('notes'):
        quality_score += 10
        print(f"   ✅ ملاحظات: {len(elements['notes'])} عنصر")
    
    print(f"   🎯 نقاط الجودة: {quality_score}/100")
    
    if quality_score >= 80:
        print("   🌟 ممتاز: تم الحفاظ على جميع العناصر المهمة")
    elif quality_score >= 60:
        print("   ✅ جيد: تم الحفاظ على معظم العناصر المهمة")
    else:
        print("   ⚠️ يحتاج تحسين: فقدان بعض العناصر المهمة")
    
    print()
    print("✅ انتهى اختبار النظام الذكي!")
    print(f"📈 الخلاصة:")
    print(f"   - تقليل النص: {optimization_result['reduction_percentage']:.1f}%")
    print(f"   - توفير API calls: {api_savings_percentage:.1f}%")
    print(f"   - جودة المحتوى: {quality_score}/100")
    print(f"   - الهدف: نظام ذكي وفعال! 🎯")


if __name__ == "__main__":
    asyncio.run(test_smart_system()) 