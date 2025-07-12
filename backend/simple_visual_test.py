#!/usr/bin/env python3
"""
اختبار مبسط للتشابه البصري بين صور المناهج التعليمية
Simple Visual Similarity Test for Educational Curriculum Images
"""

import os
import cv2
import numpy as np
from pathlib import Path
import json
from datetime import datetime

def calculate_ssim_simple(img1_path, img2_path):
    """حساب SSIM مبسط بين صورتين"""
    try:
        # قراءة الصور وتحويلها لرمادي
        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
        
        if img1 is None or img2 is None:
            return 0.0
        
        # توحيد الأبعاد
        height = min(img1.shape[0], img2.shape[0], 500)  # تحديد بحد أقصى 500 للسرعة
        width = min(img1.shape[1], img2.shape[1], 500)
        
        img1_resized = cv2.resize(img1, (width, height))
        img2_resized = cv2.resize(img2, (width, height))
        
        # حساب الـ MSE
        mse = np.mean((img1_resized - img2_resized) ** 2)
        
        # تحويل MSE إلى نسبة تشابه
        max_pixel_value = 255.0
        if mse == 0:
            return 1.0
        
        # حساب PSNR وتحويله لنسبة تشابه
        psnr = 20 * np.log10(max_pixel_value / np.sqrt(mse))
        similarity = min(1.0, psnr / 50.0)  # تطبيع النتيجة
        
        return similarity
        
    except Exception as e:
        print(f"خطأ في حساب SSIM: {e}")
        return 0.0

def calculate_histogram_similarity(img1_path, img2_path):
    """حساب التشابه باستخدام histogram comparison"""
    try:
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        if img1 is None or img2 is None:
            return 0.0
        
        # تصغير الصور للسرعة
        img1 = cv2.resize(img1, (256, 256))
        img2 = cv2.resize(img2, (256, 256))
        
        # حساب histograms لكل قناة لون
        hist1_b = cv2.calcHist([img1], [0], None, [256], [0, 256])
        hist1_g = cv2.calcHist([img1], [1], None, [256], [0, 256])
        hist1_r = cv2.calcHist([img1], [2], None, [256], [0, 256])
        
        hist2_b = cv2.calcHist([img2], [0], None, [256], [0, 256])
        hist2_g = cv2.calcHist([img2], [1], None, [256], [0, 256])
        hist2_r = cv2.calcHist([img2], [2], None, [256], [0, 256])
        
        # مقارنة histograms باستخدام correlation
        corr_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_CORREL)
        corr_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_CORREL)
        corr_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_CORREL)
        
        return (corr_b + corr_g + corr_r) / 3
        
    except Exception as e:
        print(f"خطأ في حساب Histogram similarity: {e}")
        return 0.0

def calculate_simple_hash_similarity(img1_path, img2_path):
    """حساب تشابه بسيط باستخدام average hash"""
    try:
        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
        
        if img1 is None or img2 is None:
            return 0.0
        
        # تصغير الصور إلى 8x8
        small1 = cv2.resize(img1, (8, 8))
        small2 = cv2.resize(img2, (8, 8))
        
        # حساب المتوسط
        mean1 = np.mean(small1)
        mean2 = np.mean(small2)
        
        # إنشاء hash binary
        hash1 = (small1 > mean1).astype(int)
        hash2 = (small2 > mean2).astype(int)
        
        # حساب عدد البتات المختلفة
        diff_bits = np.sum(hash1 != hash2)
        
        # تحويل إلى نسبة تشابه
        similarity = 1.0 - (diff_bits / 64.0)
        
        return similarity
        
    except Exception as e:
        print(f"خطأ في حساب Hash similarity: {e}")
        return 0.0

def compare_images(img1_path, img2_path):
    """مقارنة صورتين وإرجاع النتائج"""
    ssim_score = calculate_ssim_simple(img1_path, img2_path)
    hist_score = calculate_histogram_similarity(img1_path, img2_path)
    hash_score = calculate_simple_hash_similarity(img1_path, img2_path)
    
    # النسب المستخدمة في النظام الحقيقي
    combined_score = (
        ssim_score * 0.5 +      # SSIM: 50%
        hash_score * 0.3 +      # Hash: 30%
        hist_score * 0.2        # Histogram: 20%
    )
    
    return {
        'ssim': ssim_score,
        'histogram': hist_score,
        'hash': hash_score,
        'combined': combined_score
    }

