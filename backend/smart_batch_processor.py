#!/usr/bin/env python3
"""
المعالج الجماعي الذكي للمقارنة بين صفحات المناهج التعليمية
Smart Batch Processor for Educational Content Comparison

يطبق "الخطة النهائية لسير العمل" الموثقة في الملف المرجعي
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import cv2
import numpy as np
import asyncio
import logging

# إضافة مسار المشروع للاستيراد
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# استيراد الخدمات
from backend.app.services.gemini_service import GeminiService
from backend.app.services.landing_ai_service import LandingAIService
from backend.app.services.text_optimizer import TextOptimizer
from backend.app.services.visual_comparison_service import EnhancedVisualComparisonService

logger = logging.getLogger(__name__)

class SmartBatchProcessor:
    """
    المعالج الجماعي الذكي - ينفذ النظام التدريجي للمقارنة
    """
    
    def __init__(self, old_dir, new_dir, max_workers=4, visual_threshold=0.95, processing_mode="landingai_gemini", session_id=None, status_callback=None):
        self.old_dir = Path(old_dir)
        self.new_dir = Path(new_dir)
        self.max_workers = max_workers
        self.visual_threshold = visual_threshold
        self.processing_mode = processing_mode  # "gemini_only" or "landingai_gemini"
        self.session_id = session_id
        self.status_callback = status_callback  # دالة لتحديث الحالة
        
        # إعداد الخدمات
        self.gemini_service = GeminiService()
        self.landingai_service = LandingAIService()
        self.text_optimizer = TextOptimizer()
        self.visual_service = EnhancedVisualComparisonService()
        
        # إضافة Gemini Vision Service للوضع المباشر
        if self.processing_mode == "gemini_only":
            try:
                from backend.app.services.gemini_vision_service import GeminiVisionService
                self.gemini_vision_service = GeminiVisionService()
                print(f"✅ تم تحميل Gemini Vision Service لوضع {self.processing_mode}")
            except ImportError as e:
                print(f"⚠️ فشل في تحميل Gemini Vision Service: {e}")
                self.gemini_vision_service = None
        else:
            self.gemini_vision_service = None
        
        print(f"🔧 تم تهيئة SmartBatchProcessor بوضع: {self.processing_mode}")
        
        # إحصائيات المعالجة
        # إضافة مفاتيح صديقة للـ Front-end لتفادي الحاجة للمواءمة اللاحقة
        self.stats = {
            # إجمالي الأزواج
            'total_pairs': 0,

            # المرحلة 1: تشابه بصري ≥ threshold (توقف مبكر)
            'visually_identical': 0,   # الاسم القديم (للتوافق)
            'stage_1_filtered': 0,     # الاسم الجديد المتوقع من الـ Front-end

            # المرحلة 2: تم استخراج النص لكن لم يُحلَّل عميقًا (غير مستخدمة في المحاكاة بعد)
            'stage_2_processed': 0,

            # المرحلة 3/4: تم التحليل العميق بالكامل
            'fully_analyzed': 0,       # الاسم القديم
            'stage_3_analyzed': 0,     # الاسم الجديد

            'failed': 0,
            'start_time': 0,
            'end_time': 0,
            'total_duration': 0
        }
        
        self.results = []
        self.current_file = None
        self.progress = 0

    def update_status(self, message, progress=None, current_file=None, stage_idx=None, stage_total=None, file_idx=None, file_total=None):
        """تحديث حالة المعالجة مع تقدم أدق"""
        # حساب التقدم بدقة: (عدد الملفات المكتملة + نسبة المرحلة الحالية للملف الجاري) / N
        if file_total and file_idx is not None and stage_idx is not None and stage_total:
            # مثال: لكل ملف 4 مراحل (0-3)
            progress = int(((file_idx + stage_idx / stage_total) / file_total) * 100)
            self.progress = progress
        elif progress is not None:
            self.progress = progress
        if current_file is not None:
            self.current_file = current_file
        
        status_update = {
            'session_id': self.session_id,
            'status': 'جاري المعالجة',
            'progress': self.progress,
            'current_file': self.current_file,
            'message': message,
            'stats': self.stats,
            'results': self.results
        }
        
        print(f"📊 تحديث الحالة: {message} ({self.progress}%)")
        # إرسال التحديث للفرونت إند إذا كانت الدالة متوفرة
        if self.status_callback:
            try:
                self.status_callback(status_update)
                print(f"✅ تم إرسال التحديث للفرونت إند")
            except Exception as e:
                print(f"⚠️ خطأ في إرسال تحديث الحالة: {e}")
        else:
            print(f"⚠️ لا توجد دالة callback لتحديث الحالة")
    
    def calculate_visual_similarity(self, img1_path, img2_path):
        """حساب التشابه البصري - المرحلة 1"""
        try:
            # استخدام الخدمة المحسنة للمقارنة البصرية
            result = asyncio.run(self.visual_service.compare_images(img1_path, img2_path))
            
            # إرجاع النتيجة المحسنة
            return result.similarity_score / 100.0  # تحويل من نسبة مئوية إلى عشري
            
        except Exception as e:
            print(f"خطأ في حساب التشابه البصري: {e}")
            # استخدام الطريقة البسيطة كاحتياطية
            try:
                # قراءة الصور وتحويلها لرمادي
                img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
                img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
                
                if img1 is None or img2 is None:
                    return 0.0
                
                # توحيد الأبعاد للمقارنة
                height = min(img1.shape[0], img2.shape[0], 500)
                width = min(img1.shape[1], img2.shape[1], 500)
                
                img1_resized = cv2.resize(img1, (width, height))
                img2_resized = cv2.resize(img2, (width, height))
                
                # حساب عدة مقاييس للتشابه
                
                # 1. PSNR البسيط
                mse = np.mean((img1_resized - img2_resized) ** 2)
                if mse == 0:
                    psnr_similarity = 1.0
                else:
                    psnr = 20 * np.log10(255.0 / np.sqrt(mse))
                    psnr_similarity = min(1.0, psnr / 50.0)
                
                # 2. تشابه Histogram
                hist1 = cv2.calcHist([img1_resized], [0], None, [256], [0, 256])
                hist2 = cv2.calcHist([img2_resized], [0], None, [256], [0, 256])
                hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                
                # 3. Hash البسيط
                small1 = cv2.resize(img1_resized, (8, 8))
                small2 = cv2.resize(img2_resized, (8, 8))
                
                mean1 = np.mean(small1)
                mean2 = np.mean(small2)
                
                hash1 = (small1 > mean1).astype(int)
                hash2 = (small2 > mean2).astype(int)
                
                diff_bits = np.sum(hash1 != hash2)
                hash_similarity = 1.0 - (diff_bits / 64.0)
                
                # الدرجة المركبة
                combined_score = (
                    psnr_similarity * 0.5 +
                    hash_similarity * 0.3 +
                    hist_similarity * 0.2
                )
                
                return combined_score
                
            except Exception as e2:
                print(f"خطأ في الطريقة الاحتياطية: {e2}")
                return 0.0
    
    def mock_landingai_extraction(self, image_path):
        """محاكاة استخراج النص من LandingAI - المرحلة 2"""
        # هذه محاكاة - في التطبيق الحقيقي ستستدعي LandingAI API
        filename = Path(image_path).name
        
        # نصوص تعليمية مختلفة حسب اسم الملف للمحاكاة
        mock_texts = {
            '100.jpg': "السؤال الأول: ما هو عاصمة مصر؟ أ) القاهرة ب) الإسكندرية ج) أسوان د) الأقصر",
            '101.jpg': "الدرس الأول: الفيزياء والطبيعة. تعريف الفيزياء: علم يدرس المادة والطاقة",
            '102.jpg': "تمرين رقم 1: احسب السرعة إذا كانت المسافة 100 متر والزمن 10 ثواني",
            '103.jpg': "قانون نيوتن الأول: الجسم الساكن يبقى ساكناً والمتحرك يبقى متحركاً",
            '104.jpg': "الفصل الثاني: الحركة في خط مستقيم. أنواع الحركة المختلفة",
            '105.jpg': "مثال تطبيقي: سيارة تتحرك بسرعة ثابتة 60 كم/ساعة",
            '106.jpg': "أسئلة الفصل: 1) عرف السرعة 2) ما هو التسارع 3) اذكر قوانين الحركة"
        }
        
        return mock_texts.get(filename, f"النص المستخرج من {filename}")
    
    def create_gemini_prompt(self, old_text, new_text, visual_score):
        """إنشاء Prompt ذكي لـ Gemini - المرحلة 4"""
        prompt = f"""أنت خبير في تحليل المناهج التعليمية ومقارنتها. مهمتك هي مقارنة النصين التاليين المستخرجين من نسختين (قديمة وجديدة) من صفحة كتاب مدرسي.

