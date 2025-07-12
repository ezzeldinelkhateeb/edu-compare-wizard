"""
نظام تحسين النص الذكي
Smart Text Optimization System

الهدف: تقليل استهلاك التوكنز 70%+ مع الحفاظ على الجودة
"""

import re
from typing import List, Dict, Any, Tuple
from loguru import logger


class TextOptimizer:
    """محسن النص الذكي لتوفير التوكنز"""
    
    def __init__(self):
        # الكلمات المهمة في المناهج التعليمية
        self.educational_keywords = {
            'scientific_terms': [
                'قاعدة', 'مبدأ', 'قانون', 'نظرية', 'تعريف', 'معادلة',
                'باسكال', 'نيوتن', 'أرخميدس', 'أينشتاين',
                'هيدروليكي', 'كهربائي', 'مغناطيسي', 'حراري',
                'ضغط', 'قوة', 'طاقة', 'سرعة', 'تسارع', 'كتلة'
            ],
            'educational_elements': [
                'سؤال', 'مثال', 'تمرين', 'نشاط', 'تطبيق', 'ملاحظة',
                'تعريف', 'شرح', 'توضيح', 'خلاصة', 'ملخص'
            ],
            'mathematical_terms': [
                'معادلة', 'حساب', 'رقم', 'نسبة', 'نتيجة', 'حل',
                'متغير', 'ثابت', 'دالة', 'رسم', 'جدول', 'إحصائية'
            ]
        }
        
        # العبارات التي يجب حذفها (وصف LandingAI المفصل)
        self.noise_patterns = [
            r'Scene Overview.*?(?=\n\n|\n[A-Z]|\n•)',
            r'Technical Details.*?(?=\n\n|\n[A-Z]|\n•)',
            r'Spatial Relationships.*?(?=\n\n|\n[A-Z]|\n•)',
            r'Analysis.*?(?=\n\n|\n[A-Z]|\n•)',
            r'photo:.*?(?=\n\n|\n[A-Z])',
            r'illustration:.*?(?=\n\n|\n[A-Z])',
            r'figure:.*?(?=\n\n|\n[A-Z])',
            r'Summary.*?(?=\n\n|\n[A-Z])',
            r'from page \d+.*?\)',
            r'with ID [a-f0-9-]+',
            r'No visible scale.*?\.',
            r'Arabic text.*?translation:.*?\)',
            r'The image.*?educational.*?\.',
            r'Circular.*?number.*?\.',
            r'Main subject.*?background\.',
        ]
        
        logger.info("✅ تم تكوين محسن النص الذكي")
    
    def optimize_for_ai_analysis(self, text: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """تحسين النص للتحليل بالذكاء الاصطناعي"""
        
        if not text or not text.strip():
            return {
                "optimized_text": "",
                "original_length": 0,
                "optimized_length": 0,
                "reduction_percentage": 0,
                "extracted_elements": {}
            }
        
        original_length = len(text)
        logger.info(f"🔧 بدء تحسين النص: {original_length} حرف")
        
        # الخطوة 1: تنظيف أولي
        cleaned_text = self._remove_noise(text)
        
        # الخطوة 2: استخراج العناصر المهمة
        extracted_elements = self._extract_educational_elements(cleaned_text)
        
        # الخطوة 3: بناء النص المحسن
        optimized_text = self._build_optimized_text(extracted_elements, max_tokens)
        
        if optimized_text is None:
            optimized_text = ""
        
        optimized_length = len(optimized_text)
        reduction_percentage = ((original_length - optimized_length) / original_length * 100) if original_length > 0 else 0
        
        logger.info(f"✅ تم التحسين: {original_length} -> {optimized_length} حرف ({reduction_percentage:.1f}% تقليل)")
        
        return {
            "optimized_text": optimized_text,
            "original_length": original_length,
            "optimized_length": optimized_length,
            "reduction_percentage": round(reduction_percentage, 1),
            "extracted_elements": extracted_elements
        }
    
    def _remove_noise(self, text: str) -> str:
        """إزالة النصوص غير المفيدة"""
        
        cleaned = text
        
        # إزالة الأنماط المحددة مسبقاً
        for pattern in self.noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # إزالة الأسطر الفارغة المتعددة
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        
        # إزالة المسافات الزائدة
        cleaned = re.sub(r' +', ' ', cleaned)
        
        return cleaned.strip()
    
    def _extract_educational_elements(self, text: str) -> Dict[str, List[str]]:
        """استخراج العناصر التعليمية المهمة"""
        
        elements = {
            "definitions": [],
            "laws_and_principles": [],
            "examples": [],
            "questions": [],
            "explanations": [],
            "applications": [],
            "notes": [],
            "other_important": []
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # تصنيف السطر حسب المحتوى
            line_type = self._classify_line(line)
            
            if line_type in elements:
                elements[line_type].append(line)
            elif self._is_important_content(line):
                elements["other_important"].append(line)
        
        return elements
    
    def _classify_line(self, line: str) -> str:
        """تصنيف السطر حسب نوع المحتوى"""
        
        line_lower = line.lower()
        
        # تعريفات وقوانين
        if any(keyword in line_lower for keyword in ['قاعدة', 'مبدأ', 'قانون', 'نظرية']):
            return "laws_and_principles"
        
        if any(keyword in line_lower for keyword in ['تعريف', 'هو', 'هي', 'يُعرف']):
            return "definitions"
        
        # أسئلة
        if line.endswith('؟') or any(keyword in line_lower for keyword in ['سؤال', 'اسأل', 'ما هو', 'كيف', 'لماذا']):
            return "questions"
        
        # أمثلة وتطبيقات
        if any(keyword in line_lower for keyword in ['مثال', 'تطبيق', 'استخدام', 'يُستخدم']):
            return "examples"
        
        if any(keyword in line_lower for keyword in ['تطبيقات', 'استخدامات']):
            return "applications"
        
        # ملاحظات
        if any(keyword in line_lower for keyword in ['ملاحظة', 'انتبه', 'مهم', 'تذكر']):
            return "notes"
        
        # شرح وتوضيح
        if any(keyword in line_lower for keyword in ['شرح', 'توضيح', 'عندما', 'إذا', 'لأن']):
            return "explanations"
        
        return "other_important"
    
    def _is_important_content(self, line: str) -> bool:
        """تحديد ما إذا كان السطر مهم"""
        
        # سطر قصير جداً -> غير مهم
        if len(line) < 10:
            return False
        
        # يحتوي على كلمات مهمة
        for category in self.educational_keywords.values():
            if any(keyword in line for keyword in category):
                return True
        
        # يحتوي على أرقام أو معادلات
        if re.search(r'\d+|=|%|\+|\-|\*|/', line):
            return True
        
        # سطر طويل نسبياً مع محتوى عربي
        if len(line) > 20 and re.search(r'[\u0600-\u06FF]', line):
            return True
        
        return False
    
    def _build_optimized_text(self, elements: Dict[str, List[str]], max_tokens: int) -> str:
        """بناء النص المحسن بترتيب الأولوية"""
        
        # ترتيب الأولوية
        priority_order = [
            "laws_and_principles",
            "definitions", 
            "explanations",
            "examples",
            "applications",
            "questions",
            "notes",
            "other_important"
        ]
        
        optimized_parts = []
        current_length = 0
        max_chars = max_tokens * 4  # تقدير تقريبي: 1 توكن = 4 أحرف عربية
        
        for category in priority_order:
            if category not in elements:
                continue
            
            category_items = elements[category]
            if not category_items:
                continue
            
            # إضافة عنوان القسم إذا لزم الأمر
            section_header = self._get_section_header(category)
            if section_header is None:
                section_header = ""
            
            for item in category_items:
                if item is None or not item:
                    continue
                estimated_addition = len(item) + len(section_header) + 10  # هامش أمان
                
                if current_length + estimated_addition > max_chars:
                    break
                
                if section_header and section_header not in optimized_parts:
                    optimized_parts.append(section_header)
                    current_length += len(section_header)
                    section_header = None  # لا نكررها
                
                optimized_parts.append(item)
                current_length += len(item)
            
            if current_length >= max_chars:
                break
        
        result = '\n'.join(optimized_parts)
        return result if result else "لا توجد محتويات مهمة"
    
    def _get_section_header(self, category: str) -> str:
        """الحصول على عنوان القسم"""
        
        headers = {
            "laws_and_principles": "## القوانين والمبادئ:",
            "definitions": "## التعريفات:",
            "explanations": "## الشرح:",
            "examples": "## الأمثلة:",
            "applications": "## التطبيقات:",
            "questions": "## الأسئلة:",
            "notes": "## ملاحظات مهمة:",
            "other_important": "## محتوى إضافي:"
        }
        
        return headers.get(category, "")
    
    def compare_optimized_texts(self, text1: str, text2: str) -> Dict[str, Any]:
        """مقارنة نصين محسنين"""
        
        # تحسين النصين
        opt1 = self.optimize_for_ai_analysis(text1)
        opt2 = self.optimize_for_ai_analysis(text2)
        
        # مقارنة العناصر المستخرجة
        elements_comparison = self._compare_elements(
            opt1["extracted_elements"], 
            opt2["extracted_elements"]
        )
        
        return {
            "text1_optimization": opt1,
            "text2_optimization": opt2,
            "elements_comparison": elements_comparison,
            "total_reduction": (opt1["reduction_percentage"] + opt2["reduction_percentage"]) / 2,
            "tokens_saved_estimate": (opt1["original_length"] + opt2["original_length"] - 
                                    opt1["optimized_length"] - opt2["optimized_length"]) // 4
        }
    
    def _compare_elements(self, elements1: Dict, elements2: Dict) -> Dict[str, Any]:
        """مقارنة العناصر المستخرجة"""
        
        comparison = {}
        
        all_categories = set(elements1.keys()) | set(elements2.keys())
        
        for category in all_categories:
            items1 = set(elements1.get(category, []))
            items2 = set(elements2.get(category, []))
            
            common = items1 & items2
            only_in_1 = items1 - items2
            only_in_2 = items2 - items1
            
            comparison[category] = {
                "common_count": len(common),
                "unique_to_text1": len(only_in_1),
                "unique_to_text2": len(only_in_2),
                "similarity_percentage": len(common) / max(len(items1 | items2), 1) * 100
            }
        
        return comparison


# إنشاء instance واحد للخدمة
text_optimizer = TextOptimizer() 