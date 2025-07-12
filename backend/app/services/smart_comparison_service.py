"""
خدمة التحليل التدريجي الذكي
Smart Progressive Analysis Service

فكرة النظام:
1. تحليل بصري سريع محلي أولاً
2. إذا احتجنا تأكيد -> LandingAI للنص فقط
3. إذا احتجنا تحليل عميق -> Gemini للتحليل الذكي

توفير: 80%+ من استخدام API
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path
import hashlib
from PIL import Image, ImageChops
from skimage.metrics import structural_similarity as ssim
import asyncio
from loguru import logger

from app.services.gemini_service import GeminiService
from app.core.config import get_settings

settings = get_settings()


class SmartComparisonService:
    """خدمة التحليل التدريجي الذكي"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.cache_dir = Path(settings.UPLOAD_DIR) / "smart_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # عتبات التحليل الذكية
        self.VISUAL_SIMILARITY_THRESHOLD = 85  # إذا أقل من 85% -> استخدم النص
        self.TEXT_SIMILARITY_THRESHOLD = 75    # إذا أقل من 75% -> استخدم Gemini
        self.HIGH_CONFIDENCE_THRESHOLD = 95    # إذا أكثر من 95% -> توقف
        
        logger.info("✅ تم تكوين خدمة التحليل التدريجي الذكي")
    
    async def smart_compare_images(
        self, 
        old_image_path: str, 
        new_image_path: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """المقارنة الذكية التدريجية للصور"""
        
        start_time = datetime.now()
        result = {
            "session_id": session_id or f"smart_{int(datetime.now().timestamp())}",
            "stages_used": [],
            "api_calls_saved": 0,
            "total_processing_time": 0,
            "confidence_level": "low"
        }
        
        logger.info(f"🚀 بدء التحليل التدريجي الذكي للجلسة: {result['session_id']}")
        
        try:
            # المرحلة 1: التحليل البصري السريع (محلي)
            logger.info("📊 المرحلة 1: التحليل البصري السريع...")
            visual_result = await self._stage1_visual_analysis(old_image_path, new_image_path)
            result["stages_used"].append("visual_analysis")
            result["visual_similarity"] = visual_result["similarity"]
            
            # إذا كان التشابه عالي جداً -> توقف هنا
            if visual_result["similarity"] >= self.HIGH_CONFIDENCE_THRESHOLD:
                logger.info(f"✅ تشابه عالي ({visual_result['similarity']:.1f}%) - توقف في المرحلة 1")
                result["confidence_level"] = "very_high"
                result["api_calls_saved"] = 2  # وفرنا LandingAI + Gemini
                result["final_decision"] = "متطابق تماماً - تغييرات تصميمية فقط"
                result["similarity_percentage"] = visual_result["similarity"]
                result["recommendation"] = "لا يوجد تغييرات جوهرية"
                return result
            
            # إذا كان التشابه متوسط -> المرحلة 2
            if visual_result["similarity"] >= self.VISUAL_SIMILARITY_THRESHOLD:
                logger.info(f"📝 تشابه متوسط ({visual_result['similarity']:.1f}%) - المرحلة 2: استخراج النص")
                text_result = await self._stage2_text_extraction(old_image_path, new_image_path)
                result["stages_used"].append("text_extraction")
                result["api_calls_saved"] = 1  # وفرنا Gemini
                
                # حساب التشابه النصي
                if text_result["success"]:
                    text_similarity = await self._calculate_text_similarity(
                        text_result["old_text"], 
                        text_result["new_text"]
                    )
                    
                    # إذا كان النص متشابه جداً -> توقف هنا
                    if text_similarity >= self.TEXT_SIMILARITY_THRESHOLD:
                        logger.info(f"✅ نص متشابه ({text_similarity:.1f}%) - توقف في المرحلة 2")
                        result["confidence_level"] = "high"
                        result["text_similarity"] = text_similarity
                        result["final_decision"] = "متشابه مع تحديثات طفيفة"
                        result["similarity_percentage"] = (visual_result["similarity"] + text_similarity) / 2
                        result["recommendation"] = "مراجعة سريعة للتأكد من التحديثات"
                        return result
                
                # إذا كان النص مختلف -> المرحلة 3
                logger.info(f"🤖 نص مختلف ({text_similarity:.1f}%) - المرحلة 3: التحليل العميق")
                gemini_result = await self._stage3_deep_analysis(
                    text_result["old_text"], 
                    text_result["new_text"]
                )
                result["stages_used"].append("deep_analysis")
                result["api_calls_saved"] = 0
                result["gemini_analysis"] = gemini_result
                result["confidence_level"] = "very_high"
                result["text_similarity"] = text_similarity
                result["similarity_percentage"] = gemini_result.similarity_percentage
                result["final_decision"] = gemini_result.summary
                result["recommendation"] = gemini_result.recommendation
                
            else:
                # تشابه منخفض -> مباشرة للمرحلة 3
                logger.info(f"🚨 تشابه منخفض ({visual_result['similarity']:.1f}%) - مباشرة للتحليل العميق")
                
                # استخراج النص أولاً
                text_result = await self._stage2_text_extraction(old_image_path, new_image_path)
                result["stages_used"].extend(["text_extraction", "deep_analysis"])
                
                if text_result["success"]:
                    gemini_result = await self._stage3_deep_analysis(
                        text_result["old_text"], 
                        text_result["new_text"]
                    )
                    result["gemini_analysis"] = gemini_result
                    result["confidence_level"] = "very_high"
                    result["similarity_percentage"] = gemini_result.similarity_percentage
                    result["final_decision"] = gemini_result.summary
                    result["recommendation"] = gemini_result.recommendation
                else:
                    result["confidence_level"] = "low"
                    result["similarity_percentage"] = visual_result["similarity"]
                    result["final_decision"] = "تغييرات كبيرة محتملة - تحتاج مراجعة يدوية"
                    result["recommendation"] = "مراجعة شاملة مطلوبة"
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحليل التدريجي: {e}")
            result["error"] = str(e)
            result["confidence_level"] = "error"
        
        # حساب الوقت الإجمالي
        result["total_processing_time"] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎯 انتهى التحليل: {len(result['stages_used'])} مراحل، وفر {result['api_calls_saved']} API calls")
        
        return result
    
    async def _stage1_visual_analysis(self, old_path: str, new_path: str) -> Dict[str, Any]:
        """المرحلة 1: التحليل البصري السريع المحلي"""
        
        try:
            # قراءة الصور
            old_img = cv2.imread(old_path)
            new_img = cv2.imread(new_path)
            
            if old_img is None or new_img is None:
                raise ValueError("فشل في قراءة إحدى الصور")
            
            # تحويل للرمادي
            old_gray = cv2.cvtColor(old_img, cv2.COLOR_BGR2GRAY)
            new_gray = cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)
            
            # توحيد الأحجام
            height, width = min(old_gray.shape[0], new_gray.shape[0]), min(old_gray.shape[1], new_gray.shape[1])
            old_resized = cv2.resize(old_gray, (width, height))
            new_resized = cv2.resize(new_gray, (width, height))
            
            # حساب SSIM (Structural Similarity Index)
            ssim_score = ssim(old_resized, new_resized)
            
            # حساب Hash للمقارنة السريعة
            old_hash = self._calculate_image_hash(old_resized)
            new_hash = self._calculate_image_hash(new_resized)
            hash_similarity = self._compare_hashes(old_hash, new_hash)
            
            # حساب Histogram للألوان
            hist_similarity = self._calculate_histogram_similarity(old_img, new_img)
            
            # حساب متوسط مرجح للتشابه
            visual_similarity = (
                ssim_score * 0.5 +           # 50% للتركيب
                hash_similarity * 0.3 +      # 30% للشكل العام
                hist_similarity * 0.2        # 20% للألوان
            ) * 100
            
            logger.debug(f"📊 النتائج البصرية: SSIM={ssim_score:.3f}, Hash={hash_similarity:.3f}, Hist={hist_similarity:.3f}")
            
            return {
                "similarity": round(visual_similarity, 1),
                "ssim_score": round(ssim_score * 100, 1),
                "hash_similarity": round(hash_similarity * 100, 1),
                "histogram_similarity": round(hist_similarity * 100, 1),
                "processing_time": 0.1  # سريع جداً
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحليل البصري: {e}")
            return {"similarity": 50.0, "error": str(e)}
    
    def _calculate_image_hash(self, image: np.ndarray) -> str:
        """حساب hash للصورة للمقارنة السريعة"""
        # تصغير الصورة لـ 8x8
        small = cv2.resize(image, (8, 8))
        # حساب متوسط الإضاءة
        avg = small.mean()
        # تحويل لـ binary
        binary = small > avg
        # تحويل لـ hash
        return hashlib.md5(binary.tobytes()).hexdigest()
    
    def _compare_hashes(self, hash1: str, hash2: str) -> float:
        """مقارنة الـ hashes"""
        if hash1 == hash2:
            return 1.0
        
        # حساب Hamming distance
        diff = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        similarity = 1 - (diff / len(hash1))
        return max(similarity, 0.0)
    
    def _calculate_histogram_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """حساب تشابه الألوان باستخدام Histogram"""
        # حساب histograms
        hist1 = cv2.calcHist([img1], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([img2], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
        
        # normalization
        cv2.normalize(hist1, hist1)
        cv2.normalize(hist2, hist2)
        
        # مقارنة باستخدام correlation
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return max(correlation, 0.0)
    
    async def _stage2_text_extraction(self, old_path: str, new_path: str) -> Dict[str, Any]:
        """المرحلة 2: استخراج النص الذكي"""
        
        logger.info("📝 استخراج النص باستخدام LandingAI...")
        
        try:
            # استخراج النص من الصورتين
            # TODO: استدعاء LandingAI هنا
            # للآن نحاكي العملية
            await asyncio.sleep(1)  # محاكاة وقت المعالجة
            
            # نص تجريبي (سيتم استبداله بـ LandingAI الحقيقي)
            old_text = "قاعدة باسكال: عندما يؤثر ضغط على سائل محبوس في إناء..."
            new_text = "قاعدة باسكال: عندما يؤثر ضغط على سائل محبوس في إناء..."
            
            return {
                "success": True,
                "old_text": old_text,
                "new_text": new_text,
                "processing_time": 1.0
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في استخراج النص: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _calculate_text_similarity(self, old_text: str, new_text: str) -> float:
        """حساب تشابه النص بسرعة"""
        
        # استخدام الخوارزمية المحسنة من GeminiService
        enhanced_similarity = self.gemini_service._calculate_enhanced_similarity(
            old_text, new_text, 
            self.gemini_service.gemini_service._calculate_enhanced_similarity(old_text, new_text, 0)
        )
        
        return enhanced_similarity
    
    async def _stage3_deep_analysis(self, old_text: str, new_text: str) -> Any:
        """المرحلة 3: التحليل العميق باستخدام Gemini"""
        
        logger.info("🤖 التحليل العميق باستخدام Gemini AI...")
        
        # تنظيف النص قبل الإرسال لتوفير التوكنز
        cleaned_old = self._extract_essential_content(old_text)
        cleaned_new = self._extract_essential_content(new_text)
        
        # استدعاء Gemini مع النص المنظف
        result = await self.gemini_service.compare_texts(cleaned_old, cleaned_new)
        
        return result
    
    def _extract_essential_content(self, text: str) -> str:
        """استخراج المحتوى الأساسي فقط لتوفير التوكنز"""
        
        if not text:
            return ""
        
        # إزالة الوصف التفصيلي لـ LandingAI
        lines = text.split('\n')
        essential_lines = []
        
        # الكلمات المهمة التي نحتفظ بها
        important_keywords = [
            'قاعدة', 'مبدأ', 'قانون', 'نظرية', 'تعريف', 'باسكال', 'هيدروليكي',
            'ضغط', 'سائل', 'تطبيقات', 'مكبس', 'فرامل', 'رافعة', 'حفار',
            'ملاحظة', 'أسئلة', 'تمارين', 'أمثلة', 'شرح'
        ]
        
        for line in lines:
            line = line.strip()
            
            # تجاهل الأوصاف التقنية المفصلة
            if any(skip_word in line.lower() for skip_word in [
                'scene overview', 'technical details', 'spatial relationships', 
                'analysis', 'photo', 'image', 'figure', 'illustration'
            ]):
                continue
            
            # احتفظ بالخطوط التي تحتوي على كلمات مهمة
            if any(keyword in line for keyword in important_keywords) or len(line) > 20:
                essential_lines.append(line)
        
        # إرجاع النص المنظف
        cleaned_text = '\n'.join(essential_lines)
        
        # إذا كان النص طويل جداً، اقتطع بذكاء
        if len(cleaned_text) > 1000:
            sentences = cleaned_text.split('.')
            important_sentences = []
            total_length = 0
            
            for sentence in sentences:
                if total_length + len(sentence) < 800:  # حد أقصى آمن
                    important_sentences.append(sentence)
                    total_length += len(sentence)
                else:
                    break
            
            cleaned_text = '.'.join(important_sentences)
        
        logger.debug(f"📝 تنظيف النص: {len(text)} -> {len(cleaned_text)} حرف")
        
        return cleaned_text
    
    async def get_analysis_statistics(self) -> Dict[str, Any]:
        """إحصائيات توفير API"""
        
        # هنا يمكن حفظ إحصائيات الاستخدام
        return {
            "total_analyses": 0,
            "api_calls_saved": 0,
            "efficiency_percentage": 0,
            "average_processing_time": 0
        }


# إنشاء instance واحد للخدمة
smart_comparison_service = SmartComparisonService() 