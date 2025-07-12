#!/usr/bin/env python3
"""
اختبار قدرة المقارنة البصرية على كشف تغييرات النصوص
Test Visual Similarity's Ability to Detect Text Content Changes
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path
import os
from datetime import datetime

class TextChangeDetectionTester:
    def __init__(self):
        self.results = []
        self.test_images_dir = Path("text_change_test_images")
        self.test_images_dir.mkdir(exist_ok=True)
        
    def create_test_image(self, text_content, filename, font_size=40):
        """إنشاء صورة اختبار بنص محدد"""
        # إعدادات الصورة
        width, height = 800, 600
        background_color = (255, 255, 255)  # أبيض
        text_color = (0, 0, 0)  # أسود
        
        # إنشاء الصورة
        image = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(image)
        
        # محاولة استخدام خط عربي، أو الافتراضي
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # إضافة عنوان ثابت
        title = "اختبار كشف تغييرات النص"
        draw.text((50, 50), title, fill=text_color, font=font)
        
        # إضافة خط فاصل
        draw.line([(50, 100), (750, 100)], fill=(200, 200, 200), width=2)
        
        # إضافة النص المتغير
        y_position = 150
        lines = text_content.split('\n')
        for line in lines:
            draw.text((50, y_position), line, fill=text_color, font=font)
            y_position += font_size + 10
        
        # إضافة إطار ثابت
        draw.rectangle([(30, 30), (770, 570)], outline=(100, 100, 100), width=3)
        
        # حفظ الصورة
        image_path = self.test_images_dir / filename
        image.save(image_path)
        return str(image_path)
    
    def calculate_visual_similarity(self, img1_path, img2_path):
        """حساب التشابه البصري بين صورتين"""
        try:
            # قراءة الصور
            img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
            
            if img1 is None or img2 is None:
                return {"error": "فشل في قراءة الصور"}
            
            # توحيد الأبعاد
            height = min(img1.shape[0], img2.shape[0])
            width = min(img1.shape[1], img2.shape[1])
            
            img1_resized = cv2.resize(img1, (width, height))
            img2_resized = cv2.resize(img2, (width, height))
            
            # 1. حساب MSE و PSNR
            mse = np.mean((img1_resized - img2_resized) ** 2)
            if mse == 0:
                psnr_similarity = 1.0
            else:
                psnr = 20 * np.log10(255.0 / np.sqrt(mse))
                psnr_similarity = min(1.0, psnr / 50.0)
            
            # 2. حساب Structural Similarity (مبسط)
            # حساب المتوسط والانحراف المعياري
            mu1 = np.mean(img1_resized)
            mu2 = np.mean(img2_resized)
            sigma1 = np.std(img1_resized)
            sigma2 = np.std(img2_resized)
            sigma12 = np.mean((img1_resized - mu1) * (img2_resized - mu2))
            
            # ثوابت SSIM
            c1 = (0.01 * 255) ** 2
            c2 = (0.03 * 255) ** 2
            
            ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / ((mu1**2 + mu2**2 + c1) * (sigma1**2 + sigma2**2 + c2))
            ssim_similarity = (ssim + 1) / 2  # تحويل من [-1,1] إلى [0,1]
            
            # 3. حساب Histogram Similarity
            hist1 = cv2.calcHist([img1_resized], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([img2_resized], [0], None, [256], [0, 256])
            hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # 4. حساب Pixel Difference Analysis
            diff_pixels = np.sum(img1_resized != img2_resized)
            total_pixels = img1_resized.shape[0] * img1_resized.shape[1]
            pixel_similarity = 1.0 - (diff_pixels / total_pixels)
            
            # 5. حساب Edge Detection Similarity
            edges1 = cv2.Canny(img1_resized, 50, 150)
            edges2 = cv2.Canny(img2_resized, 50, 150)
            edge_diff = np.sum(edges1 != edges2)
            edge_total = edges1.shape[0] * edges1.shape[1]
            edge_similarity = 1.0 - (edge_diff / edge_total)
            
            # الدرجة المركبة
            combined_similarity = (
                psnr_similarity * 0.25 +
                ssim_similarity * 0.30 +
                hist_similarity * 0.20 +
                pixel_similarity * 0.15 +
                edge_similarity * 0.10
            )
            
            return {
                "psnr_similarity": round(psnr_similarity, 4),
                "ssim_similarity": round(ssim_similarity, 4),
                "histogram_similarity": round(hist_similarity, 4),
                "pixel_similarity": round(pixel_similarity, 4),
                "edge_similarity": round(edge_similarity, 4),
                "combined_similarity": round(combined_similarity, 4),
                "mse": round(mse, 2),
                "different_pixels": diff_pixels,
                "total_pixels": total_pixels,
                "diff_percentage": round((diff_pixels / total_pixels) * 100, 2)
            }
            
        except Exception as e:
            return {"error": f"خطأ في الحساب: {str(e)}"}
    
    def run_text_change_tests(self):
        """تشغيل مجموعة من اختبارات تغيير النص"""
        print("🔍 بدء اختبار قدرة المقارنة البصرية على كشف تغييرات النصوص")
        print("="*70)
        
        # تعريف الاختبارات
        test_cases = [
            {
                "name": "نفس النص تماماً",
                "text1": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "text2": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "description": "نص متطابق 100% - يجب أن تكون النتيجة عالية جداً"
            },
            {
                "name": "تغيير كلمة واحدة",
                "text1": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "text2": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) دمياط",
                "description": "تغيير إجابة واحدة (الأقصر → دمياط)"
            },
            {
                "name": "تغيير رقم السؤال",
                "text1": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "text2": "السؤال الثاني: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "description": "تغيير رقم السؤال فقط (الأول → الثاني)"
            },
            {
                "name": "تغيير السؤال كاملاً",
                "text1": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "text2": "السؤال الأول: ما هو أكبر كوكب؟\nأ) الأرض\nب) المشتري\nج) زحل\nد) المريخ",
                "description": "تغيير السؤال والإجابات كاملاً"
            },
            {
                "name": "تغيير ترتيب الإجابات",
                "text1": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "text2": "السؤال الأول: ما هو عاصمة مصر؟\nأ) الإسكندرية\nب) القاهرة\nج) الأقصر\nد) أسوان",
                "description": "نفس الإجابات لكن ترتيب مختلف"
            },
            {
                "name": "إضافة سؤال جديد",
                "text1": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "text2": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر\n\nالسؤال الثاني: كم عدد القارات؟\nأ) 5\nب) 6\nج) 7\nد) 8",
                "description": "إضافة سؤال جديد للمحتوى الأصلي"
            },
            {
                "name": "حذف جزء من النص",
                "text1": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية\nج) أسوان\nد) الأقصر",
                "text2": "السؤال الأول: ما هو عاصمة مصر؟\nأ) القاهرة\nب) الإسكندرية",
                "description": "حذف إجابتين من الأصل"
            }
        ]
        
        # تشغيل الاختبارات
        for i, test_case in enumerate(test_cases):
            print(f"\n📋 اختبار {i+1}: {test_case['name']}")
            print(f"📝 الوصف: {test_case['description']}")
            
            # إنشاء الصور
            img1_path = self.create_test_image(test_case['text1'], f"test_{i+1}_original.png")
            img2_path = self.create_test_image(test_case['text2'], f"test_{i+1}_modified.png")
            
            # حساب التشابه
            similarity_result = self.calculate_visual_similarity(img1_path, img2_path)
            
            if "error" in similarity_result:
                print(f"❌ خطأ: {similarity_result['error']}")
                continue
            
            # طباعة النتائج
            print(f"📊 النتائج:")
            print(f"   🎯 التشابه المركب: {similarity_result['combined_similarity']:.3f} ({similarity_result['combined_similarity']*100:.1f}%)")
            print(f"   🏗️  PSNR: {similarity_result['psnr_similarity']:.3f} ({similarity_result['psnr_similarity']*100:.1f}%)")
            print(f"   📐 SSIM: {similarity_result['ssim_similarity']:.3f} ({similarity_result['ssim_similarity']*100:.1f}%)")
            print(f"   🎨 Histogram: {similarity_result['histogram_similarity']:.3f} ({similarity_result['histogram_similarity']*100:.1f}%)")
            print(f"   🔍 Pixels: {similarity_result['pixel_similarity']:.3f} ({similarity_result['pixel_similarity']*100:.1f}%)")
            print(f"   📏 Edges: {similarity_result['edge_similarity']:.3f} ({similarity_result['edge_similarity']*100:.1f}%)")
            print(f"   📊 MSE: {similarity_result['mse']}")
            print(f"   🔢 بكسل مختلف: {similarity_result['different_pixels']:,} / {similarity_result['total_pixels']:,} ({similarity_result['diff_percentage']}%)")
            
            # تقييم النتيجة
            combined_score = similarity_result['combined_similarity']
            if combined_score >= 0.95:
                evaluation = "🟢 تطابق عالي جداً - تغيير ضئيل جداً أو معدوم"
            elif combined_score >= 0.85:
                evaluation = "🟡 تطابق عالي - تغيير طفيف"
            elif combined_score >= 0.70:
                evaluation = "🟠 تطابق متوسط - تغيير واضح"
            elif combined_score >= 0.50:
                evaluation = "🔴 تطابق منخفض - تغيير كبير"
            else:
                evaluation = "⚫ تطابق ضعيف - تغيير جذري"
            
            print(f"   📈 التقييم: {evaluation}")
            
            # حفظ النتيجة
            result = {
                "test_name": test_case['name'],
                "description": test_case['description'],
                "similarity_metrics": similarity_result,
                "evaluation": evaluation,
                "images": {
                    "original": img1_path,
                    "modified": img2_path
                }
            }
            self.results.append(result)
        
        # ملخص النتائج
        self.print_summary()
        
        # حفظ النتائج
        self.save_results()
    
    def print_summary(self):
        """طباعة ملخص النتائج"""
        print("\n" + "="*70)
        print("📊 ملخص نتائج اختبار كشف تغييرات النصوص")
        print("="*70)
        
        scores = [r['similarity_metrics']['combined_similarity'] for r in self.results if 'similarity_metrics' in r]
        
        if not scores:
            print("❌ لا توجد نتائج صالحة للتحليل")
            return
        
        avg_score = np.mean(scores)
        max_score = np.max(scores)
        min_score = np.min(scores)
        
        print(f"📈 متوسط التشابه: {avg_score:.3f} ({avg_score*100:.1f}%)")
        print(f"⬆️  أعلى تشابه: {max_score:.3f} ({max_score*100:.1f}%)")
        print(f"⬇️  أقل تشابه: {min_score:.3f} ({min_score*100:.1f}%)")
        
        print(f"\n🎯 تحليل النتائج حسب نوع التغيير:")
        for result in self.results:
            if 'similarity_metrics' in result:
                score = result['similarity_metrics']['combined_similarity']
                print(f"   📝 {result['test_name']}: {score:.3f} ({score*100:.1f}%)")
        
        # تحليل قدرة الكشف
        print(f"\n🔍 تحليل قدرة كشف التغييرات:")
        
        # اختبارات التغيير الطفيف
        minor_changes = [r for r in self.results if any(keyword in r['test_name'] for keyword in ['كلمة واحدة', 'رقم السؤال', 'ترتيب'])]
        if minor_changes:
            minor_scores = [r['similarity_metrics']['combined_similarity'] for r in minor_changes]
            avg_minor = np.mean(minor_scores)
            print(f"   🟡 التغييرات الطفيفة: متوسط {avg_minor:.3f} ({avg_minor*100:.1f}%)")
        
        # اختبارات التغيير الكبير
        major_changes = [r for r in self.results if any(keyword in r['test_name'] for keyword in ['السؤال كاملاً', 'إضافة', 'حذف'])]
        if major_changes:
            major_scores = [r['similarity_metrics']['combined_similarity'] for r in major_changes]
            avg_major = np.mean(major_scores)
            print(f"   🔴 التغييرات الكبيرة: متوسط {avg_major:.3f} ({avg_major*100:.1f}%)")
        
        # خلاصة التقييم
        print(f"\n🎉 الخلاصة:")
        if avg_score >= 0.80:
            print("   ⚠️  المقارنة البصرية حساسة نسبياً لتغييرات النصوص")
            print("   💡 يُنصح بدمجها مع OCR للحصول على دقة أفضل")
        elif avg_score >= 0.60:
            print("   ✅ المقارنة البصرية تكشف التغييرات الكبيرة بشكل جيد")
            print("   ⚠️  قد تفوت التغييرات الطفيفة في النصوص")
        else:
            print("   ✅ المقارنة البصرية ممتازة في كشف تغييرات النصوص")
            print("   🎯 يمكن الاعتماد عليها كأداة أولية للكشف")
    
    def save_results(self):
        """حفظ النتائج في ملف JSON"""
        output_data = {
            "test_date": datetime.now().isoformat(),
            "test_type": "text_change_detection",
            "summary": {
                "total_tests": len(self.results),
                "average_similarity": np.mean([r['similarity_metrics']['combined_similarity'] for r in self.results if 'similarity_metrics' in r]) if self.results else 0
            },
            "detailed_results": self.results
        }
        
        output_path = Path("text_change_detection_results.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ النتائج في: {output_path}")
        print(f"📁 الصور المُنشأة في: {self.test_images_dir}/")

def main():
    """الدالة الرئيسية"""
    tester = TextChangeDetectionTester()
    tester.run_text_change_tests()

if __name__ == "__main__":
    main() 