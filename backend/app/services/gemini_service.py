"""
خدمة Google Gemini للمقارنة النصية الذكية
Google Gemini Service for Intelligent Text Comparison
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import difflib
import re

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from pydantic import BaseModel, Field
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


class TextComparisonResult(BaseModel):
    """نتيجة مقارنة النصوص"""
    similarity_percentage: float = Field(..., ge=0, le=100)
    content_changes: List[str] = Field(default_factory=list)
    questions_changes: List[str] = Field(default_factory=list)
    examples_changes: List[str] = Field(default_factory=list)
    major_differences: List[str] = Field(default_factory=list)
    added_content: List[str] = Field(default_factory=list)
    removed_content: List[str] = Field(default_factory=list)
    modified_content: List[str] = Field(default_factory=list)
    
    summary: str
    recommendation: str
    detailed_analysis: str = ""
    
    processing_time: float
    service_used: str = "Gemini"
    confidence_score: float = Field(default=0.85, ge=0, le=1)
    
    # إحصائيات
    old_text_length: int = 0
    new_text_length: int = 0
    common_words_count: int = 0
    unique_old_words: int = 0
    unique_new_words: int = 0


class GeminiService:
    """خدمة Google Gemini للمقارنة النصية الذكية"""
    
    def __init__(self):
        # استخدام المفتاح المُقدم
        self.api_key = "AIzaSyCDO-0puQQN79BJ4u503O31g16ww8CAycg"
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
        self.max_output_tokens = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192"))
        self.top_p = float(os.getenv("GEMINI_TOP_P", "0.8"))
        self.top_k = int(os.getenv("GEMINI_TOP_K", "40"))
        
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY غير موجود - سيتم استخدام المحاكاة")
            self.mock_mode = True
            self.client = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                generation_config = {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "top_k": self.top_k,
                    "max_output_tokens": self.max_output_tokens,
                }
                
                self.client = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=generation_config
                )
                
                self.mock_mode = False
                logger.info("✅ تم تكوين Gemini AI Service مع API حقيقي")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تكوين Gemini: {e}")
                self.mock_mode = True
                self.client = None
    
    async def compare_texts(
        self, 
        old_text: str, 
        new_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TextComparisonResult:
        """
        مقارنة نصين باستخدام Gemini AI
        Compare two texts using Gemini AI
        """
        start_time = datetime.now()
        
        logger.info("📝 بدء مقارنة النصوص باستخدام Gemini")
        
        try:
            if self.mock_mode:
                result = await self._mock_comparison(old_text, new_text)
            else:
                result = await self._real_comparison(old_text, new_text, context)
            
            # حساب وقت المعالجة
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # إضافة إحصائيات النص
            result.old_text_length = len(old_text)
            result.new_text_length = len(new_text)
            
            # حساب الكلمات المشتركة
            old_words = set(old_text.split())
            new_words = set(new_text.split())
            common_words = old_words & new_words
            
            result.common_words_count = len(common_words)
            result.unique_old_words = len(old_words - new_words)
            result.unique_new_words = len(new_words - old_words)
            
            logger.info(f"✅ اكتملت مقارنة النصوص في {processing_time:.2f} ثانية")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ خطأ في مقارنة النصوص: {e}")
            
            # إرجاع نتيجة أساسية في حالة الخطأ
            return await self._fallback_comparison(old_text, new_text, processing_time, str(e))
    
    async def _real_comparison(
        self, 
        old_text: str, 
        new_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TextComparisonResult:
        """المقارنة الحقيقية باستخدام Gemini"""
        
        logger.info("🤖 بدء التحليل باستخدام Gemini AI...")
        
        # إعداد البرومبت المخصص للمناهج التعليمية
        prompt = self._create_comparison_prompt(old_text, new_text, context)
        
        try:
            # استدعاء Gemini
            logger.debug("📡 إرسال الطلب إلى Gemini...")
            response = await asyncio.to_thread(
                self.client.generate_content, prompt
            )
            
            if not response.text:
                raise Exception("لم يتم الحصول على استجابة من Gemini")
            
            logger.info("✅ تم الحصول على استجابة من Gemini")
            
            # تحليل الاستجابة
            logger.debug("🔍 تحليل استجابة Gemini...")
            analysis = self._parse_gemini_response(response.text)
            
            # حساب نسبة التشابه باستخدام difflib كمرجع
            logger.debug("📊 حساب نسبة التشابه...")
            similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio() * 100
            
            # إضافة معلومات إضافية للتحليل
            detailed_analysis = f"""
