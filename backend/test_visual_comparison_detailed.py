#!/usr/bin/env python3
"""
اختبار مفصل للمقارنة البصرية
Detailed Visual Comparison Test
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.visual_comparison_service import EnhancedVisualComparisonService
from app.core.config import get_settings

async def test_visual_comparison():
    """اختبار المقارنة البصرية بالتفصيل"""
    
    # مسارات الصور
    old_image_path = r"D:\ezz\compair\edu-compare-wizard\101.jpg"
    new_image_path = r"D:\ezz\compair\edu-compare-wizard\104.jpg"
    
    # التحقق من وجود الصور
    if not os.path.exists(old_image_path):
        print(f"❌ الصورة القديمة غير موجودة: {old_image_path}")
        return
    
    if not os.path.exists(new_image_path):
        print(f"❌ الصورة الجديدة غير موجودة: {new_image_path}")
        return
    
    print("🔍 بدء اختبار المقارنة البصرية المفصل...")
    print(f"📁 الصورة القديمة: {old_image_path}")
    print(f"📁 الصورة الجديدة: {new_image_path}")
    print("=" * 80)
    
    # إنشاء خدمة المقارنة البصرية
    visual_service = EnhancedVisualComparisonService()
    
    try:
        # إجراء المقارنة
        start_time = datetime.now()
        print(f"⏱️  بدء المقارنة في: {start_time.strftime('%H:%M:%S')}")
        
        result = await visual_service.compare_images(
            old_image_path=old_image_path,
            new_image_path=new_image_path,
            old_filename="101.jpg",
            new_filename="104.jpg"
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ انتهت المقارنة في: {end_time.strftime('%H:%M:%S')}")
        print(f"⏱️  المدة الزمنية: {duration:.2f} ثانية")
        print("=" * 80)
        
        # عرض النتائج بالتفصيل
        print("📊 نتائج المقارنة البصرية:")
        print("-" * 40)
        
        print(f"🎯 النتيجة الإجمالية: {result.similarity_score:.2f}%")
        print(f"📏 SSIM Score: {result.ssim_score:.4f}")
        print(f"🔍 pHash Score: {result.phash_score:.4f}")
        print(f"📊 Histogram Correlation: {result.histogram_correlation:.4f}")
        print(f"🔗 Feature Matching Score: {result.feature_matching_score:.4f}")
        print(f"🔲 Edge Similarity: {result.edge_similarity:.4f}")
        print(f"📐 Layout Similarity: {result.layout_similarity:.4f}")
        print(f"📝 Text Region Overlap: {result.text_region_overlap:.4f}")
        
        if result.clip_score is not None:
            print(f"🖼️  CLIP Score: {result.clip_score:.4f}")
        
        print("-" * 40)
        print(f"📐 حجم الصورة القديمة: {result.old_image_size}")
        print(f"📐 حجم الصورة الجديدة: {result.new_image_size}")
        print(f"📊 Mean Squared Error: {result.mean_squared_error:.4f}")
        print(f"📊 Peak Signal-to-Noise Ratio: {result.peak_signal_noise_ratio:.2f} dB")
        
        print("-" * 40)
        print(f"🔍 نوع المحتوى المكتشف: {result.content_type_detected}")
        print(f"✅ تطابق المحتوى المحتمل: {'نعم' if result.probable_content_match else 'لا'}")
        print(f"🚨 تغييرات كبيرة مكتشفة: {'نعم' if result.major_changes_detected else 'لا'}")
        print(f"🔄 اختلافات مكتشفة: {'نعم' if result.difference_detected else 'لا'}")
        
        # عرض الأوزان المستخدمة
        print("-" * 40)
        print("⚖️  الأوزان المستخدمة في الحساب:")
        for metric, weight in result.weights_used.items():
            print(f"   {metric}: {weight:.2f}")
        
        # عرض المناطق المتغيرة
        if result.changed_regions:
            print("-" * 40)
            print(f"🔍 المناطق المتغيرة ({len(result.changed_regions)} منطقة):")
            for i, region in enumerate(result.changed_regions[:5], 1):  # عرض أول 5 مناطق
                print(f"   المنطقة {i}:")
                print(f"     📍 الموقع: ({region['x']}, {region['y']})")
                print(f"     📏 الحجم: {region['width']} x {region['height']}")
                print(f"     📊 المساحة: {region['area']} بكسل")
                print(f"     🎯 المركز: ({region['center']['x']:.1f}, {region['center']['y']:.1f})")
        
        # عرض التحليل والتوصيات
        print("-" * 40)
        print("📝 ملخص التحليل:")
        print(f"   {result.analysis_summary}")
        
        print("-" * 40)
        print("💡 التوصيات:")
        print(f"   {result.recommendations}")
        
        print("-" * 40)
        print("ℹ️  ملاحظات الثقة:")
        print(f"   {result.confidence_notes}")
        
        # حفظ النتائج
        results_dict = {
            "test_info": {
                "old_image": old_image_path,
                "new_image": new_image_path,
                "test_time": datetime.now().isoformat(),
                "duration_seconds": duration
            },
            "similarity_score": result.similarity_score,
            "detailed_scores": {
                "ssim_score": result.ssim_score,
                "phash_score": result.phash_score,
                "clip_score": result.clip_score,
                "histogram_correlation": result.histogram_correlation,
                "feature_matching_score": result.feature_matching_score,
                "edge_similarity": result.edge_similarity,
                "layout_similarity": result.layout_similarity,
                "text_region_overlap": result.text_region_overlap
            },
            "image_info": {
                "old_image_size": result.old_image_size,
                "new_image_size": result.new_image_size,
                "mean_squared_error": result.mean_squared_error,
                "peak_signal_noise_ratio": result.peak_signal_noise_ratio
            },
            "analysis": {
                "content_type_detected": result.content_type_detected,
                "probable_content_match": result.probable_content_match,
                "major_changes_detected": result.major_changes_detected,
                "difference_detected": result.difference_detected,
                "weights_used": result.weights_used,
                "changed_regions_count": len(result.changed_regions),
                "changed_regions": result.changed_regions[:10]  # أول 10 مناطق
            },
            "summary": {
                "analysis_summary": result.analysis_summary,
                "recommendations": result.recommendations,
                "confidence_notes": result.confidence_notes
            }
        }
        
        # حفظ النتائج في ملف JSON
        output_file = f"visual_comparison_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join(".", output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2, default=str)
        
        print("=" * 80)
        print(f"💾 تم حفظ النتائج في: {output_path}")
        
        # خلاصة سريعة
        print("=" * 80)
        print("📋 خلاصة سريعة:")
        if result.similarity_score >= 95:
            print(f"✅ الصورتان متطابقتان تقريباً ({result.similarity_score:.1f}%)")
        elif result.similarity_score >= 85:
            print(f"🔶 الصورتان متشابهتان مع اختلافات طفيفة ({result.similarity_score:.1f}%)")
        elif result.similarity_score >= 70:
            print(f"🔸 الصورتان متشابهتان مع اختلافات واضحة ({result.similarity_score:.1f}%)")
        else:
            print(f"🔴 الصورتان مختلفتان بشكل كبير ({result.similarity_score:.1f}%)")
        
        if result.major_changes_detected:
            print("🚨 تم اكتشاف تغييرات كبيرة")
        
        if result.changed_regions:
            print(f"🔍 تم اكتشاف {len(result.changed_regions)} منطقة متغيرة")
        
    except Exception as e:
        print(f"❌ خطأ في المقارنة: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 اختبار المقارنة البصرية المفصل")
    print("=" * 80)
    asyncio.run(test_visual_comparison())
