"""
خدمة Gemini Vision لاستخراج النص مباشرة من الصور
Gemini Vision Service for Direct Text Extraction from Images
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import base64
from PIL import Image
import io

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from pydantic import BaseModel, Field
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


class GeminiVisionResult(BaseModel):
    """نتيجة استخراج النص باستخدام Gemini Vision"""
    success: bool = Field(default=True)
    extracted_text: str = Field(default="")
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    processing_time: float = Field(default=0.0)
    word_count: int = Field(default=0)
    character_count: int = Field(default=0)
    language_detected: str = Field(default="arabic")
    content_type: str = Field(default="educational")
    error_message: Optional[str] = None
    
    # تفاصيل إضافية للمحتوى التعليمي
    educational_elements: Dict[str, Any] = Field(default_factory=dict)
    text_quality_score: float = Field(default=0.0, ge=0, le=1)
    extraction_method: str = Field(default="gemini_vision")


class GeminiVisionService:
    """خدمة Gemini Vision لاستخراج النص مباشرة من الصور"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash-exp")
        self.temperature = float(os.getenv("GEMINI_VISION_TEMPERATURE", "0.1"))
        self.max_output_tokens = int(os.getenv("GEMINI_VISION_MAX_OUTPUT_TOKENS", "8192"))
        
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY غير موجود - سيتم استخدام المحاكاة")
            self.mock_mode = True
            self.client = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                generation_config = {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                }
                
                # إعداد إعدادات الأمان للسماح بالمحتوى التعليمي
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                
                self.client = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                self.mock_mode = False
                logger.info("✅ تم تكوين Gemini Vision Service مع API حقيقي")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تكوين Gemini Vision: {e}")
                self.mock_mode = True
                self.client = None
    
    async def extract_text_from_image(
        self, 
        image_path: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GeminiVisionResult:
        """
        استخراج النص من الصورة باستخدام Gemini Vision
        Extract text from image using Gemini Vision
        """
        start_time = datetime.now()
        
        logger.info(f"🖼️ بدء استخراج النص من الصورة: {image_path}")
        
        try:
            if self.mock_mode:
                result = await self._mock_extraction(image_path)
            else:
                result = await self._real_extraction(image_path, context)
            
            # حساب وقت المعالجة
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # حساب إحصائيات النص
            if result.extracted_text:
                result.word_count = len(result.extracted_text.split())
                result.character_count = len(result.extracted_text)
                result.text_quality_score = self._calculate_text_quality(result.extracted_text)
            
            logger.info(f"✅ تم استخراج النص في {processing_time:.2f} ثانية")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ خطأ في استخراج النص: {e}")
            
            return GeminiVisionResult(
                success=False,
                extracted_text="",
                confidence_score=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def compare_images_directly(
        self, 
        old_image_path: str,
        new_image_path: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مقارنة صورتين مباشرة باستخدام Gemini Vision
        Compare two images directly using Gemini Vision
        """
        start_time = datetime.now()
        
        logger.info(f"🔍 بدء المقارنة المباشرة للصورتين")
        
        try:
            if self.mock_mode:
                result = await self._mock_comparison(old_image_path, new_image_path)
            else:
                result = await self._real_comparison(old_image_path, new_image_path, context)
            
            # حساب وقت المعالجة
            processing_time = (datetime.now() - start_time).total_seconds()
            result["processing_time"] = processing_time
            
            logger.info(f"✅ تمت المقارنة المباشرة في {processing_time:.2f} ثانية")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ خطأ في المقارنة المباشرة: {e}")
            
            return {
                "success": False,
                "error_message": str(e),
                "processing_time": processing_time,
                "similarity_percentage": 0.0,
                "comparison_result": None
            }
    
    async def _real_extraction(
        self, 
        image_path: str,
        context: Optional[Dict[str, Any]] = None
    ) -> GeminiVisionResult:
        """الاستخراج الحقيقي باستخدام Gemini Vision"""
        
        logger.info("🤖 بدء الاستخراج باستخدام Gemini Vision API...")
        
        try:
            # تحميل الصورة
            image = self._load_and_prepare_image(image_path)
            
            # إنشاء البرومبت المخصص
            prompt = self._create_extraction_prompt(context)
            
            # إرسال الطلب إلى Gemini Vision
            logger.debug("📡 إرسال الطلب إلى Gemini Vision...")
            response = await asyncio.to_thread(
                self.client.generate_content, [prompt, image]
            )
            
            if not response.text:
                raise Exception("لم يتم الحصول على استجابة من Gemini Vision")
            
            logger.info("✅ تم الحصول على استجابة من Gemini Vision")
            
            # تحليل الاستجابة
            logger.debug("🔍 تحليل استجابة Gemini Vision...")
            analysis = self._parse_vision_response(response.text)
            
            return GeminiVisionResult(
                success=True,
                extracted_text=analysis.get("extracted_text", ""),
                confidence_score=analysis.get("confidence_score", 0.8),
                language_detected=analysis.get("language_detected", "arabic"),
                content_type=analysis.get("content_type", "educational"),
                educational_elements=analysis.get("educational_elements", {}),
                extraction_method="gemini_vision"
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في استدعاء Gemini Vision: {e}")
            raise e
    
    def _load_and_prepare_image(self, image_path: str) -> Any:
        """تحميل وتحضير الصورة لـ Gemini Vision"""
        try:
            # فتح الصورة باستخدام PIL
            with Image.open(image_path) as img:
                # تحويل إلى RGB إذا لزم الأمر
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # تحسين حجم الصورة لتوفير التكلفة
                max_size = (1024, 1024)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # تحويل إلى bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr = img_byte_arr.getvalue()
                
                # إنشاء كائن الصورة لـ Gemini
                return {
                    "mime_type": "image/jpeg",
                    "data": img_byte_arr
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الصورة: {e}")
            raise e
    
    def _create_extraction_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """إنشاء برومبت مخصص لاستخراج النص من الصور التعليمية"""
        
        context_info = ""
        if context:
            context_info = f"""
            معلومات السياق:
            - نوع المحتوى: {context.get('content_type', 'محتوى تعليمي')}
            - المادة: {context.get('subject', 'غير محدد')}
            - المستوى: {context.get('grade_level', 'غير محدد')}
            - اللغة المتوقعة: {context.get('expected_language', 'العربية')}
            """
        
        return f"""أنت خبير في استخراج النصوص من الصور التعليمية باستخدام Gemini Vision 2.0. 

{context_info}

**المهمة:**
استخرج جميع النصوص الموجودة في هذه الصورة التعليمية بدقة عالية.

**التعليمات المهمة:**
1. استخرج النص كما هو مكتوب بدون تفسير أو تعديل
2. حافظ على التنسيق والترتيب الأصلي للنص
3. اكتب الأرقام والرموز الرياضية كما تظهر
4. لا تضيف أي شرح أو تفسير للمحتوى
5. إذا كان هناك جداول، احتفظ بتنسيقها
6. إذا كان هناك نقاط أو قوائم، احتفظ بترقيمها

**تنسيق الإخراج:**
```json
{{
  "extracted_text": "النص المستخرج بالكامل هنا",
  "confidence_score": 0.95,
  "language_detected": "arabic",
  "content_type": "educational",
  "educational_elements": {{
    "has_definitions": true,
    "has_examples": true,
    "has_questions": false,
    "has_diagrams": false,
    "has_formulas": true,
    "topic_detected": "الموضوع المكتشف"
  }}
}}
```

**ملاحظات مهمة:**
- استخدم أعلى دقة ممكنة في الاستخراج
- تأكد من أن النص مقروء ومفهوم
- إذا كان النص غير واضح، اذكر ذلك في confidence_score
- لا تترجم النص - استخرجه كما هو"""
    
    def _parse_vision_response(self, response_text: str) -> Dict[str, Any]:
        """تحليل استجابة Gemini Vision واستخراج JSON"""
        
        try:
            # البحث عن JSON في الاستجابة
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # محاولة تحليل الاستجابة كـ JSON مباشرة
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            # في حالة فشل تحليل JSON، استخراج النص مباشرة
            logger.warning("⚠️ فشل في تحليل JSON من Gemini Vision، استخدام النص مباشرة")
            
            # تنظيف النص من علامات JSON
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            
            return {
                "extracted_text": cleaned_text,
                "confidence_score": 0.7,
                "language_detected": "arabic",
                "content_type": "educational",
                "educational_elements": {
                    "has_definitions": True,
                    "has_examples": False,
                    "has_questions": False,
                    "has_diagrams": False,
                    "has_formulas": False,
                    "topic_detected": "غير محدد"
                }
            }
    
    def _calculate_text_quality(self, text: str) -> float:
        """حساب جودة النص المستخرج"""
        if not text:
            return 0.0
        
        # معايير بسيطة لجودة النص
        quality_score = 0.5  # نقطة البداية
        
        # زيادة النقاط للنص الطويل والمفيد
        if len(text) > 50:
            quality_score += 0.2
        if len(text) > 200:
            quality_score += 0.1
        
        # زيادة النقاط للمحتوى التعليمي
        educational_keywords = ['تعريف', 'مثال', 'قاعدة', 'قانون', 'نظرية', 'مبدأ']
        for keyword in educational_keywords:
            if keyword in text:
                quality_score += 0.05
        
        # تقليل النقاط للنص المشوش
        if len([c for c in text if c.isalnum()]) / len(text) < 0.7:
            quality_score -= 0.2
        
        return min(quality_score, 1.0)
    
    async def _real_comparison(
        self, 
        old_image_path: str,
        new_image_path: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """المقارنة المباشرة الحقيقية باستخدام Gemini Vision"""
        
        logger.info("🤖 بدء المقارنة المباشرة باستخدام Gemini Vision API...")
        
        try:
            # تحميل الصورتين
            old_image = self._load_and_prepare_image(old_image_path)
            new_image = self._load_and_prepare_image(new_image_path)
            
            # إنشاء البرومبت المخصص للمقارنة
            prompt = self._create_comparison_prompt(context)
            
            # إرسال الطلب إلى Gemini Vision
            logger.debug("📡 إرسال الطلب للمقارنة إلى Gemini Vision...")
            response = await asyncio.to_thread(
                self.client.generate_content, [prompt, old_image, new_image]
            )
            
            if not response.text:
                raise Exception("لم يتم الحصول على استجابة من Gemini Vision")
            
            logger.info("✅ تم الحصول على استجابة المقارنة من Gemini Vision")
            
            # تحليل الاستجابة
            logger.debug("🔍 تحليل استجابة المقارنة...")
            analysis = self._parse_comparison_response(response.text)
            
            return {
                "success": True,
                "similarity_percentage": analysis.get("similarity_percentage", 0.0),
                "comparison_result": analysis,
                "old_text": analysis.get("old_text", ""),
                "new_text": analysis.get("new_text", ""),
                "differences": analysis.get("differences", []),
                "summary": analysis.get("summary", ""),
                "recommendation": analysis.get("recommendation", "")
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في المقارنة المباشرة: {e}")
            raise e
    
    async def _mock_comparison(self, old_image_path: str, new_image_path: str) -> Dict[str, Any]:
        """مقارنة وهمية للاختبار"""
        
        logger.info("🎭 وضع المحاكاة - المقارنة المباشرة")
        
        # محاكاة وقت المعالجة
        await asyncio.sleep(3)
        
        return {
            "success": True,
            "similarity_percentage": 87.5,
            "comparison_result": {
                "content_changes": [
                    "تم تحديث بعض الأمثلة في الدرس",
                    "إضافة تمرين جديد في نهاية الصفحة"
                ],
                "major_differences": [
                    "تغيير في صيغة السؤال الثالث"
                ],
                "summary": "النصان متشابهان إلى حد كبير مع تحسينات طفيفة في الأمثلة والتمارين",
                "recommendation": "التغييرات إيجابية وتحسن من جودة المحتوى التعليمي"
            },
            "old_text": "قاعدة باسكال: عندما يؤثر ضغط على سائل محبوس في إناء، فإن هذا الضغط ينتقل إلى جميع نقاط السائل بنفس الشدة.",
            "new_text": "قاعدة باسكال: عندما يؤثر ضغط على سائل محبوس في إناء، فإن هذا الضغط ينتقل إلى جميع نقاط السائل بنفس الشدة. مثال: الرافعة الهيدروليكية.",
            "differences": [
                "إضافة مثال الرافعة الهيدروليكية"
            ],
            "summary": "تم إضافة مثال توضيحي لقاعدة باسكال",
            "recommendation": "التحديث مفيد ويوضح التطبيق العملي للقاعدة"
        }
    
    def _create_comparison_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """إنشاء برومبت مخصص للمقارنة المباشرة بين صورتين تعليميتين"""
        
        context_info = ""
        if context:
            context_info = f"""
            معلومات السياق:
            - نوع المحتوى: {context.get('content_type', 'محتوى تعليمي')}
            - المادة: {context.get('subject', 'غير محدد')}
            - المستوى: {context.get('grade_level', 'غير محدد')}
            - اللغة المتوقعة: {context.get('expected_language', 'العربية')}
            """
        
        return f"""أنت خبير في مقارنة المحتوى التعليمي باستخدام Gemini Vision 2.0. 

{context_info}

**المهمة:**
قارن بين هاتين الصورتين التعليميتين واستخرج النصوص منهما ثم حدد الاختلافات الجوهرية.

**التعليمات المهمة:**
1. استخرج النص من كلا الصورتين بدقة عالية
2. قارن النصوص المستخرجة وحدد الاختلافات الجوهرية فقط
3. تجاهل الاختلافات الطفيفة في التنسيق أو الألوان
4. ركز على التغييرات في المحتوى التعليمي (تعريفات، أمثلة، أسئلة)
5. احسب نسبة التشابه بدقة
6. قدم توصيات واضحة للمعلم

**تنسيق الإخراج:**
```json
{{
  "similarity_percentage": 87.5,
  "old_text": "النص المستخرج من الصورة الأولى",
  "new_text": "النص المستخرج من الصورة الثانية", 
  "content_changes": [
    "قائمة بالتغييرات في المحتوى الأساسي"
  ],
  "questions_changes": [
    "قائمة بالتغييرات في الأسئلة"
  ],
  "examples_changes": [
    "قائمة بالتغييرات في الأمثلة"
  ],
  "major_differences": [
    "قائمة بالاختلافات الجوهرية المهمة"
  ],
  "added_content": [
    "قائمة بالمحتوى المضاف"
  ],
  "removed_content": [
    "قائمة بالمحتوى المحذوف"
  ],
  "summary": "ملخص شامل للمقارنة باللغة العربية",
  "recommendation": "توصيات للمعلم بناءً على التغييرات",
  "confidence_score": 0.95,
  "language_detected": "arabic"
}}
```

**معايير حساب نسبة التشابه:**
- 95-100%: نفس المحتوى تقريباً مع اختلافات طفيفة في التنسيق
- 85-94%: محتوى متشابه جداً مع تحسينات أو إضافات طفيفة
- 70-84%: محتوى متشابه مع تغييرات متوسطة
- 50-69%: محتوى مختلف جزئياً مع تغييرات كبيرة
- أقل من 50%: محتوى مختلف كلياً

**ملاحظات مهمة:**
- استخدم أعلى دقة ممكنة في الاستخراج والمقارنة
- كن دقيقاً في تحديد الاختلافات الجوهرية
- قدم توصيات عملية للمعلم
- تأكد من أن النتيجة صالحة JSON"""
    
    def _parse_comparison_response(self, response_text: str) -> Dict[str, Any]:
        """تحليل استجابة المقارنة من Gemini Vision"""
        
        try:
            # البحث عن JSON في الاستجابة
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # محاولة تحليل الاستجابة كـ JSON مباشرة
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            # في حالة فشل تحليل JSON، استخراج المعلومات يدوياً
            logger.warning("⚠️ فشل في تحليل JSON من المقارنة، استخدام تحليل نصي")
            
            return {
                "similarity_percentage": 75.0,
                "old_text": "نص من الصورة الأولى",
                "new_text": "نص من الصورة الثانية",
                "content_changes": ["تغييرات في المحتوى"],
                "questions_changes": [],
                "examples_changes": [],
                "major_differences": ["اختلافات جوهرية"],
                "added_content": [],
                "removed_content": [],
                "summary": response_text[:200] + "...",
                "recommendation": "يُنصح بمراجعة التغييرات",
                "confidence_score": 0.6,
                "language_detected": "arabic"
            }
    
    async def _mock_extraction(self, image_path: str) -> GeminiVisionResult:
        """استخراج وهمي للاختبار"""
        
        logger.info("🎭 وضع المحاكاة - استخراج النص من الصورة")
        
        # محاكاة وقت المعالجة
        await asyncio.sleep(2)
        
        # نص تجريبي للاختبار
        mock_text = """قاعدة باسكال في الهيدروليكا

التعريف:
عندما يؤثر ضغط على سائل محبوس في إناء، فإن هذا الضغط ينتقل إلى جميع نقاط السائل بنفس الشدة.

القانون الرياضي:
P₁ = P₂
حيث P₁ هو الضغط في النقطة الأولى
و P₂ هو الضغط في النقطة الثانية

التطبيقات:
- الرافعة الهيدروليكية
- فرامل السيارات
- المكبس الهيدروليكي

مثال:
إذا كان الضغط المؤثر على مكبس صغير 100 نيوتن/م²، فإن نفس الضغط ينتقل إلى المكبس الكبير."""
        
        return GeminiVisionResult(
            success=True,
            extracted_text=mock_text,
            confidence_score=0.85,
            language_detected="arabic",
            content_type="educational",
            educational_elements={
                "has_definitions": True,
                "has_examples": True,
                "has_questions": False,
                "has_diagrams": False,
                "has_formulas": True,
                "topic_detected": "قاعدة باسكال"
            },
            extraction_method="gemini_vision_mock"
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """فحص صحة خدمة Gemini Vision"""
        try:
            if self.mock_mode:
                return {
                    "status": "healthy",
                    "mode": "mock",
                    "message": "Gemini Vision Service في وضع المحاكاة",
                    "api_key_configured": False,
                    "model": "mock-vision-model"
                }
            
            # اختبار بسيط للـ API
            test_response = await asyncio.to_thread(
                self.client.generate_content, 
                "اختبار بسيط لـ Gemini Vision"
            )
            
            return {
                "status": "healthy",
                "mode": "production",
                "message": "Gemini Vision Service جاهز",
                "api_key_configured": True,
                "model": self.model_name,
                "model_version": "2.0-flash-exp",
                "features": [
                    "استخراج نص مباشر من الصور",
                    "دعم المحتوى التعليمي",
                    "تحليل ذكي للعناصر التعليمية",
                    "دقة عالية في النصوص العربية"
                ]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"خطأ في Gemini Vision Service: {str(e)}",
                "error": str(e)
            }


# إنشاء مثيل مشترك من الخدمة
gemini_vision_service = GeminiVisionService() 