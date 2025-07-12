#!/usr/bin/env python3
"""
اختبار المقارنة البصرية مع عرض الاختلافات
Visual Comparison Test with Difference Visualization
"""

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os
from datetime import datetime

def create_difference_map(img1_path, img2_path, output_path=None):
    """إنشاء خريطة الاختلافات بين الصورتين"""
    
    # قراءة الصور
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    
    # تحويل إلى اللون الرمادي
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # تغيير الحجم ليكون نفس الحجم
    height = min(gray1.shape[0], gray2.shape[0])
    width = min(gray1.shape[1], gray2.shape[1])
    
    gray1_resized = cv2.resize(gray1, (width, height))
    gray2_resized = cv2.resize(gray2, (width, height))
    img1_resized = cv2.resize(img1, (width, height))
    img2_resized = cv2.resize(img2, (width, height))
    
    # حساب SSIM مع خريطة الاختلافات
    ssim_score, diff = ssim(gray1_resized, gray2_resized, full=True)
    
    # تحويل خريطة الاختلافات إلى صورة
    diff = (diff * 255).astype("uint8")
    
    # إنشاء قناع للمناطق المختلفة
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    
    # العثور على الكونتورات (المناطق المختلفة)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # رسم المناطق المختلفة على الصور
    img1_marked = img1_resized.copy()
    img2_marked = img2_resized.copy()
    
    changed_regions = []
    total_changed_area = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # تجاهل المناطق الصغيرة جداً
            x, y, w, h = cv2.boundingRect(contour)
            
            # رسم مستطيل حول المنطقة المختلفة
            cv2.rectangle(img1_marked, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.rectangle(img2_marked, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            # إضافة نص يوضح رقم المنطقة
            cv2.putText(img1_marked, f"{len(changed_regions)+1}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(img2_marked, f"{len(changed_regions)+1}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            changed_regions.append({
                'id': len(changed_regions) + 1,
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h),
                'area': int(area),
                'center': {'x': int(x + w/2), 'y': int(y + h/2)}
            })
            total_changed_area += area
    
    # حساب نسبة المنطقة المتغيرة
    total_area = height * width
    change_percentage = (total_changed_area / total_area) * 100
    
    # دمج الصور للمقارنة
    comparison_img = np.hstack([img1_marked, img2_marked])
    
    # إضافة معلومات على الصورة
    info_text = f"SSIM: {ssim_score:.4f} | Changed: {change_percentage:.2f}% | Regions: {len(changed_regions)}"
    cv2.putText(comparison_img, info_text, (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(comparison_img, "Original", (10, height-20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(comparison_img, "Modified", (width + 10, height-20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # حفظ الصورة المدمجة
    if output_path:
        cv2.imwrite(output_path, comparison_img)
        print(f"💾 تم حفظ صورة المقارنة في: {output_path}")
    
    return {
        'ssim_score': ssim_score,
        'changed_regions': changed_regions,
        'change_percentage': change_percentage,
        'total_changed_area': total_changed_area,
        'total_area': total_area,
        'comparison_image': comparison_img,
        'image_size': (width, height)
    }

def analyze_differences():
    """تحليل الاختلافات بين الصورتين"""
    
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
    
    print("🔍 تحليل الاختلافات البصرية...")
    print(f"📁 الصورة القديمة: {os.path.basename(old_image_path)}")
    print(f"📁 الصورة الجديدة: {os.path.basename(new_image_path)}")
    print("=" * 70)
    
    start_time = datetime.now()
    
    try:
        # إنشاء اسم ملف للنتيجة
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"difference_analysis_{timestamp}.jpg"
        
        # تحليل الاختلافات
        result = create_difference_map(old_image_path, new_image_path, output_path)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("📊 نتائج تحليل الاختلافات:")
        print(f"🎯 SSIM Score: {result['ssim_score']:.4f}")
        print(f"📏 حجم الصورة: {result['image_size'][0]} x {result['image_size'][1]}")
        print(f"📊 المساحة الكلية: {result['total_area']:,} بكسل")
        print(f"🔄 المساحة المتغيرة: {result['total_changed_area']:,} بكسل")
        print(f"📈 نسبة التغيير: {result['change_percentage']:.2f}%")
        print(f"🔍 عدد المناطق المتغيرة: {len(result['changed_regions'])}")
        print(f"⏱️  وقت المعالجة: {duration:.2f} ثانية")
        
        if result['changed_regions']:
            print("\n🔍 تفاصيل المناطق المتغيرة:")
            print("-" * 50)
            
            # ترتيب المناطق حسب الحجم (الأكبر أولاً)
            sorted_regions = sorted(result['changed_regions'], 
                                   key=lambda x: x['area'], reverse=True)
            
            for i, region in enumerate(sorted_regions[:10], 1):  # عرض أول 10 مناطق
                print(f"المنطقة {region['id']}:")
                print(f"  📍 الموقع: ({region['x']}, {region['y']})")
                print(f"  📏 الحجم: {region['width']} x {region['height']}")
                print(f"  📊 المساحة: {region['area']:,} بكسل")
                print(f"  🎯 المركز: ({region['center']['x']}, {region['center']['y']})")
                
                # حساب النسبة المئوية لهذه المنطقة
                region_percentage = (region['area'] / result['total_area']) * 100
                print(f"  📈 النسبة من الصورة: {region_percentage:.3f}%")
                
                if i < len(sorted_regions):
                    print()
        
        print("=" * 70)
        print("📋 التحليل:")
        
        if result['change_percentage'] < 0.1:
            print("✅ تغييرات طفيفة جداً (أقل من 0.1%)")
            print("   - قد تكون ضوضاء أو تغييرات في الجودة")
        elif result['change_percentage'] < 1:
            print("🔶 تغييرات طفيفة (أقل من 1%)")
            print("   - تغييرات صغيرة في النص أو التفاصيل")
        elif result['change_percentage'] < 5:
            print("🔸 تغييرات متوسطة (1-5%)")
            print("   - تغييرات ملحوظة في المحتوى")
        else:
            print("🔴 تغييرات كبيرة (أكثر من 5%)")
            print("   - تغييرات جوهرية في المحتوى")
        
        if result['ssim_score'] > 0.95:
            print(f"✅ التشابه الهيكلي ممتاز ({result['ssim_score']:.4f})")
        elif result['ssim_score'] > 0.8:
            print(f"🔶 التشابه الهيكلي جيد ({result['ssim_score']:.4f})")
        else:
            print(f"🔴 التشابه الهيكلي ضعيف ({result['ssim_score']:.4f})")
        
        print(f"\n💡 تم حفظ صورة المقارنة مع المناطق المتغيرة في: {output_path}")
        print("   يمكنك فتح الصورة لرؤية المناطق المتغيرة محددة باللون الأحمر")
        
    except Exception as e:
        print(f"❌ خطأ في التحليل: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 تحليل الاختلافات البصرية مع العرض المرئي")
    print("=" * 70)
    analyze_differences()
