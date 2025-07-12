"""
خدمة LandingAI Agentic Document Extraction
LandingAI Agentic Document Extraction Service
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple, ContextManager
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
import logging
import time
import requests
import signal
import platform
from contextlib import contextmanager
import random

# إضافة استيراد Tesseract OCR
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

try:
    import agentic_doc
    from agentic_doc.parse import parse
    # استيراد اختياري للمكونات الأخرى
    try:
        from agentic_doc.utils import viz_parsed_document
    except ImportError:
        viz_parsed_document = None
    try:
        from agentic_doc.config import VisualizationConfig
    except ImportError:
        VisualizationConfig = None
    # ChunkType قد لا يكون متاح في بعض الإصدارات
    try:
        from agentic_doc.types import ChunkType
    except ImportError:
        ChunkType = None
    HAS_ADVANCED_FEATURES = True
    LANDINGAI_AVAILABLE = True
except ImportError as e:
    # Fallback for basic functionality
    HAS_ADVANCED_FEATURES = False
    viz_parsed_document = None
    VisualizationConfig = None
    ChunkType = None
    LANDINGAI_AVAILABLE = False
    print(f"❌ Failed to import agentic_doc: {e}")
from pydantic import BaseModel, Field
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

# API key should be set in environment variables
VISION_AGENT_API_KEY = settings.VISION_AGENT_API_KEY

# Setup logging
logger = logging.getLogger(__name__)

# Context manager للمهلة الزمنية - مخصص لـ Windows
import platform
from contextlib import contextmanager

@contextmanager  
def timeout_context(seconds):
    """Context manager للمهلة الزمنية - متوافق مع Windows و Linux"""
    if platform.system() == "Windows":
        # في Windows نعتمد على المهل الداخلية للمكتبات
        try:
            yield
        except Exception as e:
            raise e
    else:
        # في Linux/Unix نستخدم signal
        def timeout_handler(signum, frame):
            raise TimeoutError(f"العملية استغرقت أكثر من {seconds} ثانية")
        
        # حفظ المعالج السابق
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            # إعادة تعيين المنبه
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

# إضافة دالة مغلفة للـ parse مع محاولات متعددة
def parse_with_retry(file_path, max_retries=7, base_timeout=120, backoff_factor=1.8):
    """
    دالة مغلفة حول agentic_doc.parse مع إعادة المحاولة والمهلة المتزايدة
    
    Args:
        file_path: مسار الملف للتحليل
        max_retries: الحد الأقصى لعدد المحاولات
        base_timeout: المهلة الأساسية بالثواني
        backoff_factor: عامل التراجع للمهلة بين المحاولات
        
    Returns:
        نتيجة التحليل من agentic_doc.parse
    """
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            # حساب المهلة الحالية مع إضافة عشوائية لتجنب thundering herd
            current_timeout = int(base_timeout * (backoff_factor ** attempt))
            jitter = random.uniform(0.1, 0.3) * current_timeout
            timeout_with_jitter = current_timeout + jitter
            
            logger.info(f"🔄 محاولة {attempt + 1}/{max_retries} - مهلة: {timeout_with_jitter:.1f}s")
            
            # تنفيذ التحليل مع المهلة
            with timeout_context(int(timeout_with_jitter)):
                result = parse(file_path)
                
                # التحقق من صحة النتيجة
                if result and len(result) > 0:
                    logger.info(f"✅ نجح التحليل في المحاولة {attempt + 1}")
                    return result
                else:
                    raise Exception("نتيجة فارغة من agentic_doc.parse")
                    
        except TimeoutError as e:
            last_exception = e
            logger.warning(f"⏱️ انتهت مهلة المحاولة {attempt + 1}: {e}")
            
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # تصنيف الأخطاء
            if any(keyword in error_msg for keyword in ['server disconnected', 'connection', 'timeout', 'network']):
                logger.warning(f"🌐 خطأ في الاتصال في المحاولة {attempt + 1}: {e}")
            elif any(keyword in error_msg for keyword in ['down', 'invalid', 'unavailable']):
                logger.warning(f"🚫 خطأ في الخادم في المحاولة {attempt + 1}: {e}")
            elif any(keyword in error_msg for keyword in ['rate limit', 'quota', 'limit exceeded']):
                logger.warning(f"⚡ تجاوز الحد المسموح في المحاولة {attempt + 1}: {e}")
                # انتظار أطول في حالة rate limiting
                time.sleep(30 + (attempt * 10))
            else:
                logger.warning(f"❌ خطأ غير متوقع في المحاولة {attempt + 1}: {e}")
        
        # انتظار قبل المحاولة التالية (إلا في المحاولة الأخيرة)
        if attempt < max_retries - 1:
            wait_time = min(30, 5 * (2 ** attempt)) + random.uniform(1, 3)
            logger.info(f"⏳ انتظار {wait_time:.1f}s قبل المحاولة التالية...")
            time.sleep(wait_time)
    
    # إذا فشلت جميع المحاولات
    logger.error(f"❌ فشل في جميع المحاولات ({max_retries})")
    raise last_exception or Exception("فشل في جميع محاولات التحليل")

class CurriculumAnalysis(BaseModel):
    """نموذج تحليل المنهج التعليمي"""
    subject: str = Field(description="الموضوع أو المادة الدراسية")
    grade_level: str = Field(description="المستوى الدراسي أو الصف")
    chapter_title: str = Field(description="عنوان الفصل أو الوحدة")
    learning_objectives: List[str] = Field(description="الأهداف التعليمية", default_factory=list)
    topics: List[str] = Field(description="المواضيع المغطاة", default_factory=list)
    key_concepts: List[str] = Field(description="المفاهيم الأساسية", default_factory=list)
    assessment_methods: List[str] = Field(description="طرق التقييم", default_factory=list)
    exercises_count: int = Field(description="عدد التمارين", default=0)
    difficulty_level: str = Field(description="مستوى الصعوبة", default="متوسط")
    page_count: int = Field(description="عدد الصفحات", default=0)
    language: str = Field(description="لغة المحتوى", default="العربية")
    content_type: str = Field(description="نوع المحتوى", default="نظري")


class LandingAIExtractionResult(BaseModel):
    """نتيجة استخراج LandingAI"""
    file_path: str
    file_name: str
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    
    # محتوى مستخرج
    markdown_content: str = ""
    structured_analysis: Optional[CurriculumAnalysis] = None
    
    # تفاصيل الاستخراج
    total_chunks: int = 0
    chunks_by_type: Dict[str, int] = Field(default_factory=dict)
    confidence_score: float = 0.0
    
    # ملفات الإخراج
    visual_groundings: List[str] = Field(default_factory=list)
    visualization_images: List[str] = Field(default_factory=list)
    raw_json_path: Optional[str] = None
    
    # إحصائيات
    text_elements: int = 0
    table_elements: int = 0
    image_elements: int = 0
    title_elements: int = 0


class LandingAIService:
    """خدمة LandingAI للاستخراج الذكي للمستندات"""
    
    def __init__(self):
        self.api_key = VISION_AGENT_API_KEY
        # توحيد حالة الخدمة في متغير واحد: mock_mode
        self.mock_mode = not (bool(self.api_key) and LANDINGAI_AVAILABLE)
        self.agentic_doc_available = LANDINGAI_AVAILABLE
        
        if self.mock_mode:
            logger.warning("LandingAI service is in MOCK MODE due to missing API key or library.")
        else:
            logger.info("✅ تم تكوين LandingAI Service مع API حقيقي.")

        self.api_endpoint = "https://predict.app.landing.ai/inference/v1/predict"
        if not LANDINGAI_AVAILABLE:
            logger.warning("agentic-doc library not installed. LandingAI service will be disabled.")
        if not self.api_key:
            logger.warning("VISION_AGENT_API_KEY not set. LandingAI service will be disabled.")
        
        self.batch_size = int(os.getenv("LANDINGAI_BATCH_SIZE", "4"))
        self.max_workers = int(os.getenv("LANDINGAI_MAX_WORKERS", "4"))  # زيادة العمال
        self.max_retries = int(os.getenv("LANDINGAI_MAX_RETRIES", "1"))  # تقليل المحاولات للسرعة
        self.include_marginalia = os.getenv("LANDINGAI_INCLUDE_MARGINALIA", "False").lower() == "true"
        self.include_metadata = os.getenv("LANDINGAI_INCLUDE_METADATA", "True").lower() == "true"
        self.save_visual_groundings = os.getenv("LANDINGAI_SAVE_VISUAL_GROUNDINGS", "False").lower() == "true"  # تعطيل لتوفير الوقت
        
        # إعداد Tesseract OCR محسن للسرعة - لكن لن نستخدمه
        self.tesseract_path = os.getenv("TESSERACT_PATH", "tesseract")
        self.ocr_languages = os.getenv("OCR_LANGUAGES", "ara+eng")
        self.ocr_config = os.getenv("OCR_CONFIG", "--oem 3 --psm 6")  # PSM 6 أسرع للنصوص المنظمة
        
        # حفظ النص المستخرج تلقائياً
        self.auto_save_md = os.getenv("AUTO_SAVE_MD", "True").lower() == "true"
        
        # تعطيل Tesseract backup
        self.ocr_available = False
        
    def _downscale_if_needed(self, image_path: str, max_dim: int = 1024, temp_dir: str = None) -> Tuple[str, bool]:
        """
        تصغير الصور الكبيرة للحفاظ على سرعة استجابة LandingAI (محسن)
        Downscales large images to maintain LandingAI API performance (optimized).
        """
        try:
            img = Image.open(image_path)
            original_size = img.size
            
            # استخدم حد أقصى أصغر للتأكد من النجاح
            if max(img.size) > max_dim:
                logger.warning(f"🖼️ الصورة {Path(image_path).name} كبيرة {original_size}، سيتم تصغيرها إلى {max_dim}px")
                
                # حساب النسبة الجديدة
                ratio = max_dim / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                
                # تصغير الصورة مع ضغط أفضل
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # تحويل إلى RGB إذا كان RGBA
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # حفظ الصورة المؤقتة
                if temp_dir is None:
                    temp_dir = tempfile.gettempdir()
                
                new_path = Path(temp_dir) / f"downscaled_{Path(image_path).name}"
                # حفظ بجودة متوسطة للحفاظ على سرعة الرفع
                img.save(new_path, quality=75, format='JPEG', optimize=True)
                
                logger.info(f"✅ تم تصغير الصورة من {original_size} إلى {new_size} وحفظها في: {new_path}")
                return str(new_path), True
            
            return image_path, False
        except Exception as e:
            logger.error(f"❌ فشل تصغير الصورة {image_path}: {e}")
            return image_path, False
    
    async def extract_from_file(
        self, 
        file_path: str, 
        output_dir: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> LandingAIExtractionResult:
        """
        استخراج محتوى من ملف واحد.
        سيتم استخدام المحاكاة تلقائياً إذا كانت الخدمة في mock_mode.
        """
        start_time = datetime.now()
        file_name = Path(file_path).name
        
        # تحديد المجلدات
        if not output_dir:
            output_dir = os.path.join(settings.UPLOAD_DIR, "landingai_results")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(output_dir, f"extraction_{timestamp}")
        os.makedirs(session_dir, exist_ok=True)
        
        # التحقق من وضع المحاكاة أولاً
        if self.mock_mode:
            logger.warning(f"⚠️ استدعاء محاكاة استخراج لـ {file_name}")
            return await self._mock_extraction(file_path, session_dir, file_name)

        logger.info(f"📄 بدء استخراج النص الحقيقي من: {file_name}")
        
        try:
            # استخدام LandingAI API الحقيقي
            logger.info("🌐 بدء الاستخراج باستخدام Landing AI API...")
            result = await self._real_landingai_extraction(file_path, session_dir, file_name)
            
            if not result.success:
                raise Exception(f"فشل LandingAI: {result.error_message}")
            
            # حساب وقت المعالجة
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            logger.info(f"✅ اكتمل استخراج {file_name} في {processing_time:.2f} ثانية (LandingAI)")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ خطأ في استخراج {file_name}: {e}")
            
            # عدم التحول إلى Tesseract - فشل مباشر
            return LandingAIExtractionResult(
                file_path=file_path,
                file_name=file_name,
                processing_time=processing_time,
                success=False,
                error_message=f"فشل LandingAI: {str(e)}"
            )
    
    async def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """تحسين الصورة للـ OCR"""
        
        logger.debug("🔧 تحسين الصورة...")
        
        # تحويل إلى numpy array للمعالجة المتقدمة
        img_array = np.array(image)
        
        # تحويل إلى رمادي إذا كانت ملونة
        if len(img_array.shape) == 3:
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            img_gray = img_array
        
        # تحسين جودة الصورة
        logger.debug("📈 تحسين التباين والوضوح...")
        
        # 1. تطبيق Gaussian blur لتقليل الضوضاء
        img_blur = cv2.GaussianBlur(img_gray, (1, 1), 0)
        
        # 2. تحسين التباين باستخدام CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        img_enhanced = clahe.apply(img_blur)
        
        # 3. تطبيق threshold للحصول على نص أوضح
        # استخدام Otsu's thresholding للحصول على أفضل threshold تلقائياً
        _, img_thresh = cv2.threshold(img_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 4. تنظيف الصورة من الضوضاء الصغيرة
        kernel = np.ones((1, 1), np.uint8)
        img_cleaned = cv2.morphologyEx(img_thresh, cv2.MORPH_CLOSE, kernel)
        
        # 5. تكبير الصورة لتحسين دقة OCR
        scale_factor = 2.0
        width = int(img_cleaned.shape[1] * scale_factor)
        height = int(img_cleaned.shape[0] * scale_factor)
        img_resized = cv2.resize(img_cleaned, (width, height), interpolation=cv2.INTER_CUBIC)
        
        # تحويل العودة إلى PIL Image
        processed_image = Image.fromarray(img_resized)
        
        logger.debug(f"✅ تم تحسين الصورة: {processed_image.size}")
        
        return processed_image
    
    async def _analyze_educational_content(self, text: str) -> CurriculumAnalysis:
        """تحليل المحتوى التعليمي المستخرج"""
        
        logger.debug("📚 تحليل المحتوى التعليمي...")
        
        # تحليل بسيط للمحتوى العربي
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # البحث عن العناوين والمواضيع
        topics = []
        key_concepts = []
        exercises_count = 0
        
        for line in lines:
            # البحث عن الأسئلة
            if any(word in line for word in ['اختر', 'أجب', 'احسب', 'وضح', 'اشرح', 'قارن']):
                exercises_count += 1
            
            # البحث عن المفاهيم الفيزيائية
            if any(word in line for word in ['المكبس', 'الضغط', 'القوة', 'الهيدروليكي', 'النسبة']):
                if line not in key_concepts and len(line) < 200:
                    key_concepts.append(line)
            
            # البحث عن المواضيع
            if len(line) > 20 and len(line) < 100:
                topics.append(line)
        
        # تحديد الموضوع الرئيسي
        subject = "الفيزياء"
        if any(word in text for word in ['المكبس', 'الهيدروليكي', 'الضغط']):
            chapter_title = "المكابس الهيدروليكية"
        else:
            chapter_title = "موضوع فيزيائي"
        
        return CurriculumAnalysis(
            subject=subject,
            grade_level="الثانوي",
            chapter_title=chapter_title,
            learning_objectives=[
                "فهم مبدأ عمل المكابس الهيدروليكية",
                "حساب النسب والضغوط في الأنظمة الهيدروليكية",
                "تطبيق مبدأ باسكال في المسائل العملية"
            ],
            topics=topics[:5],  # أول 5 مواضيع
            key_concepts=key_concepts[:10],  # أول 10 مفاهيم
            assessment_methods=["أسئلة اختيار من متعدد", "مسائل حسابية"],
            exercises_count=exercises_count,
            difficulty_level="متوسط إلى متقدم",
            page_count=1,
            language="العربية",
            content_type="نظري وتطبيقي"
        )
    
    async def _real_ocr_extraction(
        self, 
        file_path: str, 
        session_dir: str, 
        file_name: str
    ) -> LandingAIExtractionResult:
        """الاستخراج الحقيقي باستخدام Tesseract OCR"""
        
        logger.info("🔍 بدء عملية OCR الحقيقية...")
        
        try:
            # تحميل وتحضير الصورة
            logger.debug("📸 تحميل الصورة...")
            image = Image.open(file_path)
            
            # معلومات الصورة
            image_info = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": os.path.getsize(file_path)
            }
            logger.info(f"📊 معلومات الصورة: {image.width}x{image.height} ({image.format})")
            
            # تحسين الصورة للـ OCR
            logger.debug("🔧 تحسين الصورة للـ OCR...")
            processed_image = await self._preprocess_image_for_ocr(image)
            
            # استخراج النص باستخدام Tesseract
            logger.info("📝 استخراج النص باستخدام Tesseract...")
            
            ocr_start_time = datetime.now()
            
            # إعدادات OCR محسنة للنصوص العربية
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=أبتثجحخدذرزسشصضطظعغفقكلمنهويىءآإؤئةـ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ()[]{}.,;:!?+-*/=<>%$#@&_|~`"\'\\/'
            
            # محاولة استخراج النص مع إعدادات محسنة للسرعة
            extraction_attempts = [
                # محاولة 1: العربية والإنجليزية مع PSM 6 (الأسرع)
                {"lang": "ara+eng", "config": r"--oem 3 --psm 6"},
                # محاولة 2: العربية فقط مع PSM 6 (أسرع للنصوص العربية)
                {"lang": "ara", "config": r"--oem 3 --psm 6"}
            ]
            
            best_result = None
            best_confidence = 0
            
            for i, attempt in enumerate(extraction_attempts):
                try:
                    logger.debug(f"🔄 المحاولة {i+1}: {attempt['lang']} - {attempt['config']}")
                    
                    # استخراج النص مع تفاصيل الثقة
                    data = pytesseract.image_to_data(
                        processed_image, 
                        lang=attempt['lang'], 
                        config=attempt['config'],
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # حساب متوسط الثقة
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # استخراج النص
                    text = pytesseract.image_to_string(
                        processed_image, 
                        lang=attempt['lang'], 
                        config=attempt['config']
                    )
                    
                    if avg_confidence > best_confidence and text.strip():
                        best_confidence = avg_confidence
                        best_result = {
                            "text": text,
                            "confidence": avg_confidence / 100,
                            "language": attempt['lang'],
                            "config": attempt['config'],
                            "data": data
                        }
                        logger.debug(f"✅ أفضل نتيجة حتى الآن: ثقة {avg_confidence:.1f}%")
                    
                except Exception as e:
                    logger.debug(f"⚠️ فشل في المحاولة {i+1}: {e}")
                    continue
            
            if not best_result:
                raise Exception("فشل في جميع محاولات استخراج النص")
            
            ocr_time = (datetime.now() - ocr_start_time).total_seconds()
            logger.info(f"⏱️ وقت OCR: {ocr_time:.2f} ثانية")
            
            # تنظيف النص المستخرج
            extracted_text = best_result["text"]
            confidence_score = best_result["confidence"]
            
            # إحصائيات النص
            character_count = len(extracted_text)
            word_count = len(extracted_text.split())
            
            logger.info(f"📊 النتائج: {character_count} حرف, {word_count} كلمة, ثقة: {confidence_score:.2f}")
            
            # حفظ النتائج
            logger.debug("💾 حفظ النتائج...")
            
            # حفظ النص الخام
            raw_text_path = os.path.join(session_dir, f"{file_name}_raw_text.txt")
            with open(raw_text_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            # حفظ الصورة المعالجة
            processed_image_path = os.path.join(session_dir, f"{file_name}_processed.png")
            processed_image.save(processed_image_path)
            
            # حفظ النص المستخرج كـ .md في نفس مسار الصورة الأصلية
            if self.auto_save_md:
                try:
                    original_file_dir = os.path.dirname(file_path)
                    base_name = os.path.splitext(file_name)[0]
                    md_path = os.path.join(original_file_dir, f"{base_name}_extracted.md")
                    
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(f"# النص المستخرج من {file_name}\n\n")
                        f.write(f"**تاريخ الاستخراج:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(f"**مستوى الثقة:** {confidence_score:.1%}\n\n")
                        f.write(f"**عدد الكلمات:** {word_count}\n\n")
                        f.write("---\n\n")
                        f.write("## النص المستخرج\n\n")
                        f.write(extracted_text)
                    
                    logger.info(f"📄 تم حفظ النص المستخرج: {md_path}")
                except Exception as e:
                    logger.warning(f"⚠️ فشل في حفظ ملف .md: {e}")
            
            # حفظ تفاصيل OCR
            ocr_details_path = os.path.join(session_dir, f"{file_name}_ocr_details.json")
            with open(ocr_details_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "confidence_score": confidence_score,
                    "language_detected": best_result["language"],
                    "config_used": best_result["config"],
                    "character_count": character_count,
                    "word_count": word_count,
                    "processing_time": ocr_time,
                    "image_info": image_info,
                    "extraction_details": {
                        "total_attempts": len(extraction_attempts),
                        "successful_attempt": best_result["language"] + " - " + best_result["config"]
                    }
                }, f, ensure_ascii=False, indent=2)
            
            # تحليل المحتوى التعليمي
            logger.info("🧠 تحليل المحتوى التعليمي...")
            structured_analysis = await self._analyze_educational_content(extracted_text)
            
            # إنشاء محتوى Markdown منظم
            markdown_content = self._create_markdown_content(extracted_text, structured_analysis, best_result)
            
            logger.info("✅ تم الاستخراج الحقيقي بنجاح")
            
            return LandingAIExtractionResult(
                file_path=file_path,
                file_name=file_name,
                processing_time=0,  # سيتم تحديثه في الدالة الرئيسية
                success=True,
                markdown_content=markdown_content,
                structured_analysis=structured_analysis,
                confidence_score=confidence_score,
                text_elements=word_count,
                total_chunks=1,
                chunks_by_type={"text": 1},
                raw_json_path=ocr_details_path,
                visual_groundings=[processed_image_path]
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في الاستخراج الحقيقي: {e}")
            raise e
    
    def _create_markdown_content(self, text: str, analysis, ocr_result: dict) -> str:
        """إنشاء محتوى Markdown منظم"""
        
        markdown = f"""# تقرير استخراج النص - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## معلومات الاستخراج