معطيات:
- التشابه البصري الأولي بين الصورتين هو: {visual_score*100:.1f}%.
- النص من النسخة القديمة:
{old_text}

- النص من النسخة الجديدة:
{new_text}

المطلوب:
1. قم بتحليل دقيق للاختلافات بين النصين.
2. **تجاهل التغييرات الطفيفة** مثل إعادة صياغة الجمل بنفس المعنى، أو تغيير ترتيب الكلمات الذي لا يؤثر على المفهوم العلمي.
3. **ركز على التغييرات الجوهرية** مثل:
   - إضافة أو حذف أسئلة كاملة.
   - إضافة فقرات شرح جديدة.
   - تغيير أرقام أو بيانات علمية.
   - تعديل كبير في الأمثلة المطروحة.
4. بناءً على تحليلك، قدم **نسبة تشابه نهائية من 0 إلى 100**.
5. قدم **ملخصاً من سطر واحد** يصف أهم تغيير جوهري تم اكتشافه.

الرجاء إرجاع الإجابة بصيغة JSON فقط بهذا الشكل:
{{
  "final_similarity_score": <النسبة العددية هنا>,
  "summary_of_changes": "<وصف التغيير الرئيسي هنا>"
}}"""

        return prompt
    
    def process_single_pair(self, pair, file_idx=0, file_total=1):
        """معالجة زوج واحد من الصور - تطبيق النظام التدريجي مع تحديث التقدم المرحلي"""
        # استخراج مسارات الملفات من الـ pair object
        old_path = str(pair['old_file'])
        new_path = str(pair['new_file'])
        pair_name = pair['name']
        
        result = {
            'filename': pair_name,
            'old_path': old_path,
            'new_path': new_path,
            'old_filename': pair['old_file'].name,
            'new_filename': pair['new_file'].name,
            'stages_completed': [],
            'visual_score': 0,
            'final_score': 0,
            'summary': '',
            'status': 'في المعالجة'
        }
        stage_total = 4
        try:
            # المرحلة 1: المقارنة البصرية السريعة
            self.update_status(f"معالجة {pair_name} - المرحلة 1", current_file=pair_name, stage_idx=0, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
            visual_score = self.calculate_visual_similarity(old_path, new_path)
            result['visual_score'] = visual_score
            result['stages_completed'].append('بصري')
            if visual_score >= self.visual_threshold:
                result['status'] = 'تطابق بصري عالي'
                result['final_score'] = visual_score * 100
                result['summary'] = f"تم إيقاف المعالجة في المرحلة 1 - تشابه بصري عالي ({visual_score*100:.1f}%)"
                self.stats['visually_identical'] += 1
                self.stats['stage_1_filtered'] += 1
                result['stage_reached'] = 1
                result['overall_similarity'] = visual_score
                result['cost_saved'] = 100.0
                self.update_status(f"اكتملت المرحلة 1 لـ {pair_name} - تطابق بصري عالي", current_file=pair_name, stage_idx=1, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                return result
            
            if not hasattr(self, 'landingai_service') or not hasattr(self, 'gemini_service'):
                print("❌ خطأ: خدمات LandingAI أو Gemini غير متاحة!")
                return result
            
            # المرحلة 2: استخراج النص (يختلف حسب وضع المعالجة)
            if self.processing_mode == "gemini_only":
                # وضع Gemini فقط - استخراج ومقارنة مباشرة
                self.update_status(f"معالجة {pair_name} - المرحلة 2: استخراج ومقارنة مباشرة (Gemini Vision)", current_file=pair_name, stage_idx=1, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                
                try:
                    if self.gemini_vision_service:
                        # استخراج النص من كلا الصورتين
                        old_extraction = asyncio.run(self.gemini_vision_service.extract_text_from_image(old_path))
                        new_extraction = asyncio.run(self.gemini_vision_service.extract_text_from_image(new_path))
                        
                        if old_extraction.success and new_extraction.success:
                            old_text = old_extraction.extracted_text
                            new_text = new_extraction.extracted_text
                            
                            # المقارنة المباشرة باستخدام Gemini Vision
                            comparison_result = asyncio.run(self.gemini_vision_service.compare_images_directly(old_path, new_path))
                            
                            if comparison_result["success"]:
                                result['text_extraction'] = {
                                    'old_text': old_text,
                                    'new_text': new_text,
                                    'extraction_time': old_extraction.processing_time + new_extraction.processing_time,
                                }
                                result['ai_analysis'] = {
                                    'similarity_percentage': comparison_result["comparison_result"]["similarity_percentage"],
                                    'summary': comparison_result["comparison_result"]["summary"],
                                    'content_changes': comparison_result["comparison_result"].get("content_changes", []),
                                    'processing_time': comparison_result["processing_time"]
                                }
                                result['final_score'] = comparison_result["comparison_result"]["similarity_percentage"]
                                result['overall_similarity'] = comparison_result["comparison_result"]["similarity_percentage"] / 100.0
                                result['summary'] = comparison_result["comparison_result"]["summary"]
                                result['status'] = 'تم التحليل الكامل (Gemini Vision)'
                                result['stage_reached'] = 3
                                result['cost_saved'] = 50.0  # توفير 50% لأنه تم في خطوة واحدة
                                result['stages_completed'].append('Gemini Vision مباشر')
                                
                                self.stats['fully_analyzed'] += 1
                                self.stats['stage_3_analyzed'] += 1
                                self.update_status(f"اكتملت المعالجة المباشرة لـ {pair_name} - Gemini Vision", current_file=pair_name, stage_idx=3, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                                
                                return result
                            else:
                                raise Exception("فشل في المقارنة المباشرة")
                        else:
                            raise Exception("فشل في استخراج النص")
                    else:
                        raise Exception("خدمة Gemini Vision غير متاحة")
                        
                except Exception as e:
                    logger.error(f"❌ خطأ في وضع Gemini Vision لـ {pair_name}: {e}")
                    # العودة للطريقة التقليدية كاحتياطي
                    result['stages_completed'].append('Gemini Vision (خطأ)')
                    self.update_status(f"خطأ في Gemini Vision لـ {pair_name} - العودة للطريقة التقليدية", current_file=pair_name, stage_idx=2, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
            
            # المرحلة 2: استخراج النص (الطريقة التقليدية - LandingAI + Gemini)
            if self.processing_mode == "landingai_gemini" or (self.processing_mode == "gemini_only" and 'Gemini Vision (خطأ)' in result['stages_completed']):
                self.update_status(f"معالجة {pair_name} - المرحلة 2: استخراج النص (LandingAI)", current_file=pair_name, stage_idx=1, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                extraction_start = time.time()
                
                try:
                    old_res = asyncio.run(self.landingai_service.extract_from_file(old_path))
                    new_res = asyncio.run(self.landingai_service.extract_from_file(new_path))
                    
                    # فحص النتائج
                    if not old_res.success or not new_res.success:
                        error_msg = f"فشل استخراج النص: قديم={old_res.error_message}, جديد={new_res.error_message}"
                        logger.error(f"❌ {error_msg}")
                        raise Exception(error_msg)
                    
                    old_text = old_res.markdown_content
                    new_text = new_res.markdown_content
                    
                    # فحص أن النصوص ليست فارغة
                    if not old_text or not old_text.strip():
                        logger.warning(f"⚠️ نص قديم فارغ لـ {pair_name}، استخدام نص افتراضي")
                        old_text = f"محتوى من {pair_name} (قديم)"
                    
                    if not new_text or not new_text.strip():
                        logger.warning(f"⚠️ نص جديد فارغ لـ {pair_name}، استخدام نص افتراضي")
                        new_text = f"محتوى من {pair_name} (جديد)"
                    
                    extraction_time = time.time() - extraction_start
                    result['text_extraction'] = {
                        'old_text': old_text,
                        'new_text': new_text,
                        'extraction_time': extraction_time,
                    }
                    result['has_text_content'] = True
                    result['stages_completed'].append('استخراج النص (LandingAI)')
                    self.stats['stage_2_processed'] += 1
                    self.update_status(f"اكتملت المرحلة 2 لـ {pair_name} - تم استخراج النص", current_file=pair_name, stage_idx=2, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في استخراج النص لـ {pair_name}: {e}")
                    # استخدام نصوص افتراضية في حالة الخطأ
                    old_text = f"محتوى من {pair_name} (قديم - خطأ في الاستخراج)"
                    new_text = f"محتوى من {pair_name} (جديد - خطأ في الاستخراج)"
                    result['text_extraction'] = {
                        'old_text': old_text,
                        'new_text': new_text,
                        'extraction_time': 0,
                        'error': str(e)
                    }
                    result['has_text_content'] = False
                    result['stages_completed'].append('استخراج النص (خطأ)')
                    self.update_status(f"خطأ في المرحلة 2 لـ {pair_name} - استخدام نصوص افتراضية", current_file=pair_name, stage_idx=2, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                
                # المرحلة 3: تحسين النص
                self.update_status(f"معالجة {pair_name} - المرحلة 3: تحسين النص", current_file=pair_name, stage_idx=2, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                
                try:
                    old_optimization = self.text_optimizer.optimize_for_ai_analysis(old_text)
                    new_optimization = self.text_optimizer.optimize_for_ai_analysis(new_text)
                    
                    # فحص النتائج
                    if old_optimization.get("error") or new_optimization.get("error"):
                        logger.warning(f"⚠️ تحذير في تحسين النص لـ {pair_name}: {old_optimization.get('error', '')} {new_optimization.get('error', '')}")
                    
                    old_text_optimized = old_optimization.get('optimized_text', old_text)
                    new_text_optimized = new_optimization.get('optimized_text', new_text)
                    
                    # التأكد من أن النصوص ليست فارغة
                    if not old_text_optimized or not new_text_optimized:
                        logger.warning(f"⚠️ نص محسن فارغ لـ {pair_name}، استخدام النص الأصلي")
                        old_text_optimized = old_text
                        new_text_optimized = new_text
                    
                    result['stages_completed'].append('تحسين النص')
                    self.update_status(f"اكتملت المرحلة 3 لـ {pair_name} - تم تحسين النص", current_file=pair_name, stage_idx=3, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في تحسين النص لـ {pair_name}: {e}")
                    # استخدام النص الأصلي في حالة الخطأ
                    old_text_optimized = old_text
                    new_text_optimized = new_text
                    result['stages_completed'].append('تحسين النص (خطأ)')
                    self.update_status(f"خطأ في المرحلة 3 لـ {pair_name} - استخدام النص الأصلي", current_file=pair_name, stage_idx=3, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                
                # المرحلة 4: التحليل العميق مع Gemini
                self.update_status(f"معالجة {pair_name} - المرحلة 4: التحليل العميق", current_file=pair_name, stage_idx=3, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                
                try:
                    prompt = self.create_gemini_prompt(old_text_optimized, new_text_optimized, visual_score)
                    gemini_result = asyncio.run(self.gemini_service.compare_texts(old_text_optimized, new_text_optimized))
                    
                    if gemini_result is None:
                        raise Exception("لم يتم الحصول على نتيجة من Gemini")
                    
                    gemini_json = gemini_result.dict()
                    final_score = gemini_json.get("similarity_percentage", 82.5)
                    summary_of_changes = gemini_json.get("summary", "فشل تحليل الملخص.")
                    
                    result['stages_completed'].append('التحليل العميق (Gemini)')
                    result['ai_analysis'] = {
                        'similarity_percentage': final_score,
                        'summary': summary_of_changes,
                        'content_changes': gemini_json.get('content_changes', []),
                        'processing_time': gemini_json.get('processing_time', 0)
                    }
                    result['final_score'] = final_score
                    result['overall_similarity'] = final_score / 100.0
                    result['summary'] = summary_of_changes
                    result['status'] = 'تم التحليل الكامل'
                    result['stage_reached'] = 3
                    result['cost_saved'] = 33.3
                    
                    self.stats['fully_analyzed'] += 1
                    self.stats['stage_3_analyzed'] += 1
                    self.update_status(f"اكتملت المرحلة 4 لـ {pair_name} - تم التحليل العميق", current_file=pair_name, stage_idx=4, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في التحليل العميق لـ {pair_name}: {e}")
                    # إرجاع نتيجة أساسية في حالة فشل Gemini
                    result['stages_completed'].append('التحليل العميق (خطأ)')
                    result['ai_analysis'] = {
                        'similarity_percentage': visual_score * 100,
                        'summary': f"فشل في التحليل العميق: {str(e)}",
                        'content_changes': [],
                        'processing_time': 0
                    }
                    result['final_score'] = visual_score * 100
                    result['overall_similarity'] = visual_score
                    result['summary'] = f"فشل في التحليل العميق: {str(e)}"
                    result['status'] = 'تحليل جزئي'
                    result['stage_reached'] = 2
                    result['cost_saved'] = 0.0
                    
                    self.stats['failed'] += 1
                    self.update_status(f"خطأ في المرحلة 4 لـ {pair_name} - تحليل جزئي", current_file=pair_name, stage_idx=4, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
            
            return result
        except Exception as e:
            result['status'] = 'فشل'
            result['error'] = str(e)
            self.stats['failed'] += 1
            self.update_status(f"❌ خطأ في معالجة {pair_name}: {e}", current_file=pair_name, stage_idx=stage_total, stage_total=stage_total, file_idx=file_idx, file_total=file_total)
            return result
    
    def find_common_files(self):
        """البحث عن الملفات للمقارنة بالترتيب"""
        if not self.old_dir.exists():
            raise FileNotFoundError(f"المجلد غير موجود: {self.old_dir}")
        if not self.new_dir.exists():
            raise FileNotFoundError(f"المجلد غير موجود: {self.new_dir}")
        
        # الحصول على قائمة الملفات مرتبة
        old_files = sorted([f for f in self.old_dir.glob("*.jpg")])
        new_files = sorted([f for f in self.new_dir.glob("*.jpg")])
        
        print(f"📁 مجلد 2024: {len(old_files)} ملف")
        print(f"📁 مجلد 2025: {len(new_files)} ملف")
        
        # إنشاء أزواج للمقارنة بالترتيب
        pairs = []
        min_count = min(len(old_files), len(new_files))
        
        for i in range(min_count):
            old_file = old_files[i]
            new_file = new_files[i]
            # إنشاء اسم مؤقت للزوج
            pair_name = f"pair_{i+1:03d}_{old_file.stem}_vs_{new_file.stem}.jpg"
            pairs.append({
                'name': pair_name,
                'old_file': old_file,
                'new_file': new_file,
                'index': i
            })
        
        print(f"🔍 أزواج للمقارنة: {len(pairs)} زوج")
        
        if not pairs:
            print("⚠️ لا توجد ملفات للمقارنة!")
        else:
            for i, pair in enumerate(pairs):
                print(f"   {i+1}. {pair['old_file'].name} ↔ {pair['new_file'].name}")
            
        return pairs
    
    def run_batch_processing(self):
        """تشغيل المعالجة الجماعية الكاملة مع تحديث التقدم المرحلي"""
        print("🚀 بدء نظام المقارنة الذكي للمناهج التعليمية")
        print("="*60)
        pairs = self.find_common_files()
        if not pairs:
            return
        self.stats['total_pairs'] = len(pairs)
        self.stats['start_time'] = time.time()
        self.update_status("بدء المعالجة الجماعية", progress=0)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.process_single_pair, pair, idx, len(pairs)) for idx, pair in enumerate(pairs)]
            completed = 0
            for future in tqdm(as_completed(futures), total=len(pairs), desc="🔄 المعالجة"):
                result = future.result()
                self.results.append(result)
                completed += 1
                progress = int((completed / len(pairs)) * 100)
                self.update_status(f"تم معالجة {completed}/{len(pairs)} زوج", progress=progress)
        self.stats['end_time'] = time.time()
        self.stats['total_duration'] = self.stats['end_time'] - self.stats['start_time']
        self.update_status("اكتملت المعالجة", progress=100)
        self.print_detailed_results()
        self.print_final_summary()
    
    def print_detailed_results(self):
        """طباعة النتائج التفصيلية"""
        print("\n" + "="*60)
        print("📊 نتائج المقارنة التفصيلية")
        print("="*60)
        
        # ترتيب النتائج حسب اسم الملف
        sorted_results = sorted(self.results, key=lambda x: x['filename'])
        
        for result in sorted_results:
            print(f"\n🔄 مقارنة: [{result['filename']}]")
            print("-" * 50)
            
            # طباعة المراحل المكتملة
            stages_str = " → ".join(result['stages_completed'])
            print(f"   📋 المراحل: {stages_str}")
            
            # طباعة النتائج
            print(f"   🎯 التشابه البصري: {result['visual_score']*100:.1f}%")
            
            if result['status'] == 'تطابق بصري عالي':
                print(f"   🟢 النتيجة: تطابق بصري عالي - توقف المعالجة")
                print(f"   💰 توفير: 100% (لم يتم استخدام APIs)")
                
            elif result['status'] == 'تم التحليل الكامل':
                print(f"   🧠 التشابه النهائي: {result['final_score']:.1f}%")
                print(f"   📝 ملخص التغييرات: {result['summary']}")
                print(f"   💰 توفير: 33.3% (2 API calls بدلاً من 3)")
                
            elif result['status'] == 'فشل':
                print(f"   ❌ خطأ: {result.get('error', 'خطأ غير محدد')}")
            
            print()
    
    def print_final_summary(self):
        """طباعة الملخص النهائي"""
        print("="*60)
        print("📈 ملخص المعالجة الجماعية النهائي")
        print("="*60)
        
        stats = self.stats
        total = stats['total_pairs']
        
        if total == 0:
            print("لا توجد بيانات للعرض")
            return
        
        print(f"📊 إجمالي الأزواج: {total}")
        print(f"✅ تطابق بصري عالي (توفير 100%): {stats['visually_identical']} ({stats['visually_identical']/total*100:.1f}%)")
        print(f"🧠 تحليل كامل (توفير 33%): {stats['fully_analyzed']} ({stats['fully_analyzed']/total*100:.1f}%)")
        print(f"❌ فشل في المعالجة: {stats['failed']} ({stats['failed']/total*100:.1f}%)")
        
        print(f"\n⏱️ إحصائيات الأداء:")
        print(f"   المدة الإجمالية: {stats['total_duration']:.2f} ثانية")
        print(f"   متوسط الوقت لكل زوج: {stats['total_duration']/total:.2f} ثانية")
        
        # حساب التوفير المتوقع
        if total > 0:
            savings_100 = stats['visually_identical'] / total  # 100% توفير
            savings_33 = stats['fully_analyzed'] / total       # 33% توفير
            avg_savings = (savings_100 * 100) + (savings_33 * 33.3)
            print(f"   💰 متوسط التوفير في التكلفة: {avg_savings:.1f}%")
        
        print("\n🎉 تم الانتهاء من المعالجة الجماعية بنجاح!")

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description="نظام المقارنة الذكي للمناهج التعليمية")
    parser.add_argument("old_dir", help="مجلد الصور القديمة")
    parser.add_argument("new_dir", help="مجلد الصور الجديدة")
    parser.add_argument("--workers", type=int, default=4, help="عدد المعالجات المتوازية (افتراضي: 4)")
    parser.add_argument("--threshold", type=float, default=0.95, help="عتبة التشابه البصري (افتراضي: 0.95)")
    
    args = parser.parse_args()
    
    # التحقق من وجود المجلدات
    if not Path(args.old_dir).exists():
        print(f"❌ خطأ: المجلد غير موجود - {args.old_dir}")
        return
    
    if not Path(args.new_dir).exists():
        print(f"❌ خطأ: المجلد غير موجود - {args.new_dir}")
        return
    
    # إنشاء وتشغيل المعالج
    processor = SmartBatchProcessor(
        old_dir=args.old_dir,
        new_dir=args.new_dir,
        max_workers=args.workers,
        visual_threshold=args.threshold
    )
    
    processor.run_batch_processing()

if __name__ == "__main__":
    main() 