## تحليل مفصل بواسطة Gemini AI

### نسبة التشابه: {similarity:.1f}%

### التحليل الذكي:
{response.text}

### إحصائيات النص:
- النص القديم: {len(old_text)} حرف
- النص الجديد: {len(new_text)} حرف
- الفرق في الطول: {abs(len(new_text) - len(old_text))} حرف

### معلومات المعالجة:
- تم التحليل باستخدام: {self.model_name}
- درجة الحرارة: {self.temperature}
- الحد الأقصى للرموز: {self.max_output_tokens}
"""
            
            result = TextComparisonResult(
                similarity_percentage=round(similarity, 1),
                content_changes=analysis.get("content_changes", []),
                questions_changes=analysis.get("questions_changes", []),
                examples_changes=analysis.get("examples_changes", []),
                major_differences=analysis.get("major_differences", []),
                added_content=analysis.get("added_content", []),
                removed_content=analysis.get("removed_content", []),
                modified_content=analysis.get("modified_content", []),
                summary=analysis.get("summary", "تم تحليل النصين بنجاح"),
                recommendation=analysis.get("recommendation", "يُنصح بمراجعة التغييرات"),
                detailed_analysis=detailed_analysis,
                processing_time=0,  # سيتم تحديثه
                confidence_score=analysis.get("confidence_score", 0.9)
            )
            
            logger.info(f"🎯 تم التحليل: {similarity:.1f}% تشابه")
            return result
            
        except Exception as e:
            logger.error(f"❌ خطأ في استدعاء Gemini: {e}")
            raise
    
    def _create_comparison_prompt(
        self, 
        old_text: str, 
        new_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """إنشاء برومبت مخصص لمقارنة المناهج التعليمية"""
        
        context_info = ""
        if context:
            context_info = f"""
معلومات السياق:
- نوع المحتوى: {context.get('content_type', 'منهج تعليمي')}
- المادة: {context.get('subject', 'غير محدد')}
- المستوى: {context.get('grade_level', 'غير محدد')}
"""
        
        prompt = f"""
أنت خبير في تحليل المناهج التعليمية. مهمتك مقارنة نسختين من منهج تعليمي مع التركيز على الأسئلة الجديدة والشرح الجديد.

{context_info}

النص الأصلي (المنهج القديم):
```
{old_text[:3000]}...
```

النص الجديد (المنهج المحدث):
```
{new_text[:3000]}...
```

ركز تحليلك على:

1. **الأسئلة الجديدة** (أولوية عالية):
   - أسئلة مضافة جديدة كلياً
   - تعديلات على صيغة الأسئلة الموجودة
   - أسئلة تطبيقية جديدة
   - أسئلة تقييمية جديدة

2. **الشرح والمحتوى الجديد** (أولوية عالية):
   - شروحات مضافة للمفاهيم
   - أمثلة توضيحية جديدة
   - طرق حل جديدة
   - مفاهيم علمية مضافة

3. **التغييرات في التمارين والتطبيقات**:
   - تمارين جديدة
   - مسائل حسابية جديدة
   - تطبيقات عملية مضافة

4. **التحسينات على المحتوى الموجود**:
   - تبسيط الشرح
   - إضافة تفاصيل مهمة
   - تحسين التسلسل المنطقي

5. **التغييرات غير المهمة** (يمكن تجاهلها):
   - تغييرات في التنسيق فقط
   - أخطاء إملائية
   - تغييرات طفيفة في الكلمات

أعط أولوية خاصة للأسئلة الجديدة والشرح الجديد. أرجع النتيجة بصيغة JSON:

```json
{{
  "new_questions": ["قائمة مفصلة بالأسئلة الجديدة"],
  "new_explanations": ["قائمة بالشروحات الجديدة"],
  "modified_questions": ["الأسئلة المعدلة"],
  "new_examples": ["الأمثلة الجديدة"],
  "content_changes": ["التغييرات في المحتوى"],
  "questions_changes": ["جميع التغييرات في الأسئلة"],
  "major_differences": ["الاختلافات الجوهرية فقط"],
  "added_content": ["المحتوى المضاف الجديد"],
  "summary": "ملخص يركز على الأسئلة والشروحات الجديدة",
  "recommendation": "توصيات للمعلمين حول الأسئلة والمحتوى الجديد",
  "has_significant_changes": true/false,
  "confidence_score": 0.95
}}
```

