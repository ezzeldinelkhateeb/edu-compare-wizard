#!/usr/bin/env python3
"""
اختبار شامل لمقارنة التشابه البصري بين صور المناهج التعليمية
Test script for visual similarity comparison between educational curriculum images
"""

import os
import sys
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image
import imagehash
import json
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path

class VisualSimilarityTester:
    def __init__(self):
        self.results = {
            'test_date': datetime.now().isoformat(),
            'comparisons': [],
            'statistics': {}
        }
        
    def calculate_ssim(self, img1_path, img2_path):
        """حساب SSIM بين صورتين"""
        try:
            # قراءة الصور وتحويلها لرمادي
            img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
            
            if img1 is None or img2 is None:
                return 0.0
            
            # توحيد الأبعاد
            height = min(img1.shape[0], img2.shape[0])
            width = min(img1.shape[1], img2.shape[1])
            
            img1_resized = cv2.resize(img1, (width, height))
            img2_resized = cv2.resize(img2, (width, height))
            
            # حساب SSIM
            score = ssim(img1_resized, img2_resized)
            return score
            
        except Exception as e:
            print(f"خطأ في حساب SSIM: {e}")
            return 0.0
    
    def calculate_hash_similarity(self, img1_path, img2_path):
        """حساب التشابه باستخدام image hashing"""
        try:
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            
            # حساب عدة أنواع من الهاش
            hash1_avg = imagehash.average_hash(img1)
            hash2_avg = imagehash.average_hash(img2)
            
            hash1_phash = imagehash.phash(img1)
            hash2_phash = imagehash.phash(img2)
            
            hash1_dhash = imagehash.dhash(img1)
            hash2_dhash = imagehash.dhash(img2)
            
            # حساب المسافة (كلما قلت المسافة، زاد التشابه)
            avg_distance = hash1_avg - hash2_avg
            phash_distance = hash1_phash - hash2_phash
            dhash_distance = hash1_dhash - hash2_dhash
            
            # تحويل المسافة إلى نسبة تشابه (0-1)
            max_distance = 64  # الحد الأقصى للمسافة
            avg_similarity = max(0, 1 - (avg_distance / max_distance))
            phash_similarity = max(0, 1 - (phash_distance / max_distance))
            dhash_similarity = max(0, 1 - (dhash_distance / max_distance))
            
            return {
                'average_hash': avg_similarity,
                'perceptual_hash': phash_similarity,
                'difference_hash': dhash_similarity,
                'combined': (avg_similarity + phash_similarity + dhash_similarity) / 3
            }
            
        except Exception as e:
            print(f"خطأ في حساب Hash similarity: {e}")
            return {'average_hash': 0, 'perceptual_hash': 0, 'difference_hash': 0, 'combined': 0}
    
    def calculate_histogram_similarity(self, img1_path, img2_path):
        """حساب التشابه باستخدام histogram comparison"""
        try:
            img1 = cv2.imread(img1_path)
            img2 = cv2.imread(img2_path)
            
            if img1 is None or img2 is None:
                return 0.0
            
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
    
    def calculate_combined_similarity(self, img1_path, img2_path):
        """حساب التشابه المركب باستخدام جميع الطرق"""
        ssim_score = self.calculate_ssim(img1_path, img2_path)
        hash_scores = self.calculate_hash_similarity(img1_path, img2_path)
        hist_score = self.calculate_histogram_similarity(img1_path, img2_path)
        
        # النسب المستخدمة في النظام الحقيقي
        combined_score = (
            ssim_score * 0.5 +           # SSIM: 50%
            hash_scores['combined'] * 0.3 +  # Hash: 30%
            hist_score * 0.2             # Histogram: 20%
        )
        
        return {
            'ssim': ssim_score,
            'hash_similarity': hash_scores,
            'histogram_similarity': hist_score,
            'combined_score': combined_score
        }
    
    def compare_folders(self, folder1_path, folder2_path):
        """مقارنة جميع الصور المتطابقة في الأسماء بين مجلدين"""
        folder1 = Path(folder1_path)
        folder2 = Path(folder2_path)
        
        # الحصول على قائمة الملفات
        files1 = {f.name: f for f in folder1.glob("*.jpg")}
        files2 = {f.name: f for f in folder2.glob("*.jpg")}
        
        # العثور على الملفات المشتركة
        common_files = set(files1.keys()) & set(files2.keys())
        
        print(f"تم العثور على {len(common_files)} ملف مشترك للمقارنة")
        print(f"الملفات المشتركة: {sorted(common_files)}")
        
        for filename in sorted(common_files):
            img1_path = str(files1[filename])
            img2_path = str(files2[filename])
            
            print(f"\n🔍 مقارنة: {filename}")
            print(f"   📁 2024: {img1_path}")
            print(f"   📁 2025: {img2_path}")
            
            # حساب التشابه
            similarity_data = self.calculate_combined_similarity(img1_path, img2_path)
            
            # طباعة النتائج
            print(f"   📊 النتائج:")
            print(f"      🏗️  SSIM: {similarity_data['ssim']:.3f} ({similarity_data['ssim']*100:.1f}%)")
            print(f"      🔍 Hash Combined: {similarity_data['hash_similarity']['combined']:.3f} ({similarity_data['hash_similarity']['combined']*100:.1f}%)")
            print(f"      🎨 Histogram: {similarity_data['histogram_similarity']:.3f} ({similarity_data['histogram_similarity']*100:.1f}%)")
            print(f"      ⭐ النتيجة النهائية: {similarity_data['combined_score']:.3f} ({similarity_data['combined_score']*100:.1f}%)")
            
            # تقييم النتيجة
            if similarity_data['combined_score'] >= 0.95:
                evaluation = "🟢 تطابق عالي جداً"
            elif similarity_data['combined_score'] >= 0.85:
                evaluation = "🟡 تطابق عالي"
            elif similarity_data['combined_score'] >= 0.70:
                evaluation = "🟠 تطابق متوسط"
            else:
                evaluation = "🔴 تطابق منخفض"
            
            print(f"      📈 التقييم: {evaluation}")
            
            # حفظ النتائج
            comparison_result = {
                'filename': filename,
                'image1_path': img1_path,
                'image2_path': img2_path,
                'similarities': similarity_data,
                'evaluation': evaluation
            }
            
            self.results['comparisons'].append(comparison_result)
    
    def generate_statistics(self):
        """إنشاء إحصائيات شاملة للنتائج"""
        if not self.results['comparisons']:
            return
        
        scores = [comp['similarities']['combined_score'] for comp in self.results['comparisons']]
        ssim_scores = [comp['similarities']['ssim'] for comp in self.results['comparisons']]
        hash_scores = [comp['similarities']['hash_similarity']['combined'] for comp in self.results['comparisons']]
        hist_scores = [comp['similarities']['histogram_similarity'] for comp in self.results['comparisons']]
        
        self.results['statistics'] = {
            'total_comparisons': len(scores),
            'combined_scores': {
                'average': np.mean(scores),
                'median': np.median(scores),
                'min': np.min(scores),
                'max': np.max(scores),
                'std': np.std(scores)
            },
            'ssim_scores': {
                'average': np.mean(ssim_scores),
                'median': np.median(ssim_scores)
            },
            'hash_scores': {
                'average': np.mean(hash_scores),
                'median': np.median(hash_scores)
            },
            'histogram_scores': {
                'average': np.mean(hist_scores),
                'median': np.median(hist_scores)
            },
            'high_similarity_count': len([s for s in scores if s >= 0.85]),
            'medium_similarity_count': len([s for s in scores if 0.70 <= s < 0.85]),
            'low_similarity_count': len([s for s in scores if s < 0.70])
        }
    
    def print_statistics(self):
        """طباعة الإحصائيات"""
        stats = self.results['statistics']
        
        print("\n" + "="*60)
        print("📊 إحصائيات شاملة للتشابه البصري")
        print("="*60)
        
        print(f"📋 عدد المقارنات الإجمالي: {stats['total_comparisons']}")
        print(f"📈 متوسط التشابه: {stats['combined_scores']['average']:.3f} ({stats['combined_scores']['average']*100:.1f}%)")
        print(f"📊 الوسيط: {stats['combined_scores']['median']:.3f} ({stats['combined_scores']['median']*100:.1f}%)")
        print(f"⬇️  أقل تشابه: {stats['combined_scores']['min']:.3f} ({stats['combined_scores']['min']*100:.1f}%)")
        print(f"⬆️  أعلى تشابه: {stats['combined_scores']['max']:.3f} ({stats['combined_scores']['max']*100:.1f}%)")
        print(f"📏 الانحراف المعياري: {stats['combined_scores']['std']:.3f}")
        
        print("\n🎯 توزيع النتائج:")
        print(f"   🟢 تشابه عالي (≥85%): {stats['high_similarity_count']} صورة")
        print(f"   🟡 تشابه متوسط (70-84%): {stats['medium_similarity_count']} صورة")
        print(f"   🔴 تشابه منخفض (<70%): {stats['low_similarity_count']} صورة")
        
        print("\n🔍 تفاصيل المقاييس:")
        print(f"   🏗️  متوسط SSIM: {stats['ssim_scores']['average']:.3f}")
        print(f"   🔍 متوسط Hash: {stats['hash_scores']['average']:.3f}")
        print(f"   🎨 متوسط Histogram: {stats['histogram_scores']['average']:.3f}")
    
    def save_results(self, output_path="visual_similarity_test_results.json"):
        """حفظ النتائج في ملف JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 تم حفظ النتائج في: {output_path}")
    
    def create_visualization(self, output_path="similarity_distribution.png"):
        """إنشاء رسم بياني لتوزيع النتائج"""
        if not self.results['comparisons']:
            return
        
        scores = [comp['similarities']['combined_score'] for comp in self.results['comparisons']]
        filenames = [comp['filename'] for comp in self.results['comparisons']]
        
        plt.figure(figsize=(12, 8))
        
        # رسم بياني للتوزيع
        plt.subplot(2, 1, 1)
        plt.hist(scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('توزيع درجات التشابه البصري', fontsize=14)
        plt.xlabel('درجة التشابه')
        plt.ylabel('عدد الصور')
        plt.grid(True, alpha=0.3)
        
        # رسم بياني للنتائج الفردية
        plt.subplot(2, 1, 2)
        colors = ['green' if s >= 0.85 else 'orange' if s >= 0.70 else 'red' for s in scores]
        plt.bar(range(len(scores)), scores, color=colors, alpha=0.7)
        plt.title('درجات التشابه لكل صورة', fontsize=14)
        plt.xlabel('الصور')
        plt.ylabel('درجة التشابه')
        plt.xticks(range(len(filenames)), filenames, rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📈 تم حفظ الرسم البياني في: {output_path}")
        plt.show()

def main():
    """الدالة الرئيسية للاختبار"""
    print("🚀 بدء اختبار التشابه البصري للمناهج التعليمية")
    print("="*60)
    
    # مسارات المجلدات
    test_folder = Path(__file__).parent / "test"
    folder_2024 = test_folder / "2024"
    folder_2025 = test_folder / "2025"
    
    # التحقق من وجود المجلدات
    if not folder_2024.exists():
        print(f"❌ المجلد غير موجود: {folder_2024}")
        return
    
    if not folder_2025.exists():
        print(f"❌ المجلد غير موجود: {folder_2025}")
        return
    
    # إنشاء كائن الاختبار
    tester = VisualSimilarityTester()
    
    # تشغيل المقارنات
    tester.compare_folders(folder_2024, folder_2025)
    
    # إنشاء الإحصائيات
    tester.generate_statistics()
    
    # طباعة النتائج
    tester.print_statistics()
    
    # حفظ النتائج
    tester.save_results("backend/visual_similarity_test_results.json")
    
    # إنشاء الرسم البياني
    tester.create_visualization("backend/similarity_distribution.png")
    
    print("\n✅ تم الانتهاء من اختبار التشابه البصري بنجاح!")

if __name__ == "__main__":
    main() 