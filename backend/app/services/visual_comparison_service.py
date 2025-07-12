"""
خدمة المقارنة البصرية للصور المحسنة
Enhanced Visual Image Comparison Service using SSIM + pHash + CLIP + Structural Analysis
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
import tempfile
from pathlib import Path
import json

from skimage.metrics import structural_similarity as ssim
import imagehash
from PIL import Image, ImageEnhance, ImageOps
from pydantic import BaseModel, Field
from loguru import logger

# استيراد اختياري لـ sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("✅ تم تحميل sentence_transformers")
except ImportError:
    logger.warning("⚠️ sentence_transformers غير متاح، سيتم تعطيل CLIP")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()


class VisualComparisonResult(BaseModel):
    """نتيجة المقارنة البصرية المحسنة"""
    similarity_score: float = Field(..., ge=0, le=100, description="النتيجة الإجمالية")
    ssim_score: float = Field(..., ge=0, le=1, description="نتيجة SSIM")
    phash_score: float = Field(..., ge=0, le=1, description="نتيجة pHash")
    clip_score: Optional[float] = Field(None, ge=0, le=1, description="نتيجة CLIP")
    
    # مقاييس إضافية محسنة
    histogram_correlation: float = Field(default=0.0, description="ارتباط الهستوجرام")
    feature_matching_score: float = Field(default=0.0, description="تطابق الميزات")
    edge_similarity: float = Field(default=0.0, description="تشابه الحواف")
    
    # تحليل هيكلي
    layout_similarity: float = Field(default=0.0, description="تشابه التخطيط")
    text_region_overlap: float = Field(default=0.0, description="تداخل مناطق النص")
    
    # الأوزان المستخدمة
    weights_used: Dict[str, float] = Field(default_factory=dict)
    
    # تفاصيل المعالجة
    processing_time: float
    old_image_path: str
    new_image_path: str
    
    # معلومات الصور
    old_image_size: Tuple[int, int] = Field(default=(0, 0))
    new_image_size: Tuple[int, int] = Field(default=(0, 0))
    
    # تحليل الاختلافات المحسن
    difference_detected: bool = False
    difference_map_path: Optional[str] = None
    major_changes_detected: bool = False
    
    # مناطق التغيير
    changed_regions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # إحصائيات
    mean_squared_error: float = 0.0
    peak_signal_noise_ratio: float = 0.0
    
    # تحليل محتوى
    content_type_detected: str = "educational"
    probable_content_match: bool = False
    
    # رسائل
    analysis_summary: str = ""
    recommendations: str = ""
    confidence_notes: str = ""


class EnhancedVisualComparisonService:
    """خدمة المقارنة البصرية المحسنة للصور التعليمية"""
    
    def __init__(self):
        # أوزان المقارنة المحسنة للمحتوى التعليمي
        self.ssim_weight = float(os.getenv("VISUAL_COMPARISON_SSIM_WEIGHT", "0.25"))
        self.phash_weight = float(os.getenv("VISUAL_COMPARISON_PHASH_WEIGHT", "0.15"))
        self.clip_weight = float(os.getenv("VISUAL_COMPARISON_CLIP_WEIGHT", "0.25"))
        self.histogram_weight = float(os.getenv("VISUAL_COMPARISON_HISTOGRAM_WEIGHT", "0.10"))
        self.feature_weight = float(os.getenv("VISUAL_COMPARISON_FEATURE_WEIGHT", "0.15"))
        self.edge_weight = float(os.getenv("VISUAL_COMPARISON_EDGE_WEIGHT", "0.10"))
        
        # التحقق من أن الأوزان تساوي 1.0
        total_weight = (self.ssim_weight + self.phash_weight + self.clip_weight + 
                       self.histogram_weight + self.feature_weight + self.edge_weight)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"⚠️ مجموع الأوزان {total_weight:.2f} ≠ 1.0، سيتم التطبيع")
            self.ssim_weight /= total_weight
            self.phash_weight /= total_weight
            self.clip_weight /= total_weight
            self.histogram_weight /= total_weight
            self.feature_weight /= total_weight
            self.edge_weight /= total_weight
        
        # عتبة التشابه للمحتوى التعليمي (أقل حساسية)
        self.similarity_threshold = float(os.getenv("VISUAL_COMPARISON_THRESHOLD", "0.75"))
        self.high_similarity_threshold = float(os.getenv("HIGH_SIMILARITY_THRESHOLD", "0.90"))
        
        # تحميل نموذج CLIP
        self.clip_model = None
        self.clip_available = False
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.clip_model = SentenceTransformer('clip-ViT-B-32')
                self.clip_available = True
                logger.info("✅ تم تحميل نموذج CLIP بنجاح")
            except Exception as e:
                logger.warning(f"⚠️ فشل في تحميل CLIP: {e}")
                self.clip_available = False
        else:
            logger.info("ℹ️ CLIP غير متاح، سيتم تعطيله")
        
        # إعادة توزيع الأوزان إذا لم يكن CLIP متاحاً
        if not self.clip_available:
            remaining_weight = 1.0 - self.clip_weight
            factor = 1.0 / remaining_weight
            self.ssim_weight *= factor
            self.phash_weight *= factor
            self.histogram_weight *= factor
            self.feature_weight *= factor
            self.edge_weight *= factor
            self.clip_weight = 0.0
        
        # إعداد SIFT للميزات
        try:
            self.sift = cv2.SIFT_create()
            self.feature_matching_available = True
            logger.info("✅ تم تحميل SIFT لمطابقة الميزات")
        except Exception as e:
            logger.warning(f"⚠️ فشل في تحميل SIFT: {e}")
            self.feature_matching_available = False
        
        logger.info(f"🔧 أوزان المقارنة المحسنة:")
        logger.info(f"   SSIM: {self.ssim_weight:.2f}")
        logger.info(f"   pHash: {self.phash_weight:.2f}")
        logger.info(f"   CLIP: {self.clip_weight:.2f}")
        logger.info(f"   Histogram: {self.histogram_weight:.2f}")
        logger.info(f"   Features: {self.feature_weight:.2f}")
        logger.info(f"   Edges: {self.edge_weight:.2f}")

    async def compare_images(
        self, 
        old_image_path: str, 
        new_image_path: str,
        output_dir: Optional[str] = None
    ) -> VisualComparisonResult:
        """
        مقارنة محسنة للصور التعليمية
        Enhanced comparison for educational images
        """
        start_time = datetime.now()
        
        logger.info(f"🖼️ بدء المقارنة البصرية المحسنة: {Path(old_image_path).name} vs {Path(new_image_path).name}")
        
        try:
            # التحقق من وجود الملفات
            if not os.path.exists(old_image_path) or not os.path.exists(new_image_path):
                raise FileNotFoundError("أحد الملفات غير موجود")
            
            # تحميل الصور
            old_image = self._load_and_preprocess_image(old_image_path)
            new_image = self._load_and_preprocess_image(new_image_path)
            
            # الحصول على أحجام الصور الأصلية
            old_pil = Image.open(old_image_path)
            new_pil = Image.open(new_image_path)
            old_size = old_pil.size
            new_size = new_pil.size
            
            # تحليل نوع المحتوى
            content_type = self._detect_content_type(old_image, new_image)
            
            # 1. حساب SSIM
            ssim_score = self._calculate_ssim(old_image, new_image)
            logger.debug(f"📊 SSIM Score: {ssim_score:.3f}")
            
            # 2. حساب pHash
            phash_score = self._calculate_phash_similarity(old_image_path, new_image_path)
            logger.debug(f"📊 pHash Score: {phash_score:.3f}")
            
            # 3. حساب CLIP (إذا كان متاحاً)
            clip_score = None
            if self.clip_available:
                clip_score = self._calculate_clip_similarity(old_image_path, new_image_path)
                logger.debug(f"📊 CLIP Score: {clip_score:.3f}")
            
            # 4. حساب الهستوجرام
            histogram_correlation = self._calculate_histogram_correlation(old_image, new_image)
            logger.debug(f"📊 Histogram Correlation: {histogram_correlation:.3f}")
            
            # 5. مطابقة الميزات
            feature_matching_score = 0.0
            if self.feature_matching_available:
                feature_matching_score = self._calculate_feature_matching(old_image, new_image)
                logger.debug(f"📊 Feature Matching: {feature_matching_score:.3f}")
            
            # 6. تشابه الحواف
            edge_similarity = self._calculate_edge_similarity(old_image, new_image)
            logger.debug(f"📊 Edge Similarity: {edge_similarity:.3f}")
            
            # 7. حساب النتيجة الإجمالية المحسنة
            overall_similarity = self._calculate_enhanced_weighted_similarity(
                ssim_score, phash_score, clip_score, 
                histogram_correlation, feature_matching_score, edge_similarity
            )
            
            # 8. تحليل هيكلي محسن
            layout_similarity = self._analyze_layout_similarity(old_image, new_image)
            text_region_overlap = self._analyze_text_regions(old_image, new_image)
            
            # 9. كشف المناطق المتغيرة
            changed_regions = self._detect_changed_regions(old_image, new_image)
            
            # 10. إنشاء خريطة الاختلافات المحسنة
            difference_map_path = None
            if output_dir:
                difference_map_path = self._create_enhanced_difference_map(
                    old_image, new_image, output_dir, 
                    Path(old_image_path).stem, Path(new_image_path).stem,
                    changed_regions
                )
            
            # 11. حساب إحصائيات إضافية
            mse = self._calculate_mse(old_image, new_image)
            psnr = self._calculate_psnr(mse)
            
            # 12. تحليل النتائج المحسن
            difference_detected = overall_similarity < (self.similarity_threshold * 100)
            major_changes = overall_similarity < 60  # عتبة أقل للتغييرات الكبيرة
            probable_content_match = overall_similarity > (self.high_similarity_threshold * 100)
            
            # 13. تحليل محسن مع ملاحظات الثقة
            analysis_summary = self._generate_enhanced_analysis_summary(
                overall_similarity, ssim_score, phash_score, clip_score, 
                histogram_correlation, feature_matching_score, edge_similarity,
                difference_detected, content_type
            )
            
            recommendations = self._generate_enhanced_recommendations(
                overall_similarity, major_changes, difference_detected, 
                probable_content_match, content_type
            )
            
            confidence_notes = self._generate_confidence_notes(
                ssim_score, phash_score, feature_matching_score, overall_similarity
            )
            
            # حساب وقت المعالجة
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = VisualComparisonResult(
                similarity_score=round(overall_similarity, 2),
                ssim_score=round(ssim_score, 3),
                phash_score=round(phash_score, 3),
                clip_score=round(clip_score, 3) if clip_score else None,
                histogram_correlation=round(histogram_correlation, 3),
                feature_matching_score=round(feature_matching_score, 3),
                edge_similarity=round(edge_similarity, 3),
                layout_similarity=round(layout_similarity, 3),
                text_region_overlap=round(text_region_overlap, 3),
                weights_used={
                    "ssim": self.ssim_weight,
                    "phash": self.phash_weight,
                    "clip": self.clip_weight,
                    "histogram": self.histogram_weight,
                    "features": self.feature_weight,
                    "edges": self.edge_weight
                },
                processing_time=processing_time,
                old_image_path=old_image_path,
                new_image_path=new_image_path,
                old_image_size=old_size,
                new_image_size=new_size,
                difference_detected=difference_detected,
                difference_map_path=difference_map_path,
                major_changes_detected=major_changes,
                changed_regions=changed_regions,
                mean_squared_error=mse,
                peak_signal_noise_ratio=psnr,
                content_type_detected=content_type,
                probable_content_match=probable_content_match,
                analysis_summary=analysis_summary,
                recommendations=recommendations,
                confidence_notes=confidence_notes
            )
            
            logger.info(f"✅ المقارنة البصرية المحسنة: {overall_similarity:.1f}% تطابق في {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ خطأ في المقارنة البصرية: {e}")
            
            return VisualComparisonResult(
                similarity_score=0.0,
                ssim_score=0.0,
                phash_score=0.0,
                processing_time=processing_time,
                old_image_path=old_image_path,
                new_image_path=new_image_path,
                analysis_summary=f"فشل في المقارنة: {str(e)}",
                recommendations="يرجى التحقق من صحة الملفات وإعادة المحاولة",
                confidence_notes="لا يمكن تحديد مستوى الثقة بسبب الخطأ"
            )
    
    def _load_and_preprocess_image(self, image_path: str) -> np.ndarray:
        """تحميل ومعالجة الصورة"""
        # قراءة الصورة
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"فشل في قراءة الصورة: {image_path}")
        
        # تحويل إلى رمادي
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # تحسين الجودة
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        
        return gray
    
    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """حساب SSIM بين صورتين"""
        try:
            # تغيير حجم الصور لتتطابق
            if img1.shape != img2.shape:
                target_shape = (min(img1.shape[1], img2.shape[1]), 
                               min(img1.shape[0], img2.shape[0]))
                img1 = cv2.resize(img1, target_shape)
                img2 = cv2.resize(img2, target_shape)
            
            # حساب SSIM
            score, _ = ssim(img1, img2, full=True)
            return max(0.0, min(1.0, score))  # تأكد من أن النتيجة بين 0 و 1
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حساب SSIM: {e}")
            return 0.0
    
    def _calculate_phash_similarity(self, img1_path: str, img2_path: str) -> float:
        """حساب تشابه pHash بين صورتين"""
        try:
            # تحميل الصور باستخدام PIL
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            
            # حساب pHash
            hash1 = imagehash.phash(img1)
            hash2 = imagehash.phash(img2)
            
            # حساب المسافة والتحويل إلى تشابه
            distance = hash1 - hash2
            max_distance = 64  # الحد الأقصى لمسافة pHash
            similarity = 1.0 - (distance / max_distance)
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حساب pHash: {e}")
            return 0.0
    
    def _calculate_clip_similarity(self, img1_path: str, img2_path: str) -> Optional[float]:
        """حساب تشابه CLIP بين صورتين"""
        if not self.clip_available:
            return None
        
        try:
            # تحميل الصور
            img1 = Image.open(img1_path).convert('RGB')
            img2 = Image.open(img2_path).convert('RGB')
            
            # الحصول على embeddings
            embeddings = self.clip_model.encode([img1, img2])
            
            # حساب cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حساب CLIP: {e}")
            return None
    
    def _calculate_histogram_correlation(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """حساب ارتباط الهستوجرام"""
        try:
            # تحويل الصور إلى هستوجرام
            hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])
            
            # حساب ارتباط الهستوجرام
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            return max(0.0, min(1.0, correlation))
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حساب ارتباط الهستوجرام: {e}")
            return 0.0
    
    def _calculate_feature_matching(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """حساب تطابق الميزات"""
        try:
            # إنشاء محولات SIFT
            kp1, des1 = self.sift.detectAndCompute(img1, None)
            kp2, des2 = self.sift.detectAndCompute(img2, None)
            
            # حساب تطابق الميزات
            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
            matches = bf.match(des1, des2)
            
            # حساب متوسط المسافة بين الميزات المتطابقة
            if len(matches) > 0:
                distances = [m.distance for m in matches]
                feature_matching_score = 1.0 - (np.mean(distances) / 256.0)
            else:
                feature_matching_score = 0.0
            
            return max(0.0, min(1.0, feature_matching_score))
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حساب تطابق الميزات: {e}")
            return 0.0
    
    def _calculate_edge_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """حساب تشابه الحواف"""
        try:
            # تحويل إلى رمادي إذا لزم الأمر
            if len(img1.shape) == 3:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            else:
                gray1 = img1.copy()
                
            if len(img2.shape) == 3:
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            else:
                gray2 = img2.copy()
            
            # توحيد الأحجام
            h1, w1 = gray1.shape
            h2, w2 = gray2.shape
            
            if (h1, w1) != (h2, w2):
                # تغيير حجم الصورة الثانية لتطابق الأولى
                gray2 = cv2.resize(gray2, (w1, h1))
            
            # إنشاء محولات حواف
            edges1 = cv2.Canny(gray1, 100, 200)
            edges2 = cv2.Canny(gray2, 100, 200)
            
            # حساب تشابه الحواف باستخدام SSIM للحواف
            from skimage.metrics import structural_similarity as ssim
            similarity = ssim(edges1, edges2)
            
            # تحويل إلى قيمة موجبة بين 0 و 1
            return max(0.0, min(1.0, (similarity + 1) / 2))
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حساب تشابه الحواف: {e}")
            return 0.0
    
    def _analyze_layout_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """تحليل تشابه التخطيط"""
        try:
            # تحويل الصور إلى مستوى أبيض وأسود (مع فحص القنوات)
            if len(img1.shape) == 3:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            else:
                gray1 = img1.copy()
                
            if len(img2.shape) == 3:
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            else:
                gray2 = img2.copy()
            
            # حساب تشابه التخطيط
            similarity = cv2.matchShapes(gray1, gray2, cv2.CONTOURS_MATCH_I2, 0)
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في تحليل تشابه التخطيط: {e}")
            return 0.0
    
    def _analyze_text_regions(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """تحليل تداخل مناطق النص"""
        try:
            # تحويل الصور إلى مستوى أبيض وأسود (مع فحص القنوات)
            if len(img1.shape) == 3:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            else:
                gray1 = img1.copy()
                
            if len(img2.shape) == 3:
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            else:
                gray2 = img2.copy()
            
            # تحويل الصور إلى مستوى ثنائي
            _, thresh1 = cv2.threshold(gray1, 127, 255, cv2.THRESH_BINARY)
            _, thresh2 = cv2.threshold(gray2, 127, 255, cv2.THRESH_BINARY)
            
            # توحيد الأحجام
            h1, w1 = thresh1.shape
            h2, w2 = thresh2.shape
            
            if (h1, w1) != (h2, w2):
                thresh2 = cv2.resize(thresh2, (w1, h1))
            
            # حساب تداخل مناطق النص
            intersection = cv2.bitwise_and(thresh1, thresh2)
            union = cv2.bitwise_or(thresh1, thresh2)
            
            intersection_count = cv2.countNonZero(intersection)
            union_count = cv2.countNonZero(union)
            
            if union_count == 0:
                overlap = 1.0  # إذا لم تكن هناك مناطق نص في أي من الصورتين
            else:
                overlap = intersection_count / union_count
            
            return max(0.0, min(1.0, overlap))
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في تحليل تداخل مناطق النص: {e}")
            return 0.0
    
    def _calculate_weighted_similarity(
        self, 
        ssim_score: float, 
        phash_score: float, 
        clip_score: Optional[float]
    ) -> float:
        """حساب النتيجة الإجمالية بالأوزان"""
        
        total_score = (
            ssim_score * self.ssim_weight +
            phash_score * self.phash_weight
        )
        
        if clip_score is not None and self.clip_weight > 0:
            total_score += clip_score * self.clip_weight
        
        return total_score * 100  # تحويل إلى نسبة مئوية
    
    def _calculate_enhanced_weighted_similarity(
        self, 
        ssim_score: float, 
        phash_score: float, 
        clip_score: Optional[float],
        histogram_correlation: float,
        feature_matching_score: float,
        edge_similarity: float
    ) -> float:
        """حساب النتيجة الإجمالية المحسنة"""
        
        total_score = (
            ssim_score * self.ssim_weight +
            phash_score * self.phash_weight +
            histogram_correlation * self.histogram_weight +
            feature_matching_score * self.feature_weight +
            edge_similarity * self.edge_weight
        )
        
        if clip_score is not None and self.clip_weight > 0:
            total_score += clip_score * self.clip_weight
        
        return total_score * 100  # تحويل إلى نسبة مئوية
    
    def _create_difference_map(
        self, 
        img1: np.ndarray, 
        img2: np.ndarray, 
        output_dir: str,
        name1: str, 
        name2: str
    ) -> str:
        """إنشاء خريطة الاختلافات"""
        try:
            # تغيير حجم الصور لتتطابق
            if img1.shape != img2.shape:
                target_shape = (min(img1.shape[1], img2.shape[1]), 
                               min(img1.shape[0], img2.shape[0]))
                img1 = cv2.resize(img1, target_shape)
                img2 = cv2.resize(img2, target_shape)
            
            # حساب الاختلاف المطلق
            diff = cv2.absdiff(img1, img2)
            
            # تطبيق threshold لإبراز الاختلافات
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # إنشاء خريطة ملونة للاختلافات
            diff_colored = cv2.applyColorMap(thresh, cv2.COLORMAP_JET)
            
            # حفظ الخريطة
            os.makedirs(output_dir, exist_ok=True)
            diff_path = os.path.join(output_dir, f"diff_{name1}_vs_{name2}.png")
            cv2.imwrite(diff_path, diff_colored)
            
            return diff_path
            
        except Exception as e:
            logger.warning(f"⚠️ فشل في إنشاء خريطة الاختلافات: {e}")
            return None
    
    def _calculate_mse(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """حساب Mean Squared Error"""
        try:
            if img1.shape != img2.shape:
                target_shape = (min(img1.shape[1], img2.shape[1]), 
                               min(img1.shape[0], img2.shape[0]))
                img1 = cv2.resize(img1, target_shape)
                img2 = cv2.resize(img2, target_shape)
            
            mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
            return float(mse)
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حساب MSE: {e}")
            return 0.0
    
    def _calculate_psnr(self, mse: float) -> float:
        """حساب Peak Signal-to-Noise Ratio"""
        if mse == 0:
            return float('inf')
        
        max_pixel_value = 255.0
        psnr = 20 * np.log10(max_pixel_value / np.sqrt(mse))
        return float(psnr)
    
    def _generate_analysis_summary(
        self, 
        overall_similarity: float,
        ssim_score: float,
        phash_score: float,
        clip_score: Optional[float],
        difference_detected: bool
    ) -> str:
        """إنشاء ملخص التحليل"""
        
        summary_parts = [
            f"التشابه الإجمالي: {overall_similarity:.1f}%",
            f"التشابه الهيكلي (SSIM): {ssim_score:.3f}",
            f"التشابه البصري (pHash): {phash_score:.3f}"
        ]
        
        if clip_score is not None:
            summary_parts.append(f"التشابه الدلالي (CLIP): {clip_score:.3f}")
        
        if difference_detected:
            summary_parts.append("تم اكتشاف اختلافات ملحوظة بين الصورتين")
        else:
            summary_parts.append("الصورتان متشابهتان إلى حد كبير")
        
        return ". ".join(summary_parts)
    
    def _generate_recommendations(
        self, 
        overall_similarity: float,
        major_changes: bool,
        difference_detected: bool
    ) -> str:
        """إنشاء التوصيات"""
        
        if major_changes:
            return "تم اكتشاف تغييرات كبيرة. يُنصح بمراجعة شاملة للمحتوى وتحديث المواد التعليمية"
        elif difference_detected:
            return "تم اكتشاف تغييرات طفيفة. يُنصح بمراجعة المناطق المختلفة وتقييم الحاجة للتحديث"
        else:
            return "الصورتان متشابهتان جداً. لا توجد حاجة لتحديثات كبيرة"
    
    async def health_check(self) -> Dict[str, Any]:
        """فحص صحة خدمة المقارنة البصرية"""
        try:
            return {
                "status": "healthy",
                "message": "Visual Comparison Service جاهز",
                "clip_available": self.clip_available,
                "weights": {
                    "ssim": self.ssim_weight,
                    "phash": self.phash_weight,
                    "clip": self.clip_weight
                },
                "similarity_threshold": self.similarity_threshold
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"خطأ في Visual Comparison Service: {str(e)}",
                "error": str(e)
            }

    def _detect_content_type(self, img1: np.ndarray, img2: np.ndarray) -> str:
        """كشف نوع المحتوى"""
        try:
            # تحليل بسيط لنوع المحتوى بناء على نسبة الأبيض
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if len(img1.shape) == 3 else img1
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY) if len(img2.shape) == 3 else img2
            
            white_ratio1 = np.sum(gray1 > 200) / gray1.size
            white_ratio2 = np.sum(gray2 > 200) / gray2.size
            
            if white_ratio1 > 0.7 and white_ratio2 > 0.7:
                return "educational_text"
            elif white_ratio1 > 0.4 and white_ratio2 > 0.4:
                return "mixed_content"
            else:
                return "visual_content"
                
        except Exception as e:
            logger.warning(f"⚠️ خطأ في كشف نوع المحتوى: {e}")
            return "unknown"
    
    def _detect_changed_regions(self, img1: np.ndarray, img2: np.ndarray) -> List[Dict[str, Any]]:
        """كشف المناطق المتغيرة"""
        try:
            # توحيد الأحجام أولاً
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            if (h1, w1) != (h2, w2):
                img2_resized = cv2.resize(img2, (w1, h1))
            else:
                img2_resized = img2.copy()
            
            # التأكد من تطابق عدد القنوات
            if len(img1.shape) != len(img2_resized.shape):
                if len(img1.shape) == 3 and len(img2_resized.shape) == 2:
                    img2_resized = cv2.cvtColor(img2_resized, cv2.COLOR_GRAY2BGR)
                elif len(img1.shape) == 2 and len(img2_resized.shape) == 3:
                    img1 = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR)
            
            # حساب الاختلاف
            diff = cv2.absdiff(img1, img2_resized)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY) if len(diff.shape) == 3 else diff
            
            # تحديد عتبة للتغيير
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            
            # العثور على المناطق المتغيرة
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            changed_regions = []
            for i, contour in enumerate(contours):
                if cv2.contourArea(contour) > 100:  # تجاهل التغييرات الصغيرة
                    x, y, w, h = cv2.boundingRect(contour)
                    area = cv2.contourArea(contour)
                    changed_regions.append({
                        "id": f"region_{i}",
                        "x": int(x),
                        "y": int(y),
                        "width": int(w),
                        "height": int(h),
                        "area": int(area),
                        "center": {"x": int(x + w/2), "y": int(y + h/2)}
                    })
            
            return changed_regions
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في كشف المناطق المتغيرة: {e}")
            return []
    
    def _create_enhanced_difference_map(
        self, 
        img1: np.ndarray, 
        img2: np.ndarray, 
        output_dir: str,
        name1: str, 
        name2: str,
        changed_regions: List[Dict[str, Any]]
    ) -> str:
        """إنشاء خريطة اختلافات محسنة"""
        try:
            # إنشاء مسار الإخراج
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            diff_filename = f"difference_map_{name1}_vs_{name2}_{timestamp}.png"
            diff_path = os.path.join(output_dir, diff_filename)
            
            # التأكد من تطابق الأحجام
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            if (h1, w1) != (h2, w2):
                # تغيير حجم الصورة الثانية لتطابق الأولى
                img2_resized = cv2.resize(img2, (w1, h1))
            else:
                img2_resized = img2.copy()
            
            # التأكد من تطابق عدد القنوات
            if len(img1.shape) != len(img2_resized.shape):
                if len(img1.shape) == 3 and len(img2_resized.shape) == 2:
                    img2_resized = cv2.cvtColor(img2_resized, cv2.COLOR_GRAY2BGR)
                elif len(img1.shape) == 2 and len(img2_resized.shape) == 3:
                    img1 = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR)
            
            # حساب الاختلاف
            diff = cv2.absdiff(img1, img2_resized)
            
            # تحسين عرض الاختلافات
            diff_enhanced = cv2.convertScaleAbs(diff, alpha=2.0, beta=30)
            
            # إضافة معرفات للمناطق المتغيرة
            diff_with_regions = diff_enhanced.copy()
            for region in changed_regions:
                x, y, w, h = region["x"], region["y"], region["width"], region["height"]
                cv2.rectangle(diff_with_regions, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(diff_with_regions, f"R{region['id'][-1]}", 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # حفظ الصورة
            cv2.imwrite(diff_path, diff_with_regions)
            logger.info(f"💾 تم حفظ خريطة الاختلافات: {diff_path}")
            
            return diff_path
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء خريطة الاختلافات: {e}")
            return ""
    
    def _generate_enhanced_analysis_summary(
        self, 
        overall_similarity: float,
        ssim_score: float,
        phash_score: float,
        clip_score: Optional[float],
        histogram_correlation: float,
        feature_matching_score: float,
        edge_similarity: float,
        difference_detected: bool,
        content_type: str
    ) -> str:
        """إنشاء ملخص تحليل محسن"""
        
        analysis_parts = []
        
        # تحليل النتيجة الإجمالية
        if overall_similarity >= 95:
            analysis_parts.append("🎯 الصور متطابقة تقريباً بنسبة عالية جداً")
        elif overall_similarity >= 85:
            analysis_parts.append("✅ الصور متشابهة بدرجة عالية مع اختلافات طفيفة")
        elif overall_similarity >= 70:
            analysis_parts.append("⚠️ الصور متشابهة بدرجة متوسطة مع وجود اختلافات ملحوظة")
        elif overall_similarity >= 50:
            analysis_parts.append("🔍 الصور مختلفة بدرجة كبيرة مع بعض أوجه التشابه")
        else:
            analysis_parts.append("❌ الصور مختلفة تماماً")
        
        # تحليل تفصيلي
        metrics_details = []
        metrics_details.append(f"SSIM: {ssim_score:.3f}")
        metrics_details.append(f"pHash: {phash_score:.3f}")
        if clip_score is not None:
            metrics_details.append(f"CLIP: {clip_score:.3f}")
        metrics_details.append(f"Histogram: {histogram_correlation:.3f}")
        metrics_details.append(f"Features: {feature_matching_score:.3f}")
        metrics_details.append(f"Edges: {edge_similarity:.3f}")
        
        analysis_parts.append(f"📊 المقاييس التفصيلية: {' | '.join(metrics_details)}")
        
        # تحليل نوع المحتوى
        content_analysis = {
            "educational_text": "📚 محتوى تعليمي نصي",
            "mixed_content": "📝 محتوى مختلط (نص وصور)",
            "visual_content": "🖼️ محتوى بصري",
            "unknown": "❓ نوع محتوى غير محدد"
        }
        
        analysis_parts.append(f"🔍 نوع المحتوى: {content_analysis.get(content_type, content_type)}")
        
        return " • ".join(analysis_parts)
    
    def _generate_enhanced_recommendations(
        self, 
        overall_similarity: float,
        major_changes: bool,
        difference_detected: bool,
        probable_content_match: bool,
        content_type: str
    ) -> str:
        """إنشاء توصيات محسنة"""
        
        recommendations = []
        
        if probable_content_match:
            recommendations.append("✅ المحتوى متطابق تقريباً - يمكن اعتبارهما نفس المحتوى")
            recommendations.append("📋 ينصح بمراجعة سريعة للتأكد من عدم وجود تغييرات مهمة")
        elif overall_similarity >= 75:
            recommendations.append("🔍 هناك تشابه كبير مع وجود اختلافات")
            recommendations.append("📝 ينصح بمراجعة تفصيلية لتحديد طبيعة التغييرات")
            if content_type == "educational_text":
                recommendations.append("📚 قد تكون هناك تحديثات في المحتوى التعليمي")
        elif major_changes:
            recommendations.append("⚠️ هناك اختلافات كبيرة بين الصورتين")
            recommendations.append("🔄 ينصح بمراجعة شاملة وإعادة تقييم المحتوى")
            recommendations.append("📊 قد تحتاج لمراجعة يدوية مفصلة")
        else:
            recommendations.append("❌ الصور مختلفة بشكل كبير")
            recommendations.append("🆕 يبدو أن هناك محتوى جديد أو تغييرات جذرية")
        
        return " • ".join(recommendations)
    
    def _generate_confidence_notes(
        self, 
        ssim_score: float,
        phash_score: float,
        feature_matching_score: float,
        overall_similarity: float
    ) -> str:
        """إنشاء ملاحظات الثقة"""
        
        confidence_notes = []
        
        # تحليل SSIM
        if ssim_score >= 0.9:
            confidence_notes.append("🎯 ثقة عالية جداً في التشابه الهيكلي")
        elif ssim_score >= 0.7:
            confidence_notes.append("✅ ثقة جيدة في التشابه الهيكلي")
        elif ssim_score >= 0.5:
            confidence_notes.append("⚠️ ثقة متوسطة في التشابه الهيكلي")
        else:
            confidence_notes.append("❌ ثقة منخفضة في التشابه الهيكلي")
        
        # تحليل pHash
        if phash_score >= 0.9:
            confidence_notes.append("🔐 تطابق قوي في البصمة الرقمية")
        elif phash_score >= 0.7:
            confidence_notes.append("👍 تطابق جيد في البصمة الرقمية")
        else:
            confidence_notes.append("🔍 تطابق ضعيف في البصمة الرقمية")
        
        # تحليل الميزات
        if feature_matching_score >= 0.8:
            confidence_notes.append("🎲 تطابق ممتاز في الميزات البصرية")
        elif feature_matching_score >= 0.5:
            confidence_notes.append("📊 تطابق متوسط في الميزات البصرية")
        else:
            confidence_notes.append("📉 تطابق ضعيف في الميزات البصرية")
        
        # تقييم إجمالي
        if overall_similarity >= 90:
            confidence_notes.append("💯 مستوى ثقة عالي جداً في النتائج")
        elif overall_similarity >= 75:
            confidence_notes.append("✅ مستوى ثقة جيد في النتائج")
        elif overall_similarity >= 50:
            confidence_notes.append("⚠️ مستوى ثقة متوسط في النتائج")
        else:
            confidence_notes.append("❓ مستوى ثقة منخفض - ينصح بالمراجعة اليدوية")
        
        return " • ".join(confidence_notes)


# إنشاء instance واحد للخدمة
visual_comparison_service = EnhancedVisualComparisonService()
enhanced_visual_comparison_service = visual_comparison_service  # للتوافق مع الاستيراد 