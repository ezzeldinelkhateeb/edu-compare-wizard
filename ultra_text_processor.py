#!/usr/bin/env python3
"""
Ultra Text Processor - معالج النصوص الفائق
نظام متقدم لتنظيف وتحسين مخرجات Landing AI للمقارنة النصية

الميزات الجديدة:
- تحليل ذكي للمحتوى التعليمي
- تحسين خاص للمقارنات مع Gemini
- معالجة PDF مباشرة
- تحليل جودة النص
- تقارير مفصلة بالعربية
"""

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import difflib
import hashlib
import unicodedata

class ContentQuality(Enum):
    """تصنيف جودة المحتوى"""
    EXCELLENT = "ممتاز"
    GOOD = "جيد" 
    ACCEPTABLE = "مقبول"
    POOR = "ضعيف"
    VERY_POOR = "ضعيف جداً"

class TextType(Enum):
    """أنواع النصوص التعليمية"""
    THEORY = "نظرية"
    EXAMPLE = "مثال"
    EXERCISE = "تمرين"
    DEFINITION = "تعريف"
    FORMULA = "معادلة"
    DIAGRAM_DESC = "وصف رسم"
    MIXED = "مختلط"

@dataclass
class TextAnalysis:
    """تحليل شامل للنص"""
    original_length: int
    cleaned_length: int
    reduction_percentage: float
    quality_score: float
    content_type: TextType
    quality_rating: ContentQuality
    arabic_ratio: float
    educational_keywords: List[str]
    technical_terms: List[str]
    formulas_count: int
    issues_found: List[str]
    suggestions: List[str]
    readability_score: float

