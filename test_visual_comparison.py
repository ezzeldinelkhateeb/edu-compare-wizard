#!/usr/bin/env python3
"""
اختبار المقارنة البصرية بالتفصيل
Test script for detailed visual comparison between two images
"""

import cv2
import numpy as np
import imagehash
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from skimage.feature import match_descriptors, ORB
import json
import time
from pathlib import Path

class VisualComparisonTester:
    """فئة اختبار المقارنة البصرية مع التفاصيل الكاملة"""
    
    def __init__(self):
        # أوزان المقارنة (نفس الأوزان المستخدمة في الباك إند)
        self.weights = {
            'ssim': 0.33,
            'phash': 0.20,
            'clip': 0.00,  # غير متاح في هذا الاختبار
            'histogram': 0.13,
            'features': 0.20,
            'edges': 0.13
        }
        
    def load_and_prepare_image(self, image_path):
        """تحميل وتحضير الصورة للمقارنة"""
        try:
            # تحميل مع OpenCV
            img_cv = cv2.imread(str(image_path))
            if img_cv is None:
                raise ValueError(f"لا يمكن تحميل الصورة: {image_path}")
            
            # تحويل إلى RGB
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            
            # تحميل مع PIL للـ hashing
            img_pil = Image.open(image_path)
            
            # إنشاء نسخة رمادية
            img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
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
    
    def resize_images_to_match(self, img1, img2):
        """تغيير حجم الصور لتتطابق"""
        h1, w1 = img1['gray'].shape
        h2, w2 = img2['gray'].shape
        
        # استخدام أصغر حجم مشترك
        target_h = min(h1, h2)
        target_w = min(w1, w2)
        
        # تغيير الحجم مع الحفاظ على النسبة
        def resize_image_dict(img_dict, target_size):
            result = {}
            for key, img in img_dict.items():
                if key in ['shape', 'size']:
                    continue
                elif key == 'pil':
                    result[key] = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                elif len(img.shape) == 2:  # grayscale
                    result[key] = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
                else:  # color
                    result[key] = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
            
            result['shape'] = (target_h, target_w, 3)
            result['size'] = (target_w, target_h)
            return result
        
        img1_resized = resize_image_dict(img1, (target_w, target_h))
        img2_resized = resize_image_dict(img2, (target_w, target_h))
        
        return img1_resized, img2_resized
    
    def calculate_ssim(self, img1_gray, img2_gray):
        """حساب SSIM (Structural Similarity Index)"""
        try:
            # تحويل إلى float32 للحساب الدقيق
            img1_float = img1_gray.astype(np.float32) / 255.0
            img2_float = img2_gray.astype(np.float32) / 255.0
            
            # حساب SSIM
            ssim_score, ssim_map = ssim(img1_float, img2_float, full=True, data_range=1.0)
            
            return {
                'score': float(ssim_score),
                'map_available': True,
                'mean_map': float(np.mean(ssim_map)),
                'std_map': float(np.std(ssim_map))
            }
        except Exception as e:
            print(f"❌ خطأ في حساب SSIM: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def calculate_phash(self, img1_pil, img2_pil):
        """حساب Perceptual Hash"""
        try:
            hash1 = imagehash.phash(img1_pil, hash_size=16)
            hash2 = imagehash.phash(img2_pil, hash_size=16)
            
            # حساب المسافة (أقل = أكثر تشابهاً)
            distance = hash1 - hash2
            max_distance = 16 * 16  # أقصى مسافة ممكنة
            similarity = 1.0 - (distance / max_distance)
            
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
    
    def calculate_histogram_correlation(self, img1_rgb, img2_rgb):
        """حساب ارتباط الهستوجرام"""
        try:
            # حساب هستوجرام لكل قناة لون
            hist1_r = cv2.calcHist([img1_rgb], [0], None, [256], [0, 256])
            hist1_g = cv2.calcHist([img1_rgb], [1], None, [256], [0, 256])
            hist1_b = cv2.calcHist([img1_rgb], [2], None, [256], [0, 256])
            
            hist2_r = cv2.calcHist([img2_rgb], [0], None, [256], [0, 256])
            hist2_g = cv2.calcHist([img2_rgb], [1], None, [256], [0, 256])
            hist2_b = cv2.calcHist([img2_rgb], [2], None, [256], [0, 256])
            
            # حساب الارتباط لكل قناة
            corr_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_CORREL)
            corr_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_CORREL)
            corr_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_CORREL)
            
            # المتوسط
            avg_correlation = (corr_r + corr_g + corr_b) / 3.0
            
            return {
                'score': float(avg_correlation),
                'r_channel': float(corr_r),
                'g_channel': float(corr_g),
                'b_channel': float(corr_b),
                'method': 'HISTCMP_CORREL'
            }
        except Exception as e:
            print(f"❌ خطأ في حساب الهستوجرام: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def calculate_feature_matching(self, img1_gray, img2_gray):
        """مطابقة الميزات باستخدام ORB"""
        try:
            # إنشاء detector ORB
            orb = cv2.ORB_create(nfeatures=1000)
            
            # استخراج النقاط المميزة والواصفات
            kp1, des1 = orb.detectAndCompute(img1_gray, None)
            kp2, des2 = orb.detectAndCompute(img2_gray, None)
            
            if des1 is None or des2 is None:
                return {
                    'score': 0.0,
                    'matches': 0,
                    'keypoints1': len(kp1) if kp1 else 0,
                    'keypoints2': len(kp2) if kp2 else 0,
                    'error': 'No descriptors found'
                }
            
            # مطابقة الميزات
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            
            # ترتيب المطابقات حسب المسافة
            matches = sorted(matches, key=lambda x: x.distance)
            
            # حساب نسبة المطابقة
            good_matches = [m for m in matches if m.distance < 50]  # threshold للمطابقات الجيدة
            max_possible_matches = min(len(kp1), len(kp2))
            
            if max_possible_matches > 0:
                similarity = len(good_matches) / max_possible_matches
            else:
                similarity = 0.0
            
            return {
                'score': float(min(similarity, 1.0)),  # تحديد أقصى 1.0
                'total_matches': len(matches),
                'good_matches': len(good_matches),
                'keypoints1': len(kp1),
                'keypoints2': len(kp2),
                'avg_distance': float(np.mean([m.distance for m in matches]) if matches else 0),
                'threshold': 50
            }
        except Exception as e:
            print(f"❌ خطأ في مطابقة الميزات: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def calculate_edge_similarity(self, img1_gray, img2_gray):
        """حساب تشابه الحواف"""
        try:
            # استخراج الحواف باستخدام Canny
            edges1 = cv2.Canny(img1_gray, 50, 150)
            edges2 = cv2.Canny(img2_gray, 50, 150)
            
            # حساب التطابق بين الحواف
            # طريقة 1: XOR للحواف
            xor_edges = cv2.bitwise_xor(edges1, edges2)
            total_edge_pixels = np.sum(edges1 > 0) + np.sum(edges2 > 0)
            different_pixels = np.sum(xor_edges > 0)
            
            if total_edge_pixels > 0:
                similarity_xor = 1.0 - (different_pixels / total_edge_pixels)
            else:
                similarity_xor = 1.0
            
            # طريقة 2: ارتباط الحواف
            if np.std(edges1) > 0 and np.std(edges2) > 0:
                correlation = np.corrcoef(edges1.flatten(), edges2.flatten())[0, 1]
                if np.isnan(correlation):
                    correlation = 0.0
            else:
                correlation = 1.0 if np.array_equal(edges1, edges2) else 0.0
            
            # متوسط الطريقتين
            final_score = (similarity_xor + abs(correlation)) / 2.0
            
            return {
                'score': float(final_score),
                'xor_similarity': float(similarity_xor),
                'correlation': float(correlation),
                'edges1_pixels': int(np.sum(edges1 > 0)),
                'edges2_pixels': int(np.sum(edges2 > 0)),
                'different_pixels': int(different_pixels)
            }
        except Exception as e:
            print(f"❌ خطأ في حساب تشابه الحواف: {e}")
            return {'score': 0.0, 'error': str(e)}
    
    def calculate_mse_psnr(self, img1_gray, img2_gray):
        """حساب MSE و PSNR"""
        try:
            # حساب MSE
            mse = np.mean((img1_gray.astype(np.float32) - img2_gray.astype(np.float32)) ** 2)
            
            # حساب PSNR
            if mse == 0:
                psnr = float('inf')
            else:
                max_pixel = 255.0
                psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
            
            return {
                'mse': float(mse),
                'psnr': float(psnr),
                'max_pixel': 255.0
            }
        except Exception as e:
            print(f"❌ خطأ في حساب MSE/PSNR: {e}")
            return {'mse': 0.0, 'psnr': 0.0, 'error': str(e)}
    
    def detect_changed_regions(self, img1_gray, img2_gray, threshold=30):
        """اكتشاف المناطق المتغيرة"""
        try:
            # حساب الفرق المطلق
            diff = cv2.absdiff(img1_gray, img2_gray)
            
            # تطبيق threshold
            _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
            
            # العثور على الكنتورات (المناطق المتغيرة)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # تصفية المناطق الصغيرة
            min_area = 100  # المساحة الدنيا للمنطقة المتغيرة
            significant_contours = [c for c in contours if cv2.contourArea(c) > min_area]
            
            changed_regions = []
            for i, contour in enumerate(significant_contours):
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                changed_regions.append({
                    'id': f'region_{i+1}',
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': float(area),
                    'center': {
                        'x': int(x + w/2),
                        'y': int(y + h/2)
                    }
                })
            
            # حساب إجمالي المساحة المتغيرة
            total_changed_area = sum(region['area'] for region in changed_regions)
            total_image_area = img1_gray.shape[0] * img1_gray.shape[1]
            change_percentage = (total_changed_area / total_image_area) * 100
            
            return {
                'regions': changed_regions,
                'total_regions': len(changed_regions),
                'total_changed_area': float(total_changed_area),
                'total_image_area': float(total_image_area),
                'change_percentage': float(change_percentage),
                'threshold_used': threshold
            }
        except Exception as e:
            print(f"❌ خطأ في اكتشاف المناطق المتغيرة: {e}")
            return {'regions': [], 'error': str(e)}
    
    def run_comprehensive_comparison(self, image1_path, image2_path):
        """تشغيل مقارنة شاملة بين صورتين"""
        start_time = time.time()
        
        print("🔍 بدء المقارنة البصرية الشاملة...")
        print(f"📷 الصورة الأولى: {image1_path}")
        print(f"📷 الصورة الثانية: {image2_path}")
        print("-" * 60)
        
        # تحميل الصور
        img1 = self.load_and_prepare_image(image1_path)
        img2 = self.load_and_prepare_image(image2_path)
        
        if not img1 or not img2:
            return None
        
        print(f"📐 حجم الصورة الأولى: {img1['shape']}")
        print(f"📐 حجم الصورة الثانية: {img2['shape']}")
        
        # تغيير الحجم للتطابق
        img1_resized, img2_resized = self.resize_images_to_match(img1, img2)
        print(f"📐 الحجم المستخدم للمقارنة: {img1_resized['shape']}")
        print("-" * 60)
        
        # إجراء جميع المقارنات
        results = {}
        
        print("🔬 حساب SSIM...")
        results['ssim'] = self.calculate_ssim(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ SSIM Score: {results['ssim']['score']:.4f}")
        
        print("🔬 حساب Perceptual Hash...")
        results['phash'] = self.calculate_phash(img1_resized['pil'], img2_resized['pil'])
        print(f"   ✅ pHash Score: {results['phash']['score']:.4f}")
        
        print("🔬 حساب ارتباط الهستوجرام...")
        results['histogram'] = self.calculate_histogram_correlation(img1_resized['rgb'], img2_resized['rgb'])
        print(f"   ✅ Histogram Correlation: {results['histogram']['score']:.4f}")
        
        print("🔬 مطابقة الميزات...")
        results['features'] = self.calculate_feature_matching(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ Feature Matching Score: {results['features']['score']:.4f}")
        
        print("🔬 حساب تشابه الحواف...")
        results['edges'] = self.calculate_edge_similarity(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ Edge Similarity Score: {results['edges']['score']:.4f}")
        
        print("🔬 حساب MSE و PSNR...")
        results['mse_psnr'] = self.calculate_mse_psnr(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ MSE: {results['mse_psnr']['mse']:.2f}, PSNR: {results['mse_psnr']['psnr']:.2f} dB")
        
        print("🔬 اكتشاف المناطق المتغيرة...")
        results['changed_regions'] = self.detect_changed_regions(img1_resized['gray'], img2_resized['gray'])
        print(f"   ✅ Found {results['changed_regions']['total_regions']} changed regions")
        
        # حساب النتيجة الإجمالية
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
            'image_info': {
                'image1_original_size': img1['shape'],
                'image2_original_size': img2['shape'],
                'comparison_size': img1_resized['shape']
            },
            'detailed_scores': results,
            'weights_used': self.weights,
            'analysis': self.generate_analysis(results, overall_score),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return final_results
    
    def generate_analysis(self, results, overall_score):
        """تحليل النتائج وتوليد التوصيات"""
        analysis = {
            'similarity_level': '',
            'major_differences': False,
            'content_type_detected': 'educational_document',
            'recommendations': [],
            'confidence_notes': [],
            'summary': ''
        }
        
        # تحديد مستوى التشابه
        if overall_score >= 95:
            analysis['similarity_level'] = 'متطابق تقريباً'
        elif overall_score >= 85:
            analysis['similarity_level'] = 'متشابه جداً'
        elif overall_score >= 70:
            analysis['similarity_level'] = 'متشابه'
        elif overall_score >= 50:
            analysis['similarity_level'] = 'اختلافات متوسطة'
        else:
            analysis['similarity_level'] = 'مختلف بشكل كبير'
        
        # اكتشاف التغييرات الكبيرة
        changed_percentage = results['changed_regions'].get('change_percentage', 0)
        if changed_percentage > 10:
            analysis['major_differences'] = True
        
        # توليد التوصيات
        if results['ssim']['score'] < 0.8:
            analysis['recommendations'].append('هناك اختلافات هيكلية ملحوظة بين الصور')
        
        if results['phash']['score'] < 0.9:
            analysis['recommendations'].append('الصور تحتوي على اختلافات في المحتوى البصري')
        
        if results['features']['good_matches'] < 50:
            analysis['recommendations'].append('عدد النقاط المتطابقة قليل - قد تكون صور مختلفة')
        
        if changed_percentage > 5:
            analysis['recommendations'].append(f'تم اكتشاف {changed_percentage:.1f}% من المساحة متغيرة')
        
        # ملاحظات الثقة
        if results['features']['keypoints1'] < 100 or results['features']['keypoints2'] < 100:
            analysis['confidence_notes'].append('عدد النقاط المميزة قليل - قد يؤثر على دقة المقارنة')
        
        if results['mse_psnr']['mse'] > 1000:
            analysis['confidence_notes'].append('MSE مرتفع - يشير إلى اختلافات كبيرة في البكسل')
        
        # الملخص
        analysis['summary'] = f"النتيجة الإجمالية {overall_score:.1f}% تشير إلى {analysis['similarity_level']}. تم اكتشاف {results['changed_regions']['total_regions']} منطقة متغيرة."
        
        return analysis

def main():
    """الدالة الرئيسية للاختبار"""
    # مسارات الصور
    image1_path = Path("D:/ezz/compair/edu-compare-wizard/104.jpg")
    image2_path = Path("D:/ezz/compair/edu-compare-wizard/101.jpg")
    
    # التحقق من وجود الصور
    if not image1_path.exists():
        print(f"❌ الصورة غير موجودة: {image1_path}")
        return
    
    if not image2_path.exists():
        print(f"❌ الصورة غير موجودة: {image2_path}")
        return
    
    # إنشاء مُختبر المقارنة
    tester = VisualComparisonTester()
    
    # تشغيل المقارنة
    results = tester.run_comprehensive_comparison(image1_path, image2_path)
    
    if results:
        print("\n" + "=" * 60)
        print("📊 النتائج النهائية")
        print("=" * 60)
        print(f"🎯 النتيجة الإجمالية: {results['overall_score']:.2f}%")
        print(f"⏱️ وقت المعالجة: {results['processing_time']:.2f} ثانية")
        print(f"📝 التقييم: {results['analysis']['similarity_level']}")
        print(f"📄 الملخص: {results['analysis']['summary']}")
        
        if results['analysis']['recommendations']:
            print("\n💡 التوصيات:")
            for rec in results['analysis']['recommendations']:
                print(f"   • {rec}")
        
        if results['analysis']['confidence_notes']:
            print("\n⚠️ ملاحظات الثقة:")
            for note in results['analysis']['confidence_notes']:
                print(f"   • {note}")
        
        # حفظ النتائج التفصيلية
        output_file = "detailed_comparison_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ النتائج التفصيلية في: {output_file}")
        
        # عرض التفاصيل المهمة
        print("\n🔍 تفاصيل النتائج:")
        print("-" * 40)
        details = results['detailed_scores']
        print(f"SSIM: {details['ssim']['score']:.4f}")
        print(f"pHash: {details['phash']['score']:.4f} (distance: {details['phash']['distance']})")
        print(f"Histogram: {details['histogram']['score']:.4f}")
        print(f"Features: {details['features']['score']:.4f} ({details['features']['good_matches']} good matches)")
        print(f"Edges: {details['edges']['score']:.4f}")
        print(f"MSE: {details['mse_psnr']['mse']:.2f}")
        print(f"PSNR: {details['mse_psnr']['psnr']:.2f} dB")
        print(f"Changed Regions: {details['changed_regions']['total_regions']} ({details['changed_regions']['change_percentage']:.1f}% area)")

if __name__ == "__main__":
    main()