def run_comparison_test():
    """تشغيل اختبار المقارنة الشامل"""
    print("🚀 بدء اختبار التشابه البصري للمناهج التعليمية")
    print("="*60)
    
    # مسارات المجلدات
    base_path = Path(__file__).parent.parent
    folder_2024 = base_path / "test" / "2024"
    folder_2025 = base_path / "test" / "2025"
    
    # التحقق من وجود المجلدات
    if not folder_2024.exists():
        print(f"❌ المجلد غير موجود: {folder_2024}")
        return
    
    if not folder_2025.exists():
        print(f"❌ المجلد غير موجود: {folder_2025}")
        return
    
    # الحصول على قائمة الملفات
    files_2024 = {f.name: f for f in folder_2024.glob("*.jpg")}
    files_2025 = {f.name: f for f in folder_2025.glob("*.jpg")}
    
    # العثور على الملفات المشتركة
    common_files = set(files_2024.keys()) & set(files_2025.keys())
    
    if not common_files:
        print("❌ لا توجد ملفات مشتركة للمقارنة")
        return
    
    print(f"✅ تم العثور على {len(common_files)} ملف مشترك للمقارنة")
    print(f"📋 الملفات: {sorted(common_files)}")
    
    results = []
    scores = []
    
    print("\n" + "="*60)
    print("🔍 نتائج المقارنة التفصيلية")
    print("="*60)
    
    for filename in sorted(common_files):
        img1_path = str(files_2024[filename])
        img2_path = str(files_2025[filename])
        
        print(f"\n📷 {filename}")
        print(f"   📁 2024: {os.path.basename(img1_path)}")
        print(f"   📁 2025: {os.path.basename(img2_path)}")
        
        # حساب التشابه
        similarity = compare_images(img1_path, img2_path)
        scores.append(similarity['combined'])
        
        # طباعة النتائج
        print(f"   📊 النتائج:")
        print(f"      🏗️  SSIM: {similarity['ssim']:.3f} ({similarity['ssim']*100:.1f}%)")
        print(f"      🔍 Hash: {similarity['hash']:.3f} ({similarity['hash']*100:.1f}%)")
        print(f"      🎨 Histogram: {similarity['histogram']:.3f} ({similarity['histogram']*100:.1f}%)")
        print(f"      ⭐ النتيجة النهائية: {similarity['combined']:.3f} ({similarity['combined']*100:.1f}%)")
        
        # تقييم النتيجة
        if similarity['combined'] >= 0.95:
            evaluation = "🟢 تطابق عالي جداً - محتوى متطابق تقريباً"
        elif similarity['combined'] >= 0.85:
            evaluation = "🟡 تطابق عالي - محتوى متشابه جداً"
        elif similarity['combined'] >= 0.70:
            evaluation = "🟠 تطابق متوسط - محتوى متشابه"
        elif similarity['combined'] >= 0.50:
            evaluation = "🔴 تطابق منخفض - محتوى مختلف نسبياً"
        else:
            evaluation = "⚫ تطابق ضعيف جداً - محتوى مختلف"
        
        print(f"      📈 التقييم: {evaluation}")
        
        results.append({
            'filename': filename,
            'similarities': similarity,
            'evaluation': evaluation
        })
    
    # إحصائيات شاملة
    print("\n" + "="*60)
    print("📊 الإحصائيات الشاملة")
    print("="*60)
    
    if scores:
        avg_score = np.mean(scores)
        max_score = np.max(scores)
        min_score = np.min(scores)
        median_score = np.median(scores)
        
        print(f"📈 متوسط التشابه: {avg_score:.3f} ({avg_score*100:.1f}%)")
        print(f"📊 الوسيط: {median_score:.3f} ({median_score*100:.1f}%)")
        print(f"⬆️  أعلى تشابه: {max_score:.3f} ({max_score*100:.1f}%)")
        print(f"⬇️  أقل تشابه: {min_score:.3f} ({min_score*100:.1f}%)")
        
        # توزيع النتائج
        high_count = len([s for s in scores if s >= 0.85])
        medium_count = len([s for s in scores if 0.70 <= s < 0.85])
        low_count = len([s for s in scores if s < 0.70])
        
        print(f"\n🎯 توزيع النتائج:")
        print(f"   🟢 تشابه عالي (≥85%): {high_count} صورة ({high_count/len(scores)*100:.1f}%)")
        print(f"   🟡 تشابه متوسط (70-84%): {medium_count} صورة ({medium_count/len(scores)*100:.1f}%)")
        print(f"   🔴 تشابه منخفض (<70%): {low_count} صورة ({low_count/len(scores)*100:.1f}%)")
        
        # تحليل النتائج
        print(f"\n🔍 تحليل النتائج:")
        if avg_score >= 0.85:
            print("   ✅ النتائج ممتازة: الصور متشابهة جداً كما هو متوقع من نفس المنهج")
        elif avg_score >= 0.70:
            print("   ✅ النتائج جيدة: الصور متشابهة مع بعض الاختلافات التصميمية")
        elif avg_score >= 0.50:
            print("   ⚠️  النتائج متوسطة: قد تحتاج لتحسين خوارزمية التشابه")
        else:
            print("   ❌ النتائج ضعيفة: هناك مشكلة في خوارزمية التشابه")
        
        # حفظ النتائج
        output_data = {
            'test_date': datetime.now().isoformat(),
            'summary': {
                'total_comparisons': len(scores),
                'average_similarity': avg_score,
                'max_similarity': max_score,
                'min_similarity': min_score,
                'median_similarity': median_score
            },
            'detailed_results': results
        }
        
        output_path = Path(__file__).parent / "visual_test_results.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ النتائج التفصيلية في: {output_path}")
    
    print("\n✅ تم الانتهاء من اختبار التشابه البصري بنجاح!")

if __name__ == "__main__":
    run_comparison_test() 