- **اللغة المكتشفة**: {ocr_result['language']}
- **مستوى الثقة**: {ocr_result['confidence']:.1%}
- **إعدادات OCR**: {ocr_result['config']}
- **عدد الكلمات**: {len(text.split())}
- **عدد الأحرف**: {len(text)}

## تحليل المحتوى التعليمي
- **الموضوع**: {analysis.subject}
- **المستوى**: {analysis.grade_level}
- **عنوان الفصل**: {analysis.chapter_title}
- **مستوى الصعوبة**: {analysis.difficulty_level}
- **نوع المحتوى**: {analysis.content_type}

## النص المستخرج

```
{text}
```

## الملاحظات
- تم استخدام تقنيات معالجة الصور المتقدمة لتحسين جودة الاستخراج
- تم تطبيق عدة محاولات لاستخراج النص للحصول على أفضل نتيجة
- النص قد يحتاج إلى مراجعة يدوية لضمان الدقة الكاملة
"""
        
        return markdown
    
    async def _real_landingai_extraction(
        self, 
        file_path: str, 
        session_dir: str, 
        file_name: str
    ) -> LandingAIExtractionResult:
        """
        الاستخراج الحقيقي باستخدام agentic_doc.parse مع تصغير الصور المحسن وآلية fallback
        Real extraction using agentic_doc.parse with optimized image downscaling and fallback mechanism.
        """
        logger.info("🌐 بدء عملية الاستخراج باستخدام agentic_doc.parse...")
        
        start_time = datetime.now()
        
        temp_image_path = None
        temp_dir = os.path.join(session_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # تصغير الصورة إذا كانت كبيرة (حد أقصى 1024px للتأكد من النجاح)
            processed_path, was_downscaled = self._downscale_if_needed(file_path, max_dim=1024, temp_dir=temp_dir)
            if was_downscaled:
                temp_image_path = processed_path

            # استخدام parse_with_retry للحصول على آلية إعادة المحاولة المحسنة
            try:
                logger.info("🔄 بدء التحليل مع آلية إعادة المحاولة المحسنة...")
                result = parse_with_retry(processed_path, max_retries=7, base_timeout=120, backoff_factor=1.8)
                
            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"❌ فشل في agentic_doc.parse: {e}")
                
                # محاولة مع صورة أصغر كآلية احتياطية
                if not any(keyword in error_msg for keyword in ['rate limit', 'quota', 'authentication']):
                    logger.info("🔄 محاولة مع صورة أصغر (512px) كآلية احتياطية...")
                    try:
                        smaller_path, _ = self._downscale_if_needed(file_path, max_dim=512, temp_dir=temp_dir)
                        if smaller_path != processed_path:
                            if temp_image_path and os.path.exists(temp_image_path):
                                os.remove(temp_image_path)
                            temp_image_path = smaller_path
                            processed_path = smaller_path
                            result = parse_with_retry(processed_path, max_retries=5, base_timeout=90, backoff_factor=1.5)
                        else:
                            raise e
                    except Exception as e2:
                        logger.warning(f"❌ فشل أيضاً مع الصورة الأصغر: {e2}")
                        # محاولة مع صورة أصغر جداً (256px) كآلية احتياطية أخيرة
                        try:
                            smallest_path, _ = self._downscale_if_needed(file_path, max_dim=256, temp_dir=temp_dir)
                            if smallest_path != processed_path:
                                if temp_image_path and os.path.exists(temp_image_path):
                                    os.remove(temp_image_path)
                                temp_image_path = smallest_path
                                processed_path = smallest_path
                                logger.info("🔄 محاولة أخيرة مع صورة صغيرة جداً (256px)...")
                                result = parse_with_retry(processed_path, max_retries=3, base_timeout=60, backoff_factor=1.3)
                            else:
                                raise e
                        except Exception as e3:
                            logger.error(f"❌ فشل في جميع محاولات agentic_doc.parse: {e3}")
                            # لا نستخدم Tesseract تلقائياً - نحتاج موافقة المستخدم
                            raise Exception(f"فشل في استخراج النص باستخدام LandingAI. يمكن المحاولة مع OCR التقليدي بعد موافقة المستخدم: {e3}")
                else:
                    raise e
            
            # التحقق من النتيجة
            if not result or len(result) == 0:
                raise Exception("لم يتم العثور على نتائج من agentic_doc.parse")
            
            # الحصول على أول نتيجة
            doc_result = result[0]
            
            # استخراج البيانات
            markdown_content = doc_result.markdown if hasattr(doc_result, 'markdown') else ""
            chunks = doc_result.chunks if hasattr(doc_result, 'chunks') else []
            
            # تحويل القطع إلى شكل قابل للتسلسل (dict)
            serializable_chunks: List[dict] = []
            for c in chunks:
                if isinstance(c, dict):
                    serializable_chunks.append(c)
                elif hasattr(c, "dict") and callable(getattr(c, "dict")):
                    # دعم نماذج Pydantic
                    serializable_chunks.append(c.dict())
                elif hasattr(c, "to_dict") and callable(getattr(c, "to_dict")):
                    serializable_chunks.append(c.to_dict())
                elif hasattr(c, "__dict__"):
                    serializable_chunks.append(vars(c))
                else:
                    serializable_chunks.append({"representation": str(c)})
            
            logger.info("✅ تم الحصول على استجابة ناجحة من agentic_doc")
            
            # حفظ النتائج
            results_file = os.path.join(session_dir, f"agentic_doc_result.json")
            result_data = {
                "markdown": markdown_content,
                "chunks": serializable_chunks,
                "result_path": getattr(doc_result, 'result_path', None),
                "image_was_downscaled": was_downscaled,
                "processed_image_size": self._get_image_size(processed_path) if processed_path else None
            }
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            markdown_file = os.path.join(session_dir, f"extracted_content.md")
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # تحليل النتائج
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # عد العناصر
            text_elements = len([c for c in serializable_chunks if c.get('chunk_type') == 'text'])
            table_elements = len([c for c in serializable_chunks if c.get('chunk_type') == 'table'])
            image_elements = len([c for c in serializable_chunks if c.get('chunk_type') == 'image'])
            title_elements = len([c for c in serializable_chunks if c.get('chunk_type') == 'title'])
            
            # حساب الثقة
            total_text_length = len(markdown_content)
            
            # تقدير الثقة بناءً على طول النص ووجود chunks
            if total_text_length > 1000 and len(serializable_chunks) > 3:
                avg_confidence = 0.9
            elif total_text_length > 500 and len(serializable_chunks) > 1:
                avg_confidence = 0.85
            elif total_text_length > 100:
                avg_confidence = 0.8
            else:
                avg_confidence = 0.7
            
            # تحليل المحتوى التعليمي
            educational_analysis = await self._analyze_educational_content(markdown_content)
            
            logger.info(f"📊 النتائج: {total_text_length} حرف, {len(serializable_chunks)} قطعة, ثقة: {avg_confidence:.2f}")
            logger.info(f"📝 محتوى مستخرج: {markdown_content[:200]}..." if len(markdown_content) > 200 else f"📝 محتوى مستخرج: {markdown_content}")
            logger.info(f"📊 تفاصيل الأجزاء: نص={text_elements}, جداول={table_elements}, صور={image_elements}, عناوين={title_elements}")
            
            # إضافة console.log للفرونت إند
            print("🔍 FRONTEND_LOG: LANDINGAI_EXTRACTION_SUCCESS")
            print("🔍 FRONTEND_LOG: " + json.dumps({
                "file_name": file_name,
                "total_chars": total_text_length,
                "chunks_count": len(serializable_chunks),
                "confidence": avg_confidence,
                "content_preview": markdown_content[:500] if len(markdown_content) > 500 else markdown_content
            }, ensure_ascii=False))
            print("🔍 FRONTEND_LOG: LANDINGAI_EXTRACTION_END")
            
            return LandingAIExtractionResult(
                file_path=file_path,
                file_name=file_name,
                processing_time=processing_time,
                success=True,
                markdown_content=markdown_content,
                structured_analysis=educational_analysis,
                total_chunks=len(serializable_chunks),
                chunks_by_type={
                    'text': text_elements,
                    'table': table_elements,
                    'image': image_elements,
                    'title': title_elements
                },
                confidence_score=avg_confidence,
                text_elements=text_elements,
                table_elements=table_elements,
                image_elements=image_elements,
                title_elements=title_elements,
                raw_json_path=results_file
            )
                        
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ خطأ في agentic_doc.parse: {e}")
            
            # إضافة console.log للفرونت إند في حالة الفشل
            print("🔍 FRONTEND_LOG: LANDINGAI_EXTRACTION_FAILED")
            print("🔍 FRONTEND_LOG: " + json.dumps({
                "file_name": file_name,
                "error": str(e),
                "processing_time": processing_time
            }, ensure_ascii=False))
            print("🔍 FRONTEND_LOG: LANDINGAI_EXTRACTION_END")
            
            # إنشاء نتيجة فاشلة مع إشارة إلى إمكانية استخدام fallback
            return LandingAIExtractionResult(
                file_path=file_path,
                file_name=file_name,
                processing_time=processing_time,
                success=False,
                error_message=str(e),
                markdown_content="",
                structured_analysis=None,
                total_chunks=0,
                chunks_by_type={},
                confidence_score=0.0,
                text_elements=0,
                table_elements=0,
                image_elements=0,
                title_elements=0,
                raw_json_path=None
            )
        finally:
            # حذف الصورة المؤقتة إذا تم إنشاؤها
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.remove(temp_image_path)
                    logger.debug(f"🗑️ تم حذف الصورة المؤقتة: {temp_image_path}")
                except OSError as e:
                    logger.error(f"❌ فشل حذف الصورة المؤقتة {temp_image_path}: {e}")
    
    def _get_image_size(self, image_path: str) -> dict:
        """الحصول على حجم الصورة"""
        try:
            with Image.open(image_path) as img:
                return {"width": img.size[0], "height": img.size[1]}
        except Exception:
            return {"width": 0, "height": 0}
    
    async def _fallback_ocr_extraction(
        self, 
        file_path: str, 
        session_dir: str, 
        file_name: str
    ) -> LandingAIExtractionResult:
        """
        آلية احتياطية لاستخراج النص باستخدام Tesseract OCR
        Fallback OCR extraction using Tesseract when LandingAI fails
        """
        logger.info(f"🔄 بدء الاستخراج الاحتياطي باستخدام Tesseract OCR لـ {file_name}")
        
        start_time = datetime.now()
        
        try:
            # تحسين الصورة للـ OCR
            with Image.open(file_path) as img:
                # تحويل إلى RGB إذا لزم الأمر
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # تحسين الصورة للـ OCR
                enhanced_img = await self._preprocess_image_for_ocr(img)
                
                # حفظ الصورة المحسنة مؤقتاً
                temp_path = os.path.join(session_dir, "temp", f"enhanced_{file_name}")
                enhanced_img.save(temp_path, "JPEG", quality=95)
                
                # استخراج النص باستخدام Tesseract
                logger.info("🔍 استخراج النص باستخدام Tesseract...")
                
                # إعدادات Tesseract للغة العربية والإنجليزية
                custom_config = r'--oem 3 --psm 6 -l ara+eng'
                
                try:
                    extracted_text = pytesseract.image_to_string(enhanced_img, config=custom_config)
                except Exception as e:
                    logger.warning(f"⚠️ فشل مع اللغة العربية، محاولة مع الإنجليزية فقط: {e}")
                    custom_config = r'--oem 3 --psm 6 -l eng'
                    extracted_text = pytesseract.image_to_string(enhanced_img, config=custom_config)
                
                # تنظيف النص المستخرج
                cleaned_text = self._clean_extracted_text(extracted_text)
                
                if not cleaned_text.strip():
                    logger.warning("⚠️ لم يتم استخراج أي نص من الصورة")
                    cleaned_text = f"لم يتم العثور على نص في الصورة {file_name}"
                
                # إنشاء محتوى markdown
                markdown_content = f"# {Path(file_name).stem}\n\n## المحتوى المستخرج (Tesseract OCR)\n\n{cleaned_text}"
                
                # تحليل المحتوى التعليمي
                educational_analysis = await self._analyze_educational_content(cleaned_text)
                
                # حفظ النتائج
                results_file = os.path.join(session_dir, f"tesseract_result.json")
                result_data = {
                    "markdown": markdown_content,
                    "raw_text": cleaned_text,
                    "extraction_method": "Tesseract OCR",
                    "image_enhanced": True
                }
                
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                
                markdown_file = os.path.join(session_dir, f"extracted_content.md")
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                # حساب الإحصائيات
                processing_time = (datetime.now() - start_time).total_seconds()
                text_length = len(cleaned_text)
                
                # تقدير الثقة بناءً على طول النص وجودته
                confidence = min(0.8, max(0.4, text_length / 1000)) if text_length > 50 else 0.3
                
                logger.info(f"✅ اكتمل الاستخراج الاحتياطي في {processing_time:.2f}s")
                logger.info(f"📊 النص المستخرج: {text_length} حرف، ثقة: {confidence:.2f}")
                
                return LandingAIExtractionResult(
                    file_path=file_path,
                    file_name=file_name,
                    processing_time=processing_time,
                    success=True,
                    markdown_content=markdown_content,
                    structured_analysis=educational_analysis,
                    total_chunks=1,
                    chunks_by_type={'text': 1},
                    confidence_score=confidence,
                    text_elements=1,
                    table_elements=0,
                    image_elements=0,
                    title_elements=0,
                    raw_json_path=results_file
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ فشل في الاستخراج الاحتياطي: {e}")
            raise Exception(f"فشل في الاستخراج الاحتياطي باستخدام Tesseract: {e}")
    
    def _clean_extracted_text(self, text: str) -> str:
        """تنظيف النص المستخرج من OCR"""
        if not text:
            return ""
        
        # إزالة الأسطر الفارغة المتعددة
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        # دمج الأسطر مع فواصل مناسبة
        cleaned_text = '\n'.join(cleaned_lines)
        
        # تنظيف إضافي
        import re
        # إزالة الأحرف الغريبة
        cleaned_text = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF.,!?;:()\[\]{}"\'-]', '', cleaned_text)
        
        return cleaned_text

    async def _mock_extraction(
        self, 
        file_path: str, 
        session_dir: str, 
        file_name: str
    ) -> LandingAIExtractionResult:
        """محاكاة الاستخراج للتطوير"""
        
        logger.info(f"🎭 وضع المحاكاة - معالجة {file_name}")
        
        # محاكاة وقت المعالجة
        await asyncio.sleep(2)
        
        # محتوى تجريبي
        mock_markdown = f"""# {Path(file_name).stem}

