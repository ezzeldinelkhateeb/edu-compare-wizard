"""
اختبار سريع للتحقق من إصلاح الأخطاء في المقارنة البصرية
Quick test to verify bug fixes in visual comparison
"""

import asyncio
import sys
from pathlib import Path

# إضافة مسار التطبيق
sys.path.append(str(Path(__file__).parent))

from app.services.visual_comparison_service import EnhancedVisualComparisonService


async def test_bug_fixes():
    """اختبار إصلاح الأخطاء"""
    print("🔧 اختبار إصلاح الأخطاء في المقارنة البصرية")
    print("=" * 60)
    
    try:
        visual_service = EnhancedVisualComparisonService()
        
        # اختبار 1: مقارنة الصورة مع نفسها (يجب أن تكون قريبة من 100%)
        print("🧪 الاختبار 1: مقارنة الصورة مع نفسها...")
        result1 = await visual_service.compare_images(
            old_image_path="../101.jpg",
            new_image_path="../101.jpg"
        )
        
        print(f"✅ النتيجة الكلية: {result1.similarity_score:.2f}%")
        print(f"   SSIM: {result1.ssim_score:.4f}")
        print(f"   pHash: {result1.phash_score:.4f}")
        print(f"   تشابه الحواف: {result1.edge_similarity:.4f}")
        
        # تقييم النتيجة
        if result1.similarity_score >= 95:
            print("✅ ممتاز! المقارنة دقيقة للصور المتطابقة")
        elif result1.similarity_score >= 90:
            print("🟡 جيد، لكن يمكن تحسين الدقة أكثر")
        else:
            print("🔴 ما زال هناك مشكلة في دقة المقارنة")
            
        print()
        
        # اختبار 2: مقارنة الصورتين المختلفتين
        print("🧪 الاختبار 2: مقارنة الصورتين 101.jpg و 104.jpg...")
        result2 = await visual_service.compare_images(
            old_image_path="../101.jpg",
            new_image_path="../104.jpg"
        )
        
        print(f"✅ النتيجة الكلية: {result2.similarity_score:.2f}%")
        print(f"   SSIM: {result2.ssim_score:.4f}")
        print(f"   pHash: {result2.phash_score:.4f}")
        print(f"   تشابه الحواف: {result2.edge_similarity:.4f}")
        
        print()
        
        # مقارنة النتائج
        print("📊 تحليل التحسينات:")
        print("-" * 30)
        
        edge_improvement = result1.edge_similarity > 0.5  # يجب أن تكون عالية للصور المتطابقة
        
        if edge_improvement:
            print("✅ تم إصلاح مشكلة حساب تشابه الحواف")
        else:
            print("⚠️ ما زالت هناك مشكلة في حساب تشابه الحواف")
            
        print(f"🔍 تحسن دقة المقارنة للصور المتطابقة: {result1.similarity_score:.1f}%")
        print(f"🔍 المقارنة للصور المختلفة: {result2.similarity_score:.1f}%")
        
        # التوصيات
        print("\n💡 التوصيات:")
        if result1.similarity_score < 95:
            print("   📝 يُنصح بمراجعة أوزان المقارنة لتحسين دقة الصور المتطابقة")
            
        print("\n✅ انتهى اختبار الإصلاحات")
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bug_fixes())
