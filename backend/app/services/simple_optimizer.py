"""
محسن النص المبسط - نسخة تعمل بدون أخطاء
Simple Text Optimizer - Working Version
"""

import re
from typing import Dict, Any
from loguru import logger


class SimpleOptimizer:
    """محسن النص المبسط والفعال"""
    
    def __init__(self):
        logger.info("✅ تم تكوين محسن النص المبسط")
    
    def optimize_text(self, text: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """تحسين النص بطريقة مبسطة وفعالة"""
        
        if not text or not text.strip():
            return {
                "optimized_text": "",
                "original_length": 0,
                "optimized_length": 0,
                "reduction_percentage": 0
            }
        
        original_length = len(text)
        logger.info(f"🔧 بدء تحسين النص: {original_length} حرف")
        
        # الخطوة 1: إزالة النصوص غير المفيدة
        cleaned_text = self._remove_noise_simple(text)
        
        # الخطوة 2: استخراج الأجزاء المهمة
        important_parts = self._extract_important_parts(cleaned_text)
        
        # الخطوة 3: بناء النص المحسن
        max_chars = max_tokens * 4  # تقدير: 1 توكن = 4 أحرف عربية
        optimized_text = self._build_optimized_simple(important_parts, max_chars)
        
        optimized_length = len(optimized_text)
        reduction_percentage = ((original_length - optimized_length) / original_length * 100) if original_length > 0 else 0
        
        logger.info(f"✅ تم التحسين: {original_length} -> {optimized_length} حرف ({reduction_percentage:.1f}% تقليل)")
        
        return {
            "optimized_text": optimized_text,
            "original_length": original_length,
            "optimized_length": optimized_length,
            "reduction_percentage": round(reduction_percentage, 1)
        }
    
    def _remove_noise_simple(self, text: str) -> str:
        """إزالة النصوص غير المفيدة بطريقة مبسطة"""
        
        # النصوص التي يجب حذفها
        noise_patterns = [
            r'Scene Overview.*?(?=\n\n|\n[A-Z]|\n•|\n*)',
            r'Technical Details.*?(?=\n\n|\n[A-Z]|\n•|\n*)',
            r'Spatial Relationships.*?(?=\n\n|\n[A-Z]|\n•|\n*)',
            r'Analysis.*?(?=\n\n|\n[A-Z]|\n•|\n*)',
            r'Summary.*?(?=\n\n|\n[A-Z]|\n•|\n*)',
            r'•.*?(?=\n)',
            r'The image.*?\.(?=\n)',
            r'Arabic text.*?\.(?=\n)',
            r'No visible.*?\.(?=\n)'
        ]
        
        cleaned = text
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # تنظيف عام
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # إزالة الأسطر الفارغة المتعددة
        cleaned = re.sub(r' +', ' ', cleaned)        # إزالة المسافات المتعددة
        
        return cleaned.strip()
    
    def _extract_important_parts(self, text: str) -> list:
        """استخراج الأجزاء المهمة"""
        
        important_parts = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # تحديد الأهمية
            if self._is_important_line(line):
                important_parts.append(line)
        
        return important_parts
    
    def _is_important_line(self, line: str) -> bool:
        """تحديد ما إذا كان السطر مهم"""
        
        # سطر قصير جداً
        if len(line) < 5:
            return False
        
        # الكلمات المهمة
        important_keywords = [
            'قاعدة', 'مبدأ', 'قانون', 'نظرية', 'تعريف',
            'باسكال', 'هيدروليكي', 'ضغط', 'سائل',
            'تطبيقات', 'مثال', 'ملاحظة', 'مهم'
        ]
        
        line_lower = line.lower()
        
        # يحتوي على كلمات مهمة
        if any(keyword in line_lower for keyword in important_keywords):
            return True
        
        # يحتوي على نص عربي طويل
        if len(line) > 15 and re.search(r'[\u0600-\u06FF]', line):
            return True
        
        # يحتوي على رموز مثل الشرطة (قوائم)
        if line.startswith('-') or line.startswith('*'):
            return True
        
        return False
    
    def _build_optimized_simple(self, parts: list, max_chars: int) -> str:
        """بناء النص المحسن بطريقة مبسطة"""
        
        if not parts:
            return "لا توجد محتويات مهمة"
        
        optimized_parts = []
        current_length = 0
        
        # ترتيب الأولوية: الأهم أولاً
        sorted_parts = self._sort_by_importance(parts)
        
        for part in sorted_parts:
            if current_length + len(part) + 5 < max_chars:  # هامش أمان
                optimized_parts.append(part)
                current_length += len(part) + 1  # +1 للسطر الجديد
            else:
                break
        
        return '\n'.join(optimized_parts)
    
    def _sort_by_importance(self, parts: list) -> list:
        """ترتيب الأجزاء حسب الأهمية"""
        
        def importance_score(line):
            score = 0
            line_lower = line.lower()
            
            # قوانين ومبادئ (الأهم)
            if any(keyword in line_lower for keyword in ['قاعدة', 'مبدأ', 'قانون', 'نظرية']):
                score += 100
            
            # تعريفات
            if any(keyword in line_lower for keyword in ['تعريف', 'هو', 'هي']):
                score += 80
            
            # تطبيقات
            if any(keyword in line_lower for keyword in ['تطبيقات', 'استخدام']):
                score += 60
            
            # ملاحظات
            if any(keyword in line_lower for keyword in ['ملاحظة', 'مهم']):
                score += 40
            
            # طول الخط
            score += min(len(line) // 10, 20)
            
            return score
        
        return sorted(parts, key=importance_score, reverse=True)


# إنشاء instance واحد
simple_optimizer = SimpleOptimizer() 