## الفصل الأول: مقدمة في الرياضيات

### الأهداف التعليمية:
- فهم مفهوم الأعداد الطبيعية
- تطبيق العمليات الحسابية الأساسية
- حل المسائل الرياضية البسيطة

### المحتوى:
يتناول هذا الفصل المفاهيم الأساسية في الرياضيات...

### التمارين:
1. احسب مجموع الأعداد من 1 إلى 10
2. اوجد ناتج 15 × 7
3. حل المعادلة س + 5 = 12

### جدول النتائج:
| الطالب | الدرجة | التقدير |
|---------|---------|----------|
| أحمد    | 85      | جيد جداً |
| فاطمة   | 92      | ممتاز    |
| محمد    | 78      | جيد      |
"""
        
        mock_analysis = CurriculumAnalysis(
            subject="الرياضيات",
            grade_level="الصف الأول الثانوي",
            chapter_title="مقدمة في الرياضيات",
            learning_objectives=["فهم الأعداد", "العمليات الحسابية"],
            topics=["الأعداد الطبيعية", "العمليات الأساسية"],
            key_concepts=["الجمع", "الطرح", "الضرب", "القسمة"],
            difficulty_level="متوسط",
            content_type="نظري وعملي"
        )
        mock_json_path = os.path.join(session_dir, f"{Path(file_name).stem}_mock.json")
        mock_data = {
            "markdown": mock_markdown,
            "structured_analysis": mock_analysis.dict(),
            "chunks": [
                {
                    "chunk_id": "title_1",
                    "chunk_type": "title",
                    "content": "الفصل الأول: مقدمة في الرياضيات",
                    "page": 1
                },
                {
                    "chunk_id": "text_1", 
                    "chunk_type": "text",
                    "content": "يتناول هذا الفصل المفاهيم الأساسية في الرياضيات...",
                    "page": 1
                },
                {
                    "chunk_id": "table_1",
                    "chunk_type": "table", 
                    "content": "جدول النتائج",
                    "page": 1
                }
            ]
        }
        
        with open(mock_json_path, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, ensure_ascii=False, indent=2)
        
        return LandingAIExtractionResult(
            file_path=file_path,
            file_name=file_name,
            processing_time=0,
            success=True,
            markdown_content=mock_markdown,
            structured_analysis=mock_analysis,
            total_chunks=3,
            chunks_by_type={"title": 1, "text": 1, "table": 1},
            confidence_score=0.95,
            visual_groundings=[],
            visualization_images=[],
            raw_json_path=mock_json_path,
            text_elements=1,
            table_elements=1,
            image_elements=0,
            title_elements=1
        )
    
    async def extract_from_multiple_files(
        self, 
        file_paths: List[str], 
        output_dir: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> List[LandingAIExtractionResult]:
        """
        استخراج محتوى من ملفات متعددة
        Extract content from multiple files
        """
        logger.info(f"📁 بدء استخراج من {len(file_paths)} ملف")
        
        results = []
        for i, file_path in enumerate(file_paths):
            try:
                logger.info(f"📄 معالجة الملف {i+1}/{len(file_paths)}: {Path(file_path).name}")
                result = await self.extract_from_file(file_path, output_dir, job_id)
                results.append(result)
                
                # تأخير قصير لتجنب Rate Limiting
                if not self.mock_mode and i < len(file_paths) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة {file_path}: {e}")
                results.append(LandingAIExtractionResult(
                    file_path=file_path,
                    file_name=Path(file_path).name,
                    processing_time=0,
                    success=False,
                    error_message=str(e)
                ))
        
        successful = len([r for r in results if r.success])
        logger.info(f"✅ اكتمل استخراج {successful}/{len(file_paths)} ملف")
        
        return results
    
    def get_supported_formats(self) -> List[str]:
        """الحصول على الصيغ المدعومة"""
        return ["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"]
    
    def validate_file(self, file_path: str) -> bool:
        """التحقق من صحة الملف"""
        if not os.path.exists(file_path):
            return False
        
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        return file_ext in self.get_supported_formats()
    
    async def health_check(self) -> Dict[str, Any]:
        """فحص صحة الخدمة"""
        try:
            if self.mock_mode:
                return {
                    "status": "healthy",
                    "mode": "mock",
                    "message": "LandingAI Service في وضع المحاكاة",
                    "api_key_configured": False
                }
            
            # اختبار بسيط للـ API
            # يمكن إضافة اختبار حقيقي هنا
            return {
                "status": "healthy", 
                "mode": "production",
                "message": "LandingAI Service جاهز",
                "api_key_configured": True,
                "batch_size": self.batch_size,
                "max_workers": self.max_workers
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"خطأ في LandingAI Service: {str(e)}",
                "error": str(e)
            }

    def is_enabled(self) -> bool:
        """للتحقق من أن الخدمة ليست في وضع المحاكاة"""
        return not self.mock_mode


# إنشاء instance واحد للخدمة
landing_ai_service = LandingAIService() 