class UltraTextProcessor:
    """معالج النصوص الفائق"""
    
    def __init__(self):
        self.educational_keywords = {
            'theory': ['قانون', 'نظرية', 'مبدأ', 'قاعدة', 'أساس', 'مفهوم'],
            'example': ['مثال', 'توضيح', 'تطبيق', 'حالة', 'مسألة'],
            'definition': ['تعريف', 'معنى', 'مصطلح', 'يعني', 'هو عبارة عن'],
            'formula': ['معادلة', 'صيغة', 'قانون', 'حساب', 'نتيجة'],
            'exercise': ['تمرين', 'سؤال', 'مسألة', 'احسب', 'أوجد', 'حل']
        }
        
        self.noise_patterns = [
            # HTML وتعليقات Landing AI
            r'<!--[\s\S]*?-->',
            r'<!-- text,[\s\S]*?-->',
            r'<!-- figure,[\s\S]*?-->',
            r'<!-- marginalia,[\s\S]*?-->',
            r'<!-- illustration,[\s\S]*?-->',
            r'<!-- table,[\s\S]*?-->',
            
            # معلومات الصفحة والإحداثيات
            r'from page \d+ \([^)]+\)',
            r'with ID [a-f0-9\-]+',
            r'\(l=[\d.]+,t=[\d.]+,r=[\d.]+,b=[\d.]+\)',
            
            # أوصاف الصور الإنجليزية
            r'Summary\s*:\s*This[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            r'Scene Overview\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            r'Technical Details\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            r'Spatial Relationships\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            r'Analysis\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            r'photo\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            r'illustration\s*:[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            
            # نقاط وصف إنجليزية
            r'^\s*•\s+The[\s\S]*?(?=\n)',
            r'^\s*•\s+Each[\s\S]*?(?=\n)',
            r'^\s*•\s+No scale[\s\S]*?(?=\n)',
            r'^\s*•\s+Arabic text[\s\S]*?(?=\n)',
            
            # عبارات وصفية عامة
            r'The image[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            r'This figure[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
            r'The figure[\s\S]*?(?=\n\n|\n[أ-ي]|\Z)',
        ]
        
        self.improvement_patterns = [
            # تحسين علامات الترقيم العربية
            (r'\s*([،؛؟!])\s*', r'\1 '),
            (r'\s*([:])\s*', r'\1 '),
            
            # إزالة المسافات الزائدة
            (r'\s+', ' '),
            (r'\n\s*\n\s*\n+', '\n\n'),
            
            # تحسين كتابة الأرقام العربية
            (r'(\d+)\s*([أ-ي])', r'\1. \2'),
        ]

    async def ultra_clean_text(self, text: str) -> TextAnalysis:
        """تنظيف فائق للنص مع تحليل شامل"""
        if not text:
            return self._create_empty_analysis()
        
        original_length = len(text)
        original_text = text
        
        # 1. إزالة الضوضاء
        for pattern in self.noise_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL)
        
        # 2. تنظيف السطور
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if self._is_useful_line(line):
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # 3. تطبيق تحسينات
        for pattern, replacement in self.improvement_patterns:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        
        # 4. تنظيف نهائي
        text = text.strip()
        
        # 5. إنشاء التحليل الشامل
        return await self._analyze_text(original_text, text, original_length)

    def _is_useful_line(self, line: str) -> bool:
        """تحديد إذا كان السطر مفيداً أم لا"""
        if not line or len(line.strip()) < 3:
            return False
        
        # تجاهل السطور التي تحتوي على وصف إنجليزي فقط
        if re.match(r'^[a-zA-Z\s\.,;:!?\-()0-9]+$', line):
            return False
            
        # تجاهل أرقام الصفحات والإحداثيات
        if re.match(r'^\d+$|^page \d+|^\([lr]=[\d.]+', line):
            return False
            
        # تجاهل السطور التي تحتوي على معرفات فقط
        if re.match(r'^[a-f0-9\-]+$', line):
            return False
            
        return True

    async def _analyze_text(self, original: str, cleaned: str, original_length: int) -> TextAnalysis:
        """تحليل شامل للنص"""
        cleaned_length = len(cleaned)
        reduction_percentage = ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0
        
        # تحليل اللغة والمحتوى ثنائي اللغة
        language_analysis = self._detect_languages(cleaned)
        arabic_ratio = language_analysis['arabic_ratio']
        english_ratio = language_analysis['english_ratio']
        primary_language = language_analysis['primary_language']
        
        # استخراج الكلمات المفتاحية التعليمية
        educational_keywords = self._extract_educational_keywords(cleaned)
        
        # استخراج المصطلحات التقنية
        technical_terms = self._extract_technical_terms(cleaned)
        
        # عد المعادلات والصيغ
        formulas_count = len(re.findall(r'=|∑|∫|√|π|α|β|γ|\+|\-|\*|÷', cleaned))
        
        # تحديد نوع المحتوى
        content_type = self._classify_content_type(cleaned, educational_keywords)
        
        # تقييم الجودة
        quality_score = self._calculate_quality_score(cleaned, arabic_ratio, educational_keywords, technical_terms)
        quality_rating = self._get_quality_rating(quality_score)
        
        # تحليل القابلية للقراءة
        readability_score = self._calculate_readability(cleaned)
        
        # العثور على المشاكل والاقتراحات
        issues_found = self._find_issues(cleaned)
        suggestions = self._generate_suggestions(issues_found, quality_score, arabic_ratio)
        
        return TextAnalysis(
            original_length=original_length,
            cleaned_length=cleaned_length,
            reduction_percentage=reduction_percentage,
            quality_score=quality_score,
            content_type=content_type,
            quality_rating=quality_rating,
            arabic_ratio=arabic_ratio,
            educational_keywords=educational_keywords,
            technical_terms=technical_terms,
            formulas_count=formulas_count,
            issues_found=issues_found,
            suggestions=suggestions,
            readability_score=readability_score
        )

    def _extract_educational_keywords(self, text: str) -> List[str]:
        """استخراج الكلمات المفتاحية التعليمية"""
        found_keywords = []
        text_lower = text.lower()
        
        for category, keywords in self.educational_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))

    def _extract_technical_terms(self, text: str) -> List[str]:
        """استخراج المصطلحات التقنية"""
        # قائمة بالمصطلحات التقنية الشائعة
        tech_terms = [
            'الجزيء', 'الذرة', 'التفاعل', 'المعادلة', 'الخاصية',
            'النسبة', 'المعدل', 'الثابت', 'المتغير', 'الدالة',
            'الخوارزمية', 'البرمجة', 'البيانات', 'الشبكة', 'النظام'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in tech_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms

    def _classify_content_type(self, text: str, keywords: List[str]) -> TextType:
        """تصنيف نوع المحتوى"""
        text_lower = text.lower()
        
        # عد أنواع الكلمات المفتاحية
        theory_count = sum(1 for kw in keywords if any(t in kw for t in self.educational_keywords['theory']))
        example_count = sum(1 for kw in keywords if any(t in kw for t in self.educational_keywords['example']))
        definition_count = sum(1 for kw in keywords if any(t in kw for t in self.educational_keywords['definition']))
        formula_count = sum(1 for kw in keywords if any(t in kw for t in self.educational_keywords['formula']))
        exercise_count = sum(1 for kw in keywords if any(t in kw for t in self.educational_keywords['exercise']))
        
        # التصنيف بناءً على أعلى عدد
        counts = {
            TextType.THEORY: theory_count,
            TextType.EXAMPLE: example_count,
            TextType.DEFINITION: definition_count,
            TextType.FORMULA: formula_count,
            TextType.EXERCISE: exercise_count
        }
        
        max_type = max(counts.keys(), key=lambda k: counts[k])
        
        # إذا كان هناك تنوع في الأنواع، فهو مختلط
        if sum(1 for c in counts.values() if c > 0) > 2:
            return TextType.MIXED
        
        return max_type

    def _calculate_quality_score(self, text: str, arabic_ratio: float, 
                                educational_keywords: List[str], technical_terms: List[str]) -> float:
        """حساب نقاط الجودة"""
        score = 0.0
        
        # نقاط للمحتوى العربي (40%)
        score += arabic_ratio * 40
        
        # نقاط للكلمات التعليمية (30%)
        if len(educational_keywords) > 0:
            score += min(len(educational_keywords) * 5, 30)
        
        # نقاط للمصطلحات التقنية (20%)
        if len(technical_terms) > 0:
            score += min(len(technical_terms) * 4, 20)
        
        # نقاط لطول النص المناسب (10%)
        if 50 <= len(text) <= 1000:
            score += 10
        elif len(text) > 1000:
            score += 8
        elif len(text) > 20:
            score += 5
        
        return min(score, 100)

    def _get_quality_rating(self, score: float) -> ContentQuality:
        """تحديد تقييم الجودة"""
        if score >= 85:
            return ContentQuality.EXCELLENT
        elif score >= 70:
            return ContentQuality.GOOD
        elif score >= 55:
            return ContentQuality.ACCEPTABLE
        elif score >= 35:
            return ContentQuality.POOR
        else:
            return ContentQuality.VERY_POOR

    def _calculate_readability(self, text: str) -> float:
        """حساب سهولة القراءة للنص العربي"""
        if not text:
            return 0.0
        
        sentences = len(re.findall(r'[.!?؟]', text))
        words = len(text.split())
        
        if sentences == 0:
            return 50.0  # متوسط افتراضي
        
        avg_words_per_sentence = words / sentences
        
        # معادلة مبسطة لسهولة القراءة العربية
        readability = 100 - (avg_words_per_sentence * 1.5)
        
        return max(0, min(100, readability))

    def _find_issues(self, text: str) -> List[str]:
        """العثور على المشاكل في النص"""
        issues = []
        
        if len(text) < 20:
            issues.append("النص قصير جداً")
        
        if len(re.findall(r'[أ-ي]', text)) / len(text) < 0.3:
            issues.append("نسبة المحتوى العربي منخفضة")
        
        if len(text.split()) < 5:
            issues.append("عدد الكلمات قليل جداً")
        
        # فحص علامات الترقيم
        if not re.search(r'[.!?؟،]', text):
            issues.append("لا توجد علامات ترقيم")
        
        # فحص الأرقام الإنجليزية في النص العربي
        if re.search(r'[أ-ي].*[0-9].*[أ-ي]', text):
            issues.append("خلط بين الأرقام الإنجليزية والنص العربي")
        
        return issues

    def _generate_suggestions(self, issues: List[str], quality_score: float, arabic_ratio: float) -> List[str]:
        """إنتاج اقتراحات للتحسين"""
        suggestions = []
        
        if quality_score < 50:
            suggestions.append("يحتاج النص إلى تحسين كبير في الجودة")
        
        if arabic_ratio < 0.5:
            suggestions.append("زيادة المحتوى العربي سيحسن من جودة المقارنة")
        
        if "النص قصير جداً" in issues:
            suggestions.append("إضافة المزيد من التفاصيل التعليمية")
        
        if "لا توجد علامات ترقيم" in issues:
            suggestions.append("إضافة علامات الترقيم المناسبة")
        
        if not suggestions:
            suggestions.append("النص في حالة جيدة ولا يحتاج تحسينات كبيرة")
        
        return suggestions

    def _create_empty_analysis(self) -> TextAnalysis:
        """إنشاء تحليل فارغ"""
        return TextAnalysis(
            original_length=0,
            cleaned_length=0,
            reduction_percentage=0.0,
            quality_score=0.0,
            content_type=TextType.MIXED,
            quality_rating=ContentQuality.VERY_POOR,
            arabic_ratio=0.0,
            educational_keywords=[],
            technical_terms=[],
            formulas_count=0,
            issues_found=["النص فارغ"],
            suggestions=["إضافة محتوى للمعالجة"],
            readability_score=0.0
        )

    async def process_multiple_files(self, file_paths: List[str]) -> Dict[str, Tuple[str, TextAnalysis]]:
        """معالجة ملفات متعددة بشكل متوازي"""
        results = {}
        
        async def process_single(file_path: str):
            try:
                if not Path(file_path).exists():
                    return file_path, ("", self._create_empty_analysis())
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                analysis = await self.ultra_clean_text(content)
                return file_path, (content, analysis)
            except Exception as e:
                return file_path, ("", self._create_empty_analysis())
        
        # معالجة متوازية
        tasks = [process_single(fp) for fp in file_paths]
        task_results = await asyncio.gather(*tasks)
        
        for file_path, (content, analysis) in task_results:
            results[file_path] = (content, analysis)
        
        return results

    async def process_folder(self, folder_path: str, file_extensions: List[str] = ['.txt', '.md']) -> Dict[str, Tuple[str, TextAnalysis]]:
        """معالجة مجلد كامل"""
        folder = Path(folder_path)
        if not folder.exists():
            return {}
        
        file_paths = []
        for ext in file_extensions:
            file_paths.extend([str(f) for f in folder.rglob(f'*{ext}')])
        
        return await self.process_multiple_files(file_paths)

    def compare_texts_ultra(self, text1: str, text2: str) -> Dict[str, Any]:
        """مقارنة فائقة بين نصين"""
        # تنظيف النصوص أولاً
        import asyncio
        loop = asyncio.get_event_loop()
        
        analysis1 = loop.run_until_complete(self.ultra_clean_text(text1))
        analysis2 = loop.run_until_complete(self.ultra_clean_text(text2))
        
        # المقارنة التفصيلية
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio() * 100
        
        # تحليل الاختلافات
        diff = list(difflib.unified_diff(
            text1.splitlines(),
            text2.splitlines(),
            lineterm='',
            fromfile='النص الأول',
            tofile='النص الثاني'
        ))
        
        return {
            'similarity_percentage': similarity,
            'text1_analysis': asdict(analysis1),
            'text2_analysis': asdict(analysis2),
            'quality_difference': abs(analysis1.quality_score - analysis2.quality_score),
            'content_type_match': analysis1.content_type == analysis2.content_type,
            'differences_count': len(diff),
            'differences': diff[:10],  # أول 10 اختلافات
            'recommendation': self._get_comparison_recommendation(analysis1, analysis2, similarity)
        }

    def _get_comparison_recommendation(self, analysis1: TextAnalysis, analysis2: TextAnalysis, similarity: float) -> str:
        """اقتراح بناءً على المقارنة"""
        if similarity > 85:
            return "النصان متشابهان جداً - مقارنة موثوقة"
        elif similarity > 70:
            return "النصان متشابهان إلى حد كبير - مقارنة جيدة"
        elif similarity > 50:
            return "النصان لديهما تشابه متوسط - مقارنة مقبولة"
        elif analysis1.content_type == analysis2.content_type:
            return "النصان من نفس النوع لكن مختلفان في المحتوى"
        else:
            return "النصان مختلفان جداً - قد تحتاج مراجعة المقارنة"

    def generate_detailed_report(self, analysis: TextAnalysis, original_text: str = "", cleaned_text: str = "") -> str:
        """إنتاج تقرير مفصل بالعربية"""
        report = f"""
# تقرير تحليل النص المفصل
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## الإحصائيات الأساسية
- **الطول الأصلي**: {analysis.original_length:,} حرف
- **الطول بعد التنظيف**: {analysis.cleaned_length:,} حرف
- **نسبة التخفيض**: {analysis.reduction_percentage:.1f}%
- **نسبة المحتوى العربي**: {analysis.arabic_ratio:.1f}%

## تقييم الجودة
- **النقاط**: {analysis.quality_score:.1f}/100
- **التقييم**: {analysis.quality_rating.value}
- **سهولة القراءة**: {analysis.readability_score:.1f}/100

## تصنيف المحتوى
- **نوع المحتوى**: {analysis.content_type.value}
- **عدد المعادلات**: {analysis.formulas_count}

## الكلمات المفتاحية التعليمية
{', '.join(analysis.educational_keywords) if analysis.educational_keywords else 'لم يتم العثور على كلمات مفتاحية'}

## المصطلحات التقنية
{', '.join(analysis.technical_terms) if analysis.technical_terms else 'لم يتم العثور على مصطلحات تقنية'}

## المشاكل المكتشفة
"""
        
        for issue in analysis.issues_found:
            report += f"❌ {issue}\n"
        
        report += "\n## الاقتراحات للتحسين\n"
        for suggestion in analysis.suggestions:
            report += f"💡 {suggestion}\n"
        
        if cleaned_text:
            report += f"\n## النص بعد التنظيف\n```\n{cleaned_text[:500]}{'...' if len(cleaned_text) > 500 else ''}\n```"
        
        report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return report

    async def process_file(self, file_path: str) -> Tuple[str, TextAnalysis]:
        """معالجة ملف واحد"""
        try:
            if not Path(file_path).exists():
                return "", self._create_empty_analysis()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = await self.ultra_clean_text(content)
            return content, analysis
        except Exception as e:
            return "", self._create_empty_analysis()

    def generate_report(self, analysis: TextAnalysis, filename: str = "") -> str:
        """إنتاج تقرير مبسط"""
        return f"""
تقرير تحليل الملف: {filename}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 إحصائيات:
   الطول الأصلي: {analysis.original_length:,} حرف
   الطول المنظف: {analysis.cleaned_length:,} حرف
   نسبة التخفيض: {analysis.reduction_percentage:.1f}%

🎯 الجودة: {analysis.quality_score:.1f}/100 ({analysis.quality_rating.value})
📖 نوع المحتوى: {analysis.content_type.value}
🔤 نسبة العربي: {analysis.arabic_ratio:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    async def process_directory(self, directory: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """معالجة مجلد كامل"""
        if extensions is None:
            extensions = ['.txt', '.md', '.json']
        
        results = await self.process_folder(directory, extensions)
        
        total_files = len(results)
        processed_files = len([r for r in results.values() if r[1].original_length > 0])
        
        # إحصائيات إجمالية
        total_original = sum(r[1].original_length for r in results.values())
        total_cleaned = sum(r[1].cleaned_length for r in results.values())
        avg_quality = sum(r[1].quality_score for r in results.values()) / total_files if total_files > 0 else 0
        
        return {
            'total_files': total_files,
            'processed': processed_files,
            'total_original_length': total_original,
            'total_cleaned_length': total_cleaned,
            'overall_reduction': ((total_original - total_cleaned) / total_original * 100) if total_original > 0 else 0,
            'average_quality': avg_quality,
            'results': results
        }

# دوال مساعدة للاستخدام السريع
async def ultra_process_single_file(file_path: str) -> Tuple[str, TextAnalysis, str]:
    """معالجة ملف واحد وإرجاع التقرير"""
    processor = UltraTextProcessor()
    original_text, analysis = await processor.process_file(file_path)
    report = processor.generate_report(analysis, Path(file_path).name)
    return original_text, analysis, report

async def ultra_process_directory(directory: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """معالجة مجلد كامل"""
    processor = UltraTextProcessor()
    return await processor.process_directory(directory, extensions)

# مثال على الاستخدام
if __name__ == "__main__":
    async def test_ultra_processor():
        # اختبار معالجة ملف واحد
        test_file = "backend/uploads/landingai_results/extraction_20250705_172654/extracted_content.md"
        if Path(test_file).exists():
            original, analysis, report = await ultra_process_single_file(test_file)
            print(report)
        
        # اختبار معالجة مجلد
        test_dir = "backend/uploads/landingai_results"
        if Path(test_dir).exists():
            results = await ultra_process_directory(test_dir)
            print(f"\nتم معالجة {results['processed']} ملف من أصل {results['total_files']}")
    
    asyncio.run(test_ultra_processor())
    
    async def test_landing_ai_optimization():
        """اختبار تحسين مخرجات Landing AI"""
        
        # ملف Landing AI المحدد في الطلب
        landing_ai_file = "backend/uploads/landingai_results/extraction_20250705_172654/agentic_doc_result.json"
        
        if Path(landing_ai_file).exists():
            print("🔍 معالجة ملف Landing AI...")
            result = await process_landing_ai_file(landing_ai_file)
            
            if 'error' not in result:
                print(f"✅ تم تحسين النص بنجاح")
                print(f"📊 النص الأصلي: {result['optimization_stats']['original_length']} حرف")
                print(f"📊 النص المحسن: {result['optimization_stats']['optimized_length']} حرف")
                print(f"📊 نسبة التحسين: {result['optimization_stats']['reduction_percentage']:.1f}%")
                print(f"🎯 جاهزية Gemini: {result['optimization_stats']['gemini_readiness_score']:.1f}/100")
                
                # حفظ النتيجة
                output_file = "optimized_landing_ai_output.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result['optimized_text'])
                print(f"💾 تم حفظ النص المحسن في: {output_file}")
            else:
                print(f"❌ خطأ: {result['error']}")
        
        # اختبار مجلد النتائج
        results_dir = "backend/uploads/landingai_results"
        if Path(results_dir).exists():
            print(f"\n📁 معالجة مجلد النتائج: {results_dir}")
            folder_results = await ultra_process_directory(results_dir, ['.md', '.json', '.txt'])
            
            print(f"📊 تم معالجة {folder_results['processed']} ملف من أصل {folder_results['total_files']}")
            print(f"📊 متوسط الجودة: {folder_results['average_quality']:.1f}/100")
            print(f"📊 نسبة التخفيض الإجمالية: {folder_results['overall_reduction']:.1f}%")
    
    # تشغيل الاختبار
    asyncio.run(test_landing_ai_optimization())

# دوال إضافية لتحسين Landing AI
async def process_landing_ai_file(file_path: str) -> Dict[str, Any]:
    """معالجة متقدمة لملف Landing AI JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # استخراج النص من البيانات المعقدة
        extracted_text = extract_text_from_landing_ai(data)
        
        # تحسين النص لـ Gemini
        processor = UltraTextProcessor()
        optimized_text = await optimize_for_gemini(extracted_text, processor)
        
        # إحصائيات التحسين
        original_length = len(extracted_text)
        optimized_length = len(optimized_text)
        reduction_percentage = ((original_length - optimized_length) / original_length * 100) if original_length > 0 else 0
        
        # تقييم جاهزية Gemini
        gemini_score = calculate_gemini_readiness(optimized_text)
        
        return {
            'original_text': extracted_text,
            'optimized_text': optimized_text,
            'optimization_stats': {
                'original_length': original_length,
                'optimized_length': optimized_length,
                'reduction_percentage': reduction_percentage,
                'gemini_readiness_score': gemini_score
            }
        }
    except Exception as e:
        return {'error': str(e)}

def extract_text_from_landing_ai(data: Dict) -> str:
    """استخراج النص المفيد من بيانات Landing AI"""
    text_parts = []
    
    # استخراج النص الرئيسي
    if 'agentic_doc_result' in data:
        result = data['agentic_doc_result']
        
        # النص المستخرج
        if 'extracted_text' in result:
            text_parts.append(result['extracted_text'])
        
        # وصف الصور (مبسط)
        if 'image_descriptions' in result:
            for desc in result['image_descriptions']:
                if len(desc) < 200:  # فقط الأوصاف المختصرة
                    text_parts.append(f"[صورة: {desc}]")
        
        # المحتوى النصي من الصفحات
        if 'pages' in result:
            for page in result['pages']:
                if 'text_content' in page:
                    text_parts.append(page['text_content'])
    
    # استخراج من البنية البديلة
    elif 'extracted_text' in data:
        text_parts.append(data['extracted_text'])
    
    # استخراج من النتائج المباشرة
    elif 'result' in data:
        if isinstance(data['result'], str):
            text_parts.append(data['result'])
        elif isinstance(data['result'], dict):
            for key, value in data['result'].items():
                if isinstance(value, str) and len(value) > 50:
                    text_parts.append(value)
    
    return '\n'.join(text_parts)

async def optimize_for_gemini(text: str, processor: UltraTextProcessor) -> str:
    """تحسين النص ليكون مناسب لـ Gemini"""
    # تنظيف أولي
    analysis = await processor.ultra_clean_text(text)
    
    # إزالة التفاصيل الزائدة
    lines = text.split('\n')
    optimized_lines = []
    
    for line in lines:
        line = line.strip()
        
        # تخطي الأسطر الفارغة والطويلة جداً
        if not line or len(line) > 500:
            continue
        
        # تخطي التفاصيل التقنية المعقدة
        if any(keyword in line.lower() for keyword in [
            'metadata', 'coordinate', 'pixel', 'rgb', 'hex',
            'json', 'array', 'object', 'null', 'undefined'
        ]):
            continue
        
        # تبسيط أوصاف الصور
        if line.startswith('[صورة:'):
            # اختصار الوصف
            if len(line) > 100:
                line = line[:97] + '...]'
        
        # إزالة الأرقام المعقدة والمعادلات المطولة
        if re.search(r'\d{5,}', line) or line.count('=') > 3:
            continue
        
        optimized_lines.append(line)
    
    # دمج الأسطر المتشابهة
    final_lines = []
    prev_line = ""
    
    for line in optimized_lines:
        # تجنب التكرار
        if line != prev_line and not (len(line) < 10 and line in prev_line):
            final_lines.append(line)
        prev_line = line
    
    return '\n'.join(final_lines)

def calculate_gemini_readiness(text: str) -> float:
    """حساب مدى جاهزية النص لـ Gemini"""
    if not text:
        return 0
    
    score = 100
    
    # طول النص
    length = len(text)
    if length > 10000:
        score -= 20
    elif length > 5000:
        score -= 10
    elif length < 100:
        score -= 30
    
    # نسبة المحتوى العربي
    arabic_chars = len(re.findall(r'[أ-ي]', text))
    arabic_ratio = arabic_chars / length if length > 0 else 0
    
    if arabic_ratio < 0.3:
        score -= 15
    elif arabic_ratio > 0.8:
        score += 10
    
    # وجود محتوى تعليمي
    educational_keywords = [
        'تعليم', 'دراسة', 'تعلم', 'شرح', 'توضيح',
        'مفهوم', 'درس', 'محاضرة', 'كتاب', 'مقرر'
    ]
    
    found_keywords = sum(1 for keyword in educational_keywords if keyword in text)
    if found_keywords == 0:
        score -= 10
    else:
        score += min(found_keywords * 2, 10)
    
    # وضوح البنية
    if text.count('\n') < 3:
        score -= 5
    
    # تجنب النصوص المعقدة
    if text.count('{') > 5 or text.count('[') > 10:
        score -= 15
    
    return max(0, min(100, score))

# إضافة فئة للمقارنة المحسنة
class EnhancedComparison:
    """فئة للمقارنة المحسنة"""
    
    def __init__(self):
        self.processor = UltraTextProcessor()
    
    async def compare_educational_content(self, text1: str, text2: str) -> Dict[str, Any]:
        """مقارنة محسنة للمحتوى التعليمي"""
        
        # تحليل النصوص
        analysis1 = await self.processor.ultra_clean_text(text1)
        analysis2 = await self.processor.ultra_clean_text(text2)
        
        # مقارنة الكلمات المفتاحية التعليمية
        common_keywords = set(analysis1.educational_keywords) & set(analysis2.educational_keywords)
        keyword_similarity = len(common_keywords) / max(len(analysis1.educational_keywords), len(analysis2.educational_keywords), 1) * 100
        
        # مقارنة المصطلحات التقنية
        common_terms = set(analysis1.technical_terms) & set(analysis2.technical_terms)
        terms_similarity = len(common_terms) / max(len(analysis1.technical_terms), len(analysis2.technical_terms), 1) * 100
        
        # مقارنة نوع المحتوى
        content_type_match = analysis1.content_type == analysis2.content_type
        
        # مقارنة جودة المحتوى
        quality_similarity = 100 - abs(analysis1.quality_score - analysis2.quality_score)
        
        # حساب التشابه الإجمالي
        overall_similarity = (keyword_similarity + terms_similarity + quality_similarity) / 3
        
        return {
            'overall_similarity': overall_similarity,
            'keyword_similarity': keyword_similarity,
            'terms_similarity': terms_similarity,
            'quality_similarity': quality_similarity,
            'content_type_match': content_type_match,
            'common_keywords': list(common_keywords),
            'common_terms': list(common_terms),
            'quality_difference': abs(analysis1.quality_score - analysis2.quality_score),
            'recommendation': self._get_enhanced_recommendation(overall_similarity, content_type_match),
            'detailed_analysis': {
                'text1_stats': {
                    'length': analysis1.cleaned_length,
                    'quality': analysis1.quality_score,
                    'type': analysis1.content_type.value,
                    'arabic_ratio': analysis1.arabic_ratio
                },
                'text2_stats': {
                    'length': analysis2.cleaned_length,
                    'quality': analysis2.quality_score,
                    'type': analysis2.content_type.value,
                    'arabic_ratio': analysis2.arabic_ratio
                }
            }
        }
    
    def _get_enhanced_recommendation(self, similarity: float, type_match: bool) -> str:
        """اقتراح محسن للمقارنة"""
        if similarity > 80 and type_match:
            return "محتوى متطابق تقريباً - مقارنة ممتازة"
        elif similarity > 60 and type_match:
            return "محتوى متشابه في الموضوع - مقارنة جيدة"
        elif similarity > 40:
            return "تشابه متوسط - قد يحتاج مراجعة"
        elif type_match:
            return "نفس نوع المحتوى لكن موضوعات مختلفة"
        else:
            return "محتوى مختلف - تأكد من صحة المقارنة"

# دالة للمعالجة السريعة
async def quick_process_and_compare(file1: str, file2: str) -> Dict[str, Any]:
    """معالجة ومقارنة سريعة لملفين"""
    processor = UltraTextProcessor()
    comparator = EnhancedComparison()
    
    try:
        # قراءة الملفات
        with open(file1, 'r', encoding='utf-8') as f:
            text1 = f.read()
        
        with open(file2, 'r', encoding='utf-8') as f:
            text2 = f.read()
        
        # معالجة وتحليل
        analysis1 = await processor.ultra_clean_text(text1)
        analysis2 = await processor.ultra_clean_text(text2)
        
        # مقارنة محسنة
        comparison = await comparator.compare_educational_content(text1, text2)
        
        return {
            'file1_analysis': asdict(analysis1),
            'file2_analysis': asdict(analysis2),
            'comparison_results': comparison,
            'processing_time': time.time(),
            'success': True
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

# دالة للمعالجة المتقدمة للمجلدات
async def advanced_folder_processing(folder_path: str, output_dir: str = "processed_results") -> Dict[str, Any]:
    """معالجة متقدمة للمجلدات مع حفظ النتائج"""
    
    processor = UltraTextProcessor()
    results_dir = Path(output_dir)
    results_dir.mkdir(exist_ok=True)
    
    # معالجة المجلد
    folder_results = await processor.process_directory(folder_path)
    
    # حفظ النتائج المفصلة
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # ملف التقرير الإجمالي
    summary_file = results_dir / f"processing_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'folder_path': folder_path,
            'total_files': folder_results['total_files'],
            'processed_files': folder_results['processed'],
            'overall_reduction': folder_results['overall_reduction'],
            'average_quality': folder_results['average_quality']
        }, f, ensure_ascii=False, indent=2)
    
    # حفظ تفاصيل كل ملف
    details_file = results_dir / f"detailed_results_{timestamp}.json"
    serializable_results = {}
    
    for file_path, (content, analysis) in folder_results['results'].items():
        serializable_results[file_path] = {
            'analysis': asdict(analysis),
            'content_preview': content[:500] + '...' if len(content) > 500 else content
        }
    
    with open(details_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    return {
        'summary': folder_results,
        'summary_file': str(summary_file),
        'details_file': str(details_file),
        'timestamp': timestamp
    }
