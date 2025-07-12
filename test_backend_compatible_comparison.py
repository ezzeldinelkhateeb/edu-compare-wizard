#!/usr/bin/env python3
"""
اختبار المقارنة البصرية المحسن مع مقارنة النتائج مع الباك إند
Enhanced Visual Comparison Test with Backend Results Validation
"""

import cv2
import numpy as np
import imagehash
from PIL import Image, ImageEnhance, ImageOps
from skimage.metrics import structural_similarity as ssim
import json
import time
import requests
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import base64
from datetime import datetime

class EnhancedVisualComparisonTester:
    """فئة اختبار المقارنة البصرية المحسنة مع مقارنة النتائج مع الباك إند"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        # أوزان المقارنة المحسنة (مطابقة للباك إند)
        self.weights = {
            'ssim': 0.25,
            'phash': 0.15,
            'clip': 0.25,  # سيتم تعطيله في الاختبار المحلي
            'histogram': 0.10,
            'features': 0.15,
            'edges': 0.10
        }
        
        # إعادة توزيع الأوزان بدون CLIP
        remaining_weight = 1.0 - self.weights['clip']
        factor = 1.0 / remaining_weight
        for key in ['ssim', 'phash', 'histogram', 'features', 'edges']:
            self.weights[key] *= factor
        self.weights['clip'] = 0.0
        
        self.backend_url = backend_url
        self.similarity_threshold = 0.75
        self.high_similarity_threshold = 0.90
        
        # إعداد SIFT للميزات
        try:
            self.sift = cv2.SIFT_create(nfeatures=1000)
            self.feature_matching_available = True
        except Exception:
            self.feature_matching_available = False
            
        print(f"🔧 أوزان المقارنة المحسنة:")
        for key, value in self.weights.items():
            print(f"   {key.upper()}: {value:.2f}")
    
    def load_and_preprocess_image(self, image_path: str) -> Dict[str, Any]:
        """تحميل ومعالجة الصورة (مطابق للباك إند)"""
        try:
            # تحميل مع OpenCV
            img_cv = cv2.imread(str(image_path))
            if img_cv is None:
                raise ValueError(f"فشل في قراءة الصورة: {image_path}")
            
            # تحويل إلى RGB
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            
            # تحميل مع PIL
            img_pil = Image.open(image_path)
            
            # إنشاء نسخة رمادية مع تحسين (مطابق للباك إند)
            img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            img_gray = cv2.GaussianBlur(img_gray, (3, 3), 0)  # تحسين الجودة
            
            return {
                'cv': img_cv,
                'rgb': img_rgb,
                'pil': img_pil,
                'gray': img_gray,
                'shape': img_cv.shape,
                'size': img_pil.size
            }
        except Exception as e:
            print(f"❌ خطأ في تحميل {image_path}: {e}")
            return None
    
    def resize_images_to_match(self, img1: Dict, img2: Dict) -> Tuple[Dict, Dict]:
        """تغيير حجم الصور لتتطابق (مطابق للباك إند)"""
        h1, w1 = img1['gray'].shape
        h2, w2 = img2['gray'].shape
        
        # استخدام أصغر حجم مشترك (مطابق للباك إند)
        target_h = min(h1, h2)
        target_w = min(w1, w2)
        
        def resize_image_dict(img_dict, target_size):
            result = {}
            for key, img in img_dict.items():
                if key in ['shape', 'size']:
                    continue
                elif key == 'pil':
                    result[key] = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                elif len(img.shape) == 2:  # grayscale
                    result[key] = cv2.resize(img, (target_w, target_h))
                else:  # color
                    result[key] = cv2.resize(img, (target_w, target_h))
            
            result['shape'] = (target_h, target_w, 3)
            result['size'] = (target_w, target_h)
            return result
        
        img1_resized = resize_image_dict(img1, (target_w, target_h))
        img2_resized = resize_image_dict(img2, (target_w, target_h))
        
        return img1_resized, img2_resized
    
    def calculate_ssim(self, img1_gray: np.ndarray, img2_gray: np.ndarray) -> Dict[str, Any]:
        """حساب SSIM (مطابق للباك إند)"""
        try:
            # حساب SSIM مع full=True للحصول على الخريطة
            score, ssim_map = ssim(img1_gray, img2_gray, full=True)
            score = max(0.0, min(1.0, score))  # تأكد من أن النتيجة بين 0 و 1
            
            return {
                'score': float(score),
                'map_available': True,
                'mean_map': float(np.mean(ssim_map)),
                'std_map': float(np.std(ssim_map)),
                'min_map': float(np.min(ssim_map)),
                'max_map': float(np.max(ssim_map))
            }
        except Exception as e:
            print(f"❌ خطأ في حساب SSIM: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def calculate_phash_similarity(self, img1_pil: Image.Image, img2_pil: Image.Image) -> Dict[str, Any]:
        """حساب تشابه pHash (مطابق للباك إند)"""
        try:
            # حساب pHash
            hash1 = imagehash.phash(img1_pil)
            hash2 = imagehash.phash(img2_pil)
            
            # حساب المسافة والتحويل إلى تشابه
            distance = hash1 - hash2
            max_distance = 64  # الحد الأقصى لمسافة pHash
            similarity = 1.0 - (distance / max_distance)
            similarity = max(0.0, min(1.0, similarity))
            
            return {
                'score': float(similarity),
                'hash1': str(hash1),
                'hash2': str(hash2),
                'distance': int(distance),
                'max_distance': max_distance
            }
        except Exception as e:
            print(f"❌ خطأ في حساب pHash: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def calculate_histogram_correlation(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """حساب ارتباط الهستوجرام (مطابق للباك إند)"""
        try:
            # تحويل إلى grayscale إذا لزم الأمر
            gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY) if len(img1.shape) == 3 else img1
            gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY) if len(img2.shape) == 3 else img2
            
            # تحويل الصور إلى هستوجرام
            hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
            
            # حساب ارتباط الهستوجرام
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            correlation = max(0.0, min(1.0, correlation))
            
            return {
                'score': float(correlation),
                'method': 'HISTCMP_CORREL',
                'hist1_mean': float(np.mean(hist1)),
                'hist2_mean': float(np.mean(hist2))
            }
        except Exception as e:
            print(f"❌ خطأ في حساب ارتباط الهستوجرام: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def calculate_feature_matching(self, img1_gray: np.ndarray, img2_gray: np.ndarray) -> Dict[str, Any]:
        """حساب تطابق الميزات (مطابق للباك إند)"""
        if not self.feature_matching_available:
            return {'score': 0.0, 'error': 'SIFT not available'}
        
        try:
            # إنشاء كاشف SIFT
            kp1, des1 = self.sift.detectAndCompute(img1_gray, None)
            kp2, des2 = self.sift.detectAndCompute(img2_gray, None)
            
            if des1 is None or des2 is None:
                return {
                    'score': 0.0,
                    'keypoints1': len(kp1) if kp1 else 0,
                    'keypoints2': len(kp2) if kp2 else 0,
                    'error': 'No descriptors found'
                }
            
            # حساب تطابق الميزات
            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
            matches = bf.match(des1, des2)
            
            # حساب متوسط المسافة بين الميزات المتطابقة (مطابق للباك إند)
            if len(matches) > 0:
                distances = [m.distance for m in matches]
                feature_matching_score = 1.0 - (np.mean(distances) / 256.0)
                feature_matching_score = max(0.0, min(1.0, feature_matching_score))
            else:
                feature_matching_score = 0.0
            
            return {
                'score': float(feature_matching_score),
                'total_matches': len(matches),
                'keypoints1': len(kp1),
                'keypoints2': len(kp2),
                'avg_distance': float(np.mean(distances) if matches else 0),
                'min_distance': float(np.min(distances) if matches else 0),
                'max_distance': float(np.max(distances) if matches else 0)
            }
        except Exception as e:
            print(f"❌ خطأ في حساب تطابق الميزات: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def calculate_edge_similarity(self, img1_gray: np.ndarray, img2_gray: np.ndarray) -> Dict[str, Any]:
        """حساب تشابه الحواف (مطابق للباك إند)"""
        try:
            # استخراج الحواف باستخدام Canny
            edges1 = cv2.Canny(img1_gray, 100, 200)
            edges2 = cv2.Canny(img2_gray, 100, 200)
            
            # حساب تشابه الحواف باستخدام matchShapes (مطابق للباك إند)
            similarity = cv2.matchShapes(edges1, edges2, cv2.CONTOURS_MATCH_I2, 0)
            similarity = max(0.0, min(1.0, similarity))
            
            return {
                'score': float(similarity),
                'edges1_pixels': int(np.sum(edges1 > 0)),
                'edges2_pixels': int(np.sum(edges2 > 0)),
                'method': 'CONTOURS_MATCH_I2'
            }
        except Exception as e:
            print(f"❌ خطأ في حساب تشابه الحواف: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def run_comprehensive_comparison(self, image1_path: str, image2_path: str) -> Dict[str, Any]:
        """تشغيل مقارنة شاملة بين صورتين (محسن)"""
        start_time = time.time()
        
        print("🔍 بدء المقارنة البصرية الشاملة المحسنة...")
        print(f"📷 الصورة الأولى: {image1_path}")
        print(f"📷 الصورة الثانية: {image2_path}")
        print("-" * 70)
        
        # تحميل الصور
        img1 = self.load_and_preprocess_image(image1_path)
        img2 = self.load_and_preprocess_image(image2_path)
        
        if not img1 or not img2:
            return None
        
        print(f"📐 حجم الصورة الأولى: {img1['shape']}")
        print(f"📐 حجم الصورة الثانية: {img2['shape']}")
        
        # تغيير الحجم للتطابق
        img1_resized, img2_resized = self.resize_images_to_match(img1, img2)
        print(f"📐 الحجم المستخدم للمقارنة: {img1_resized['shape']}")
        print("-" * 70)
        
        # إجراء جميع المقارنات
        results = {}
        
        print("🔬 حساب SSIM...")
        results['ssim'] = self.calculate_ssim(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ SSIM Score: {results['ssim']['score']:.4f}")
        
        print("🔬 حساب Perceptual Hash...")
        results['phash'] = self.calculate_phash_similarity(img1_resized['pil'], img2_resized['pil'])
        print(f"   ✅ pHash Score: {results['phash']['score']:.4f}")
        
        print("🔬 حساب ارتباط الهستوجرام...")
        results['histogram'] = self.calculate_histogram_correlation(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ Histogram Correlation: {results['histogram']['score']:.4f}")
        
        print("🔬 مطابقة الميزات...")
        results['features'] = self.calculate_feature_matching(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ Feature Matching Score: {results['features']['score']:.4f}")
        
        print("🔬 حساب تشابه الحواف...")
        results['edges'] = self.calculate_edge_similarity(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ Edge Similarity Score: {results['edges']['score']:.4f}")
        
        # حساب النتيجة الإجمالية (مطابق للباك إند)
        overall_score = (
            results['ssim']['score'] * self.weights['ssim'] +
            results['phash']['score'] * self.weights['phash'] +
            results['histogram']['score'] * self.weights['histogram'] +
            results['features']['score'] * self.weights['features'] +
            results['edges']['score'] * self.weights['edges']
        ) * 100
        
        processing_time = time.time() - start_time
        
        # تجميع النتائج النهائية
        final_results = {
            'overall_score': overall_score,
            'processing_time': processing_time,
            'detailed_scores': results,
            'weights_used': self.weights,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return final_results

def main():
    """الدالة الرئيسية للاختبار المحسن"""
    # مسارات الصور
    image1_path = Path("104.jpg")
    image2_path = Path("101.jpg")
    
    # التحقق من وجود الصور
    if not image1_path.exists():
        print(f"❌ الصورة غير موجودة: {image1_path}")
        return
    
    if not image2_path.exists():
        print(f"❌ الصورة غير موجودة: {image2_path}")
        return
    
    # إنشاء مُختبر المقارنة المحسن
    tester = EnhancedVisualComparisonTester()
    
    # تشغيل المقارنة المحلية
    print("🔬 تشغيل المقارنة المحلية...")
    local_results = tester.run_comprehensive_comparison(str(image1_path), str(image2_path))
    
    if local_results:
        print("\n" + "=" * 80)
        print("📊 النتائج المحلية المحسنة")
        print("=" * 80)
        print(f"🎯 النتيجة الإجمالية: {local_results['overall_score']:.2f}%")
        print(f"⏱️ وقت المعالجة: {local_results['processing_time']:.2f} ثانية")
        
        # عرض تحليل المقاييس التفصيلي
        details = local_results['detailed_scores']
        print(f"\n🔍 تحليل المقاييس التفصيلي:")
        print(f"   📊 SSIM: {details['ssim']['score']:.4f}")
        print(f"   🔐 pHash: {details['phash']['score']:.4f}")
        print(f"   📈 Histogram: {details['histogram']['score']:.4f}")
        print(f"   🎯 Features: {details['features']['score']:.4f}")
        print(f"   📐 Edges: {details['edges']['score']:.4f}")
        
        # حفظ النتائج التفصيلية
        output_file = f"enhanced_backend_compatible_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(local_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ النتائج التفصيلية في: {output_file}")

if __name__ == "__main__":
    main()