إذا كانت التغييرات طفيفة أو غير مهمة، اذكر ذلك بوضوح.
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """تحليل استجابة Gemini واستخراج JSON"""
        
        try:
            # البحث عن JSON في الاستجابة
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # محاولة تحليل الاستجابة كـ JSON مباشرة
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            # في حالة فشل تحليل JSON، استخراج المعلومات يدوياً
            logger.warning("⚠️ فشل في تحليل JSON من Gemini، استخدام تحليل نصي")
            
            return {
                "content_changes": self._extract_list_from_text(response_text, "التغييرات في المحتوى"),
                "questions_changes": self._extract_list_from_text(response_text, "التغييرات في الأسئلة"),
                "examples_changes": self._extract_list_from_text(response_text, "التغييرات في الأمثلة"),
                "major_differences": self._extract_list_from_text(response_text, "الاختلافات الجوهرية"),
                "added_content": [],
                "removed_content": [],
                "modified_content": [],
                "summary": self._extract_summary_from_text(response_text),
                "recommendation": self._extract_recommendation_from_text(response_text),
                "detailed_analysis": response_text[:1000],
                "confidence_score": 0.8
            }
    
    def _extract_list_from_text(self, text: str, section: str) -> List[str]:
        """استخراج قائمة من النص"""
        # تطبيق بسيط لاستخراج النقاط
        lines = text.split('\n')
        items = []
        in_section = False
        
        for line in lines:
            if section in line:
                in_section = True
                continue
            if in_section and line.strip().startswith('-'):
                items.append(line.strip()[1:].strip())
            elif in_section and line.strip() == '':
                break
        
        return items[:5]  # حد أقصى 5 عناصر
    
    def _extract_summary_from_text(self, text: str) -> str:
        """استخراج الملخص من النص"""
        lines = text.split('\n')
        for line in lines:
            if 'ملخص' in line and len(line) > 20:
                return line.strip()
        return "تم تحليل النصين وتحديد الاختلافات الرئيسية"
    
    def _extract_recommendation_from_text(self, text: str) -> str:
        """استخراج التوصية من النص"""
        lines = text.split('\n')
        for line in lines:
            if 'توصية' in line or 'يُنصح' in line:
                return line.strip()
        return "يُنصح بمراجعة التغييرات وتحديث خطط التدريس وفقاً لذلك"
    
    async def _mock_comparison(
        self, 
        old_text: str, 
        new_text: str
    ) -> TextComparisonResult:
        """مقارنة محاكاة للتطوير"""
        
        logger.info("🎭 وضع المحاكاة - مقارنة النصوص")
        
        # محاكاة وقت المعالجة
        await asyncio.sleep(2)
        
        # حساب تشابه أساسي
        similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio() * 100
        
        # تغييرات تجريبية
        mock_changes = [
            "تم إضافة فقرة جديدة عن التطبيقات العملية",
            "تم تحديث الأمثلة لتكون أكثر وضوحاً",
            "تم إعادة ترتيب بعض المفاهيم لتحسين التسلسل",
            "تم إضافة تمارين إضافية للتعزيز"
        ]
        
        return TextComparisonResult(
            similarity_percentage=round(similarity, 1),
            content_changes=mock_changes[:2],
            questions_changes=["تم إضافة 3 أسئلة جديدة", "تم تعديل صياغة سؤالين"],
            examples_changes=["تم استبدال مثال قديم بمثال أكثر حداثة"],
            major_differences=mock_changes[2:] if similarity < 80 else [],
            added_content=["محتوى جديد حول التطبيقات"],
            removed_content=["محتوى قديم غير ذي صلة"],
            modified_content=["تحسين في الشرح"],
            summary=f"تم تحليل النصين وتحديد مستوى التطابق {similarity:.1f}%. تم العثور على {len(mock_changes)} تغيير رئيسي.",
            recommendation="يُنصح بمراجعة التغييرات المحددة وتحديث خطة التدريس وفقاً لذلك" if similarity < 85 else "التغييرات طفيفة ولا تتطلب تحديثات كبيرة",
            detailed_analysis="تحليل تفصيلي: النصان متشابهان إلى حد كبير مع تحسينات طفيفة في المحتوى الجديد",
            processing_time=0,
            confidence_score=0.9
        )
    
    async def _fallback_comparison(
        self, 
        old_text: str, 
        new_text: str,
        processing_time: float,
        error_message: str
    ) -> TextComparisonResult:
        """مقارنة احتياطية في حالة الخطأ"""
        
        # حساب تشابه أساسي باستخدام difflib
        similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio() * 100
        
        return TextComparisonResult(
            similarity_percentage=round(similarity, 1),
            content_changes=[],
            questions_changes=[],
            examples_changes=[],
            major_differences=[],
            added_content=[],
            removed_content=[],
            modified_content=[],
            summary=f"تم حساب التشابه الأساسي: {similarity:.1f}%",
            recommendation="حدث خطأ في التحليل المتقدم، يُنصح بالمراجعة اليدوية",
            detailed_analysis=f"خطأ في المعالجة: {error_message}",
            processing_time=processing_time,
            confidence_score=0.5
        )
    
    async def analyze_text(self, text: str, prompt: Optional[str] = None) -> str:
        """
        تحليل نص واحد باستخدام Gemini
        Analyze single text using Gemini
        """
        logger.info("🔍 بدء تحليل النص باستخدام Gemini")
        
        try:
            if self.mock_mode:
                return await self._mock_text_analysis(text)
            
            # إعداد البرومبت
            analysis_prompt = prompt or f"""
            يرجى تحليل النص التالي وتقديم:
            1. ملخص للمحتوى
            2. الموضوع الرئيسي
            3. النقاط المهمة
            4. تقييم جودة النص
            5. أي ملاحظات أخرى
            
            النص:
            {text}
            
            يرجى الإجابة باللغة العربية بشكل مفصل ومفيد.
            """
            
            # استدعاء Gemini
            response = await asyncio.to_thread(
                self.client.generate_content, analysis_prompt
            )
            
            if not response.text:
                raise Exception("لم يتم الحصول على استجابة من Gemini")
            
            logger.info("✅ تم تحليل النص بنجاح")
            return response.text
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحليل النص: {e}")
            return await self._mock_text_analysis(text)
    
    async def _mock_text_analysis(self, text: str) -> str:
        """تحليل وهمي للنص للاختبار"""
        await asyncio.sleep(1)  # محاكاة وقت المعالجة
        
        word_count = len(text.split())
        char_count = len(text)
        
        return f"""# تحليل النص - وضع المحاكاة

## ملخص المحتوى
تم تحليل نص يحتوي على {word_count} كلمة و {char_count} حرف. النص يبدو أنه يحتوي على محتوى تعليمي أو أكاديمي.

## الموضوع الرئيسي
بناءً على التحليل الأولي، يتعلق النص بموضوع تعليمي يتضمن معلومات ومفاهيم أساسية.

## النقاط المهمة
- النص منظم ومهيكل بشكل جيد
- يحتوي على معلومات قيمة للقارئ
- اللغة واضحة ومفهومة
- المحتوى مناسب للغرض التعليمي

## تقييم جودة النص
- **الوضوح**: جيد
- **التنظيم**: ممتاز
- **المحتوى**: مفيد ومناسب
- **اللغة**: سليمة ومفهومة

## ملاحظات إضافية
- تم استخراج النص بنجاح من المصدر الأصلي
- جودة الاستخراج جيدة مع حد أدنى من الأخطاء
- النص جاهز للمعالجة والمقارنة
- يُنصح بمراجعة النص للتأكد من دقة المعلومات

---
*تم إنشاء هذا التحليل في وضع المحاكاة لأغراض الاختبار*
"""

    async def health_check(self) -> Dict[str, Any]:
        """فحص صحة خدمة Gemini"""
        try:
            if self.mock_mode:
                return {
                    "status": "healthy",
                    "mode": "mock", 
                    "message": "Gemini Service في وضع المحاكاة",
                    "api_key_configured": False
                }
            
            # اختبار بسيط للـ API
            test_response = await asyncio.to_thread(
                self.client.generate_content, 
                "اختبار بسيط للاتصال"
            )
            
            return {
                "status": "healthy",
                "mode": "production",
                "message": "Gemini Service جاهز",
                "api_key_configured": True,
                "model": self.model_name,
                "test_response_length": len(test_response.text) if test_response.text else 0
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"خطأ في Gemini Service: {str(e)}",
                "error": str(e)
            }


# إنشاء instance واحد للخدمة
gemini_service = GeminiService() 