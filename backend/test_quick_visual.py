#!/usr/bin/env python3
"""
اختبار سريع للمقارنة البصرية
Quick Visual Comparison Test
"""

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import imagehash
from PIL import Image
import os
from datetime import datetime

def calculate_phash_similarity(img1_path, img2_path):
    """حساب تشابه pHash"""
    hash1 = imagehash.phash(Image.open(img1_path))
    hash2 = imagehash.phash(Image.open(img2_path))
    return 1 - (hash1 - hash2) / len(hash1.hash) ** 2

def calculate_ssim(img1_path, img2_path):
    """حساب SSIM"""
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
    
    # تغيير الحجم ليكون نفس الحجم
    height = min(img1.shape[0], img2.shape[0])
    width = min(img1.shape[1], img2.shape[1])
    
    img1_resized = cv2.resize(img1, (width, height))
    img2_resized = cv2.resize(img2, (width, height))
    
    return ssim(img1_resized, img2_resized)

def calculate_histogram_similarity(img1_path, img2_path):
    """حساب تشابه الهيستوجرام"""
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    
    hist1 = cv2.calcHist([img1], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([img2], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
    
    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

def calculate_mse_psnr(img1_path, img2_path):
    """حساب MSE و PSNR"""
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
    
    # تغيير الحجم ليكون نفس الحجم
    height = min(img1.shape[0], img2.shape[0])
    width = min(img1.shape[1], img2.shape[1])
    
    img1_resized = cv2.resize(img1, (width, height))
    img2_resized = cv2.resize(img2, (width, height))
    
    mse = np.mean((img1_resized - img2_resized) ** 2)
    if mse == 0:
        psnr = float('inf')
    else:
        psnr = 20 * np.log10(255.0 / np.sqrt(mse))
    
    return mse, psnr

def quick_visual_comparison():
    """مقارنة بصرية سريعة"""
    
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
    
    print("🔍 بدء المقارنة البصرية السريعة...")
    print(f"📁 الصورة القديمة: {os.path.basename(old_image_path)}")
    print(f"📁 الصورة الجديدة: {os.path.basename(new_image_path)}")
    print("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # حساب المقاييس المختلفة
        print("📊 حساب المقاييس...")
        
        ssim_score = calculate_ssim(old_image_path, new_image_path)
        print(f"✅ SSIM: {ssim_score:.4f}")
        
        phash_score = calculate_phash_similarity(old_image_path, new_image_path)
        print(f"✅ pHash: {phash_score:.4f}")
        
        hist_corr = calculate_histogram_similarity(old_image_path, new_image_path)
        print(f"✅ Histogram: {hist_corr:.4f}")
        
        mse, psnr = calculate_mse_psnr(old_image_path, new_image_path)
        print(f"✅ MSE: {mse:.4f}")
        print(f"✅ PSNR: {psnr:.2f} dB")
        
        # حساب النتيجة الإجمالية (نفس أوزان النظام)
        weights = {
            'ssim': 0.33,
            'phash': 0.20,
            'histogram': 0.13,
            'features': 0.20,  # لن نحسبه هنا
            'edges': 0.13      # لن نحسبه هنا
        }
        
        # حساب مبسط للنتيجة الإجمالية
        basic_score = (
            ssim_score * weights['ssim'] +
            phash_score * weights['phash'] +
            hist_corr * weights['histogram']
        ) / (weights['ssim'] + weights['phash'] + weights['histogram'])
        
        overall_score = basic_score * 100
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("=" * 60)
        print("📊 النتائج:")
        print(f"🎯 النتيجة الإجمالية (مبسطة): {overall_score:.2f}%")
        print(f"⏱️  وقت المعالجة: {duration:.2f} ثانية")
        
        # تحليل النتيجة
        print("=" * 60)
        print("📋 التحليل:")
        
        if overall_score >= 95:
            print("✅ الصورتان متطابقتان تقريباً")
            print("   - تغييرات طفيفة جداً أو لا توجد تغييرات")
        elif overall_score >= 85:
            print("🔶 الصورتان متشابهتان مع اختلافات طفيفة")
            print("   - قد تكون تغييرات في النص أو التفاصيل الصغيرة")
        elif overall_score >= 70:
            print("🔸 الصورتان متشابهتان مع اختلافات واضحة")
            print("   - تغييرات ملحوظة في المحتوى")
        else:
            print("🔴 الصورتان مختلفتان بشكل كبير")
            print("   - تغييرات جوهرية في المحتوى")
        
        # تحليل مفصل للمقاييس
        print("\n🔍 تحليل المقاييس:")
        
        if ssim_score > 0.9:
            print(f"   SSIM ({ssim_score:.4f}): ممتاز - هيكل الصورة متشابه جداً")
        elif ssim_score > 0.7:
            print(f"   SSIM ({ssim_score:.4f}): جيد - هيكل الصورة متشابه")
        else:
            print(f"   SSIM ({ssim_score:.4f}): ضعيف - اختلافات في هيكل الصورة")
        
        if phash_score > 0.9:
            print(f"   pHash ({phash_score:.4f}): ممتاز - الصور متشابهة جداً")
        elif phash_score > 0.7:
            print(f"   pHash ({phash_score:.4f}): جيد - الصور متشابهة")
        else:
            print(f"   pHash ({phash_score:.4f}): ضعيف - الصور مختلفة")
        
        if hist_corr > 0.8:
            print(f"   Histogram ({hist_corr:.4f}): ممتاز - توزيع الألوان متشابه")
        elif hist_corr > 0.6:
            print(f"   Histogram ({hist_corr:.4f}): جيد - توزيع الألوان متقارب")
        else:
            print(f"   Histogram ({hist_corr:.4f}): ضعيف - توزيع الألوان مختلف")
        
        if psnr > 30:
            print(f"   PSNR ({psnr:.2f} dB): ممتاز - جودة عالية")
        elif psnr > 20:
            print(f"   PSNR ({psnr:.2f} dB): جيد - جودة مقبولة")
        else:
            print(f"   PSNR ({psnr:.2f} dB): ضعيف - جودة منخفضة")
        
        # معلومات الصور
        img1 = cv2.imread(old_image_path)
        img2 = cv2.imread(new_image_path)
        
        print("=" * 60)
        print("📐 معلومات الصور:")
        print(f"   الصورة القديمة: {img1.shape[1]}x{img1.shape[0]} بكسل")
        print(f"   الصورة الجديدة: {img2.shape[1]}x{img2.shape[0]} بكسل")
        
    except Exception as e:
        print(f"❌ خطأ في المقارنة: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 اختبار المقارنة البصرية السريع")
    print("=" * 60)
    quick_visual_comparison()
