"""
اختبار شامل ودقيق للمقارنة البصرية للنظام التعليمي
Comprehensive Visual Comparison Test for Educational System
"""

import asyncio
import os
import sys
from pathlib import Path
import json

# إضافة مسار التطبيق
sys.path.append(str(Path(__file__).parent))

from app.services.visual_comparison_service import EnhancedVisualComparisonService
from app.core.config import get_settings


async def test_visual_comparison_101_104():
    """
    اختبار مقارنة الصورتين 101.jpg و 104.jpg
    Test comparison between 101.jpg and 104.jpg
    """
    print("🚀 بدء اختبار المقارنة البصرية الشاملة")
    print("=" * 60)
    
    # مسارات الصور
    image_101_path = "../101.jpg"
    image_104_path = "../104.jpg"
    
    # التحقق من وجود الصور
    if not os.path.exists(image_101_path):
        print(f"❌ الصورة غير موجودة: {image_101_path}")
        return
        
    if not os.path.exists(image_104_path):
        print(f"❌ الصورة غير موجودة: {image_104_path}")
        return
        
    print(f"✅ تم العثور على الصورتين:")
    print(f"   📷 الصورة الأولى: {image_101_path}")
    print(f"   📷 الصورة الثانية: {image_104_path}")
    print()
    
    try:
        # إنشاء خدمة المقارنة البصرية
        settings = get_settings()
        visual_service = EnhancedVisualComparisonService()
        
        print("📊 بدء عملية المقارنة البصرية...")
        print("-" * 40)
        
        # تشغيل المقارنة
        result = await visual_service.compare_images(
            old_image_path=image_101_path,
            new_image_path=image_104_path,
            output_dir="comparison_output"
        )
        
        print("\n🎯 نتائج المقارنة البصرية:")
        print("=" * 50)
        
        # النتيجة الإجمالية
        print(f"📈 النتيجة الإجمالية: {result.similarity_score:.2f}%")
        print()
        
        # النتائج التفصيلية
        print("📋 النتائج التفصيلية:")
        print(f"   🔍 SSIM (التشابه الهيكلي): {result.ssim_score:.4f}")
        print(f"   🔗 pHash (بصمة الصورة): {result.phash_score:.4f}")
        print(f"   📊 الهستوجرام: {result.histogram_correlation:.4f}")
        print(f"   🎯 مطابقة الميزات: {result.feature_matching_score:.4f}")
        print(f"   📐 تشابه الحواف: {result.edge_similarity:.4f}")
        
        if result.clip_score is not None:
            print(f"   🤖 CLIP (ذكي): {result.clip_score:.4f}")
        else:
            print("   🤖 CLIP: غير متاح")
            
        print()
        
        # تحليل النتائج
        print("🧠 تحليل النتائج:")
        print("-" * 30)
        
        if result.similarity_score >= 90:
            print("✅ الصورتان متطابقتان تقريباً (تغيرات طفيفة جداً)")
        elif result.similarity_score >= 75:
            print("🟡 الصورتان متشابهتان مع بعض التغيرات")
        elif result.similarity_score >= 50:
            print("🟠 الصورتان مختلفتان إلى حد ما")
        else:
            print("🔴 الصورتان مختلفتان بشكل كبير")
            
        print()
        
        # تحليل مقاييس فردية
        print("🔎 تحليل المقاييس الفردية:")
        print("-" * 40)
        
        # SSIM
        if result.ssim_score >= 0.9:
            print("   📏 SSIM: تشابه هيكلي عالي جداً")
        elif result.ssim_score >= 0.7:
            print("   📏 SSIM: تشابه هيكلي جيد")
        elif result.ssim_score >= 0.5:
            print("   📏 SSIM: تشابه هيكلي متوسط")
        else:
            print("   📏 SSIM: تشابه هيكلي منخفض")
            
        # pHash
        if result.phash_score >= 0.95:
            print("   🔗 pHash: بصمات متطابقة تقريباً")
        elif result.phash_score >= 0.8:
            print("   🔗 pHash: بصمات متشابهة")
        else:
            print("   🔗 pHash: بصمات مختلفة")
            
        # الهستوجرام
        if result.histogram_correlation >= 0.9:
            print("   📊 الهستوجرام: توزيع ألوان متشابه جداً")
        elif result.histogram_correlation >= 0.7:
            print("   📊 الهستوجرام: توزيع ألوان متشابه")
        else:
            print("   📊 الهستوجرام: توزيع ألوان مختلف")
            
        # الحواف
        if result.edge_similarity >= 0.8:
            print("   📐 الحواف: تشابه عالي في الحواف والخطوط")
        elif result.edge_similarity >= 0.6:
            print("   📐 الحواف: تشابه متوسط في الحواف")
        else:
            print("   📐 الحواف: اختلاف في الحواف والخطوط")
            
        print()
        
        # حفظ النتائج
        output_file = f"visual_comparison_result_{Path(image_101_path).stem}_vs_{Path(image_104_path).stem}.json"
        
        result_data = {
            "timestamp": str(asyncio.get_event_loop().time()),
            "image_1": image_101_path,
            "image_2": image_104_path,
            "overall_similarity": result.similarity_score,
            "detailed_scores": {
                "ssim": result.ssim_score,
                "phash": result.phash_score,
                "clip": result.clip_score,
                "histogram": result.histogram_correlation,
                "features": result.feature_matching_score,
                "edges": result.edge_similarity
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
            
        print(f"💾 تم حفظ النتائج في: {output_file}")
        
        # توصيات
        print("\n💡 التوصيات:")
        print("-" * 20)
        
        if result.similarity_score < 80:
            print("   📝 يُنصح بمراجعة التغيرات في المحتوى التعليمي")
            
        if result.ssim_score < 0.7:
            print("   🏗️ هناك تغيرات هيكلية في تخطيط الصورة")
            
        if result.histogram_correlation < 0.8:
            print("   🎨 هناك تغيرات في الألوان أو الإضاءة")
            
        if result.edge_similarity < 0.7:
            print("   ✏️ هناك تغيرات في النصوص أو الرسوم البيانية")
            
        print("\n✅ اكتمل الاختبار بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في المقارنة البصرية: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_comparison_sensitivity():
    """
    اختبار حساسية المقارنة البصرية
    Test visual comparison sensitivity
    """
    print("\n🎯 اختبار حساسية المقارنة البصرية")
    print("=" * 50)
    
    # اختبار مقارنة الصورة مع نفسها
    image_101_path = "../101.jpg"
    
    if not os.path.exists(image_101_path):
        print(f"❌ الصورة غير موجودة: {image_101_path}")
        return
        
    try:
        visual_service = EnhancedVisualComparisonService()
        
        print("🔄 مقارنة الصورة مع نفسها (يجب أن تكون 100%)...")
        
        result = await visual_service.compare_images(
            old_image_path=image_101_path,
            new_image_path=image_101_path
        )
        
        print(f"📊 النتيجة (نفس الصورة): {result.similarity_score:.2f}%")
        print(f"   SSIM: {result.ssim_score:.4f}")
        print(f"   pHash: {result.phash_score:.4f}")
        
        if result.similarity_score >= 99:
            print("✅ المقارنة دقيقة - نفس الصورة تعطي نتيجة عالية")
        else:
            print("⚠️ قد تحتاج المقارنة لتعديل في الحساسية")
            
    except Exception as e:
        print(f"❌ خطأ في اختبار الحساسية: {str(e)}")


async def main():
    """دالة رئيسية لتشغيل جميع الاختبارات"""
    print("🎓 نظام اختبار المقارنة البصرية للمحتوى التعليمي")
    print("Educational Content Visual Comparison Test System")
    print("=" * 70)
    print()
    
    # تشغيل الاختبار الرئيسي
    await test_visual_comparison_101_104()
    
    # تشغيل اختبار الحساسية
    await test_comparison_sensitivity()
    
    print("\n" + "=" * 70)
    print("🏁 انتهت جميع الاختبارات")


if __name__ == "__main__":
    asyncio.run(main())
