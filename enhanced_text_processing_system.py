#!/usr/bin/env python3
"""
نظام معالجة النصوص المحسن - Enhanced Text Processing System
نظام شامل لتحسين استخراج ومعالجة النصوص من المستندات التعليمية

يشمل:
1. معالجة محسنة لنصوص Landing AI
2. تنظيف ذكي للمحتوى غير المرغوب
3. معالجة ملفات متعددة ومجلدات كاملة
4. تسريع العمليات بالمعالجة المتوازية
5. تحسين دقة المقارنات
"""

import os
import re
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
from loguru import logger
import aiofiles
import tempfile
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from functools import lru_cache

# إعداد الـ logging
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}",
    level="INFO"
)

class ContentType(Enum):
    """أنواع المحتوى المختلفة"""
    EDUCATIONAL_TEXT = "educational_text"
    FIGURE_DESCRIPTION = "figure_description"
    TECHNICAL_METADATA = "technical_metadata"
    COORDINATES = "coordinates"
    NOISE = "noise"
    UNKNOWN = "unknown"

@dataclass
class ProcessingResult:
    """نتيجة معالجة نص"""
    original_text: str
    cleaned_text: str
    content_type: ContentType
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]
    chunks_removed: List[str]
    chunks_kept: List[str]

@dataclass
class BatchProcessingResult:
    """نتيجة معالجة مجموعة من الملفات"""
    total_files: int
    processed_files: int
    failed_files: int
    total_time: float
    results: List[ProcessingResult]
    summary_stats: Dict[str, Any]

class AdvancedTextProcessor:
    """معالج النصوص المتقدم"""
    
    def __init__(self, num_workers: int = None):
        """
        تهيئة المعالج
        
        Args:
            num_workers: عدد العمليات المتوازية (افتراضي: عدد المعالجات)
        """
        self.num_workers = num_workers or min(8, multiprocessing.cpu_count())
        
        # أنماط تنظيف محسنة
        self.cleanup_patterns = self._initialize_cleanup_patterns()
        
        # أنماط التعرف على المحتوى التعليمي
        self.educational_patterns = self._initialize_educational_patterns()
        
        # إحصائيات المعالجة
        self.stats = {
            'total_processed': 0,
            'total_cleaned': 0,
            'average_reduction': 0.0,
            'processing_times': []
        }
        
        logger.info(f"🚀 تم تهيئة معالج النصوص المتقدم مع {self.num_workers} عمليات متوازية")

    def _initialize_cleanup_patterns(self) -> Dict[str, List[str]]:
        """تهيئة أنماط التنظيف المختلفة"""
        return {
            # إزالة تعليقات HTML وتفاصيل Landing AI
            'html_comments': [
                r'<!--[\s\S]*?-->',
                r'<!-- text,[\s\S]*?-->',
                r'<!-- figure,[\s\S]*?-->',
                r'<!-- marginalia,[\s\S]*?-->',
                r'<!-- illustration,[\s\S]*?-->',
                r'<!-- table,[\s\S]*?-->'
            ],
            
            # إزالة أقسام وصف الصور
            'image_descriptions': [
                r'Summary\s*:\s*This[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'photo\s*:[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'illustration\s*:[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'Scene Overview\s*:[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'Technical Details\s*:[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'Spatial Relationships\s*:[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'Analysis\s*:[\s\S]*?(?=\n\n|\n[أ-ي])'
            ],
            
            # إزالة الإحداثيات والتفاصيل التقنية
            'coordinates': [
                r'from page \d+ \(l=[\d.]+,t=[\d.]+,r=[\d.]+,b=[\d.]+\)',
                r'with ID [a-f0-9\-]+',
                r'\(l=[\d.]+,t=[\d.]+,r=[\d.]+,b=[\d.]+\)',
                r'page \d+',
                r'ID [a-f0-9\-]+'
            ],
            
            # إزالة النصوص الإنجليزية غير المفيدة
            'english_noise': [
                r'The image[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'This figure[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'The figure[\s\S]*?(?=\n\n|\n[أ-ي])',
                r'^\s*•\s+The[\s\S]*?(?=\n)',
                r'^\s*•\s+Each[\s\S]*?(?=\n)',
                r'^\s*•\s+No scale[\s\S]*?(?=\n)'
            ],
            
            # تنظيف عام
            'whitespace': [
                r'\n\s*\n\s*\n+',  # أسطر فارغة متعددة
                r'^\s+',  # مسافات في بداية السطر
                r'\s+$',  # مسافات في نهاية السطر
                r'\s+',   # مسافات متعددة
            ]
        }

    def _initialize_educational_patterns(self) -> List[str]:
        """تهيئة أنماط التعرف على المحتوى التعليمي"""
        return [
            # النصوص العربية التعليمية
            r'[أ-ي]+.*[:.؟!]',
            r'الفصل\s+\d+',
            r'قاعدة|مبدأ|نظرية|قانون',
            r'تعريف|تطبيق|مثال|ملاحظة',
            r'يؤثر|ينتقل|يعمل|يستخدم',
            
            # المعادلات والرموز
            r'\$.*?\$',
            r'=\s*[\d\w]+',
            r'[A-Za-z]\s*=\s*[A-Za-z\d]+',
            
            # العناوين والترقيم
            r'^\d+[\.\-]\d*',
            r'^[أ-ي]+\s*:',
            r'^\*\s+[أ-ي]+'
        ]

    def classify_content(self, text: str) -> Tuple[ContentType, float]:
        """
        تصنيف نوع المحتوى
        
        Returns:
            Tuple[ContentType, float]: نوع المحتوى ودرجة الثقة
        """
        if not text.strip():
            return ContentType.NOISE, 1.0
        
        # فحص التعليقات التقنية
        if re.search(r'<!--.*?-->', text):
            return ContentType.TECHNICAL_METADATA, 0.9
        
        # فحص الإحداثيات
        if re.search(r'\(l=[\d.]+,t=[\d.]+', text):
            return ContentType.COORDINATES, 0.95
        
        # فحص أوصاف الصور
        if any(keyword in text.lower() for keyword in ['summary :', 'photo:', 'scene overview', 'analysis :']):
            return ContentType.FIGURE_DESCRIPTION, 0.8
        
        # فحص المحتوى التعليمي
        educational_score = 0
        for pattern in self.educational_patterns:
            if re.search(pattern, text):
                educational_score += 1
        
        if educational_score > 0:
            confidence = min(educational_score / len(self.educational_patterns), 1.0)
            return ContentType.EDUCATIONAL_TEXT, confidence
        
        return ContentType.UNKNOWN, 0.3

    def clean_text_advanced(self, text: str) -> ProcessingResult:
        """
        تنظيف متقدم للنص مع تتبع التفاصيل
        
        Args:
            text: النص المراد تنظيفه
            
        Returns:
            ProcessingResult: نتيجة المعالجة مع التفاصيل
        """
        start_time = datetime.now()
        original_text = text
        chunks_removed = []
        chunks_kept = []
        
        # تصنيف المحتوى الأصلي
        content_type, confidence = self.classify_content(text)
        
        logger.debug(f"🔍 تصنيف المحتوى: {content_type.value} (ثقة: {confidence:.2f})")
        
        # تطبيق أنماط التنظيف بالترتيب
        for category, patterns in self.cleanup_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
                if matches:
                    chunks_removed.extend(matches)
                    text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL)
        
        # تنظيف إضافي للنص العربي
        text = self._clean_arabic_text(text)
        
        # تنظيف المسافات والأسطر الفارغة
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = text.strip()
        
        # حفظ الأجزاء المحتفظ بها
        if text.strip():
            chunks_kept = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # حساب إحصائيات
        reduction_percentage = ((len(original_text) - len(text)) / len(original_text)) * 100 if original_text else 0
        
        metadata = {
            'original_length': len(original_text),
            'cleaned_length': len(text),
            'reduction_percentage': reduction_percentage,
            'removed_chunks_count': len(chunks_removed),
            'kept_chunks_count': len(chunks_kept)
        }
        
        return ProcessingResult(
            original_text=original_text,
            cleaned_text=text,
            content_type=content_type,
            confidence=confidence,
            processing_time=processing_time,
            metadata=metadata,
            chunks_removed=chunks_removed,
            chunks_kept=chunks_kept
        )

    def _clean_arabic_text(self, text: str) -> str:
        """تنظيف خاص بالنص العربي"""
        # إزالة الأحرف الغريبة والرموز غير المرغوبة
        text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\w\s\.\,\!\?\:\;\(\)\[\]\{\}\-\+\=\$\%\@\#\*\/\\\|]', '', text)
        
        # تصحيح المسافات حول علامات الترقيم العربية
        text = re.sub(r'\s*([،؛؟!])\s*', r'\1 ', text)
        text = re.sub(r'\s*([:])\s*', r'\1 ', text)
        
        # تنظيف الأرقام العربية والإنجليزية
        text = re.sub(r'(\d+)\s*([أ-ي])', r'\1 \2', text)
        text = re.sub(r'([أ-ي])\s*(\d+)', r'\1 \2', text)
        
        return text

    async def process_file_async(self, file_path: Union[str, Path]) -> ProcessingResult:
        """
        معالجة ملف واحد بشكل غير متزامن
        
        Args:
            file_path: مسار الملف
            
        Returns:
            ProcessingResult: نتيجة المعالجة
        """
        file_path = Path(file_path)
        
        try:
            logger.info(f"📄 معالجة الملف: {file_path.name}")
            
            # قراءة الملف
            if file_path.suffix.lower() == '.json':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    text = data.get('markdown', '') or data.get('text', '')
            else:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    text = await f.read()
            
            # معالجة النص
            result = self.clean_text_advanced(text)
            
            # حفظ النتيجة
            await self._save_processed_result(file_path, result)
            
            logger.success(f"✅ تم معالجة {file_path.name} - تحسن: {result.metadata['reduction_percentage']:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ فشل معالجة {file_path.name}: {e}")
            return ProcessingResult(
                original_text="",
                cleaned_text="",
                content_type=ContentType.UNKNOWN,
                confidence=0.0,
                processing_time=0.0,
                metadata={'error': str(e)},
                chunks_removed=[],
                chunks_kept=[]
            )

    async def _save_processed_result(self, original_path: Path, result: ProcessingResult):
        """حفظ نتيجة المعالجة"""
        output_dir = original_path.parent / "processed"
        output_dir.mkdir(exist_ok=True)
        
        # حفظ النص المنظف
        cleaned_file = output_dir / f"{original_path.stem}_cleaned.md"
        async with aiofiles.open(cleaned_file, 'w', encoding='utf-8') as f:
            await f.write(result.cleaned_text)
        
        # حفظ تقرير المعالجة
        report_file = output_dir / f"{original_path.stem}_processing_report.json"
        report_data = {
            'file_path': str(original_path),
            'processing_time': result.processing_time,
            'content_type': result.content_type.value,
            'confidence': result.confidence,
            'metadata': result.metadata,
            'chunks_removed_count': len(result.chunks_removed),
            'chunks_kept_count': len(result.chunks_kept)
        }
        
        async with aiofiles.open(report_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report_data, ensure_ascii=False, indent=2))

    async def process_directory_batch(self, directory_path: Union[str, Path], 
                                    file_extensions: List[str] = None) -> BatchProcessingResult:
        """
        معالجة مجموعة من الملفات في مجلد
        
        Args:
            directory_path: مسار المجلد
            file_extensions: امتدادات الملفات المراد معالجتها
            
        Returns:
            BatchProcessingResult: نتيجة المعالجة المجمعة
        """
        directory_path = Path(directory_path)
        file_extensions = file_extensions or ['.md', '.txt', '.json']
        
        logger.info(f"📁 بدء معالجة مجموعية للمجلد: {directory_path}")
        
        # البحث عن الملفات
        files_to_process = []
        for ext in file_extensions:
            files_to_process.extend(directory_path.glob(f"**/*{ext}"))
        
        total_files = len(files_to_process)
        logger.info(f"📊 وُجد {total_files} ملف للمعالجة")
        
        if total_files == 0:
            return BatchProcessingResult(
                total_files=0,
                processed_files=0,
                failed_files=0,
                total_time=0.0,
                results=[],
                summary_stats={}
            )
        
        start_time = datetime.now()
        
        # معالجة متوازية
        semaphore = asyncio.Semaphore(self.num_workers)
        
        async def process_with_semaphore(file_path):
            async with semaphore:
                return await self.process_file_async(file_path)
        
        # تشغيل المعالجة المتوازية
        tasks = [process_with_semaphore(file_path) for file_path in files_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # تحليل النتائج
        processed_results = []
        failed_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed_count += 1
                logger.error(f"❌ فشل معالجة ملف: {result}")
            else:
                processed_results.append(result)
        
        total_time = (datetime.now() - start_time).total_seconds()
        processed_count = len(processed_results)
        
        # إحصائيات مجمعة
        summary_stats = self._calculate_batch_stats(processed_results, total_time)
        
        logger.success(f"🎉 اكتملت المعالجة المجمعة في {total_time:.2f}s")
        logger.info(f"📊 معالج: {processed_count}, فشل: {failed_count}")
        
        return BatchProcessingResult(
            total_files=total_files,
            processed_files=processed_count,
            failed_files=failed_count,
            total_time=total_time,
            results=processed_results,
            summary_stats=summary_stats
        )

    def _calculate_batch_stats(self, results: List[ProcessingResult], total_time: float) -> Dict[str, Any]:
        """حساب إحصائيات المعالجة المجمعة"""
        if not results:
            return {}
        
        # إحصائيات الطول
        original_lengths = [r.metadata['original_length'] for r in results]
        cleaned_lengths = [r.metadata['cleaned_length'] for r in results]
        reduction_percentages = [r.metadata['reduction_percentage'] for r in results]
        processing_times = [r.processing_time for r in results]
        
        # إحصائيات أنواع المحتوى
        content_types = {}
        for result in results:
            content_type = result.content_type.value
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            'total_original_length': sum(original_lengths),
            'total_cleaned_length': sum(cleaned_lengths),
            'average_reduction_percentage': statistics.mean(reduction_percentages),
            'median_reduction_percentage': statistics.median(reduction_percentages),
            'average_processing_time': statistics.mean(processing_times),
            'total_processing_time': total_time,
            'content_type_distribution': content_types,
            'files_per_second': len(results) / total_time if total_time > 0 else 0,
            'efficiency_score': (sum(reduction_percentages) / len(results)) * (len(results) / total_time) if total_time > 0 else 0
        }

    def generate_comparison_optimized_text(self, result: ProcessingResult) -> str:
        """
        إنتاج نص محسن للمقارنة
        
        Args:
            result: نتيجة المعالجة
            
        Returns:
            str: النص المحسن للمقارنة
        """
        text = result.cleaned_text
        
        # تحسينات خاصة بالمقارنة
        # 1. توحيد المصطلحات
        text = self._normalize_terminology(text)
        
        # 2. ترتيب المفاهيم
        text = self._organize_concepts(text)
        
        # 3. إزالة التفاصيل غير المهمة للمقارنة
        text = self._remove_comparison_noise(text)
        
        return text.strip()

    def _normalize_terminology(self, text: str) -> str:
        """توحيد المصطلحات العلمية"""
        # قاموس توحيد المصطلحات
        terminology_map = {
            r'قاعدة\s+باسكال|مبدأ\s+باسكال': 'قاعدة باسكال',
            r'الضغط\s+الهيدروليكي|الضغط\s+المائي': 'الضغط الهيدروليكي',
            r'المكبس\s+الهيدروليكي|الكباس\s+الهيدروليكي': 'المكبس الهيدروليكي',
            r'السائل\s+الهيدروليكي|السائل\s+المائي': 'السائل الهيدروليكي'
        }
        
        for pattern, replacement in terminology_map.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text

    def _organize_concepts(self, text: str) -> str:
        """ترتيب المفاهيم حسب الأولوية"""
        lines = text.split('\n')
        organized_lines = []
        
        # ترتيب أولويات: تعريفات، قوانين، تطبيقات، أمثلة
        priorities = {
            'definition': [],  # تعريفات
            'law': [],         # قوانين
            'application': [], # تطبيقات
            'example': [],     # أمثلة
            'other': []        # أخرى
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if re.search(r'تعريف|يُعرف|هو', line):
                priorities['definition'].append(line)
            elif re.search(r'قاعدة|قانون|مبدأ|نظرية', line):
                priorities['law'].append(line)
            elif re.search(r'تطبيق|استخدام|يستخدم', line):
                priorities['application'].append(line)
            elif re.search(r'مثال|مثلاً|على سبيل المثال', line):
                priorities['example'].append(line)
            else:
                priorities['other'].append(line)
        
        # ترتيب النص حسب الأولوية
        for category in ['definition', 'law', 'application', 'example', 'other']:
            organized_lines.extend(priorities[category])
        
        return '\n'.join(organized_lines)

    def _remove_comparison_noise(self, text: str) -> str:
        """إزالة التفاصيل غير المهمة للمقارنة"""
        # إزالة التفاصيل الفرعية التي قد تشوش المقارنة
        noise_patterns = [
            r'كما بالشكل',
            r'انظر الشكل',
            r'في الشكل التالي',
            r'الشكل يوضح',
            r'من الشكل نلاحظ'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text

class SmartBatchProcessor:
    """معالج مجموعي ذكي للملفات الكبيرة"""
    
    def __init__(self, max_workers: int = None, chunk_size: int = 1000):
        self.processor = AdvancedTextProcessor(max_workers)
        self.chunk_size = chunk_size
        
    async def process_large_dataset(self, root_directory: Path, 
                                  output_directory: Path = None) -> Dict[str, Any]:
        """
        معالجة مجموعة بيانات كبيرة مع تحسينات الذاكرة
        
        Args:
            root_directory: المجلد الجذر
            output_directory: مجلد الإخراج
            
        Returns:
            Dict: تقرير شامل عن المعالجة
        """
        root_directory = Path(root_directory)
        output_directory = output_directory or root_directory / "batch_processed"
        output_directory.mkdir(exist_ok=True)
        
        logger.info(f"🏭 بدء المعالجة المجموعية الذكية لـ: {root_directory}")
        
        # العثور على جميع الملفات
        all_files = list(root_directory.rglob("*.md")) + \
                   list(root_directory.rglob("*.txt")) + \
                   list(root_directory.rglob("*.json"))
        
        total_files = len(all_files)
        logger.info(f"📊 إجمالي الملفات: {total_files}")
        
        # تجميع الملفات في دفعات
        batches = [all_files[i:i + self.chunk_size] 
                  for i in range(0, total_files, self.chunk_size)]
        
        all_results = []
        batch_reports = []
        
        start_time = datetime.now()
        
        for i, batch in enumerate(batches, 1):
            logger.info(f"📦 معالجة الدفعة {i}/{len(batches)} ({len(batch)} ملف)")
            
            # معالجة الدفعة
            batch_start = datetime.now()
            
            tasks = [self.processor.process_file_async(file_path) for file_path in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            batch_time = (datetime.now() - batch_start).total_seconds()
            
            # تحليل نتائج الدفعة
            successful_results = [r for r in batch_results if not isinstance(r, Exception)]
            failed_count = len(batch_results) - len(successful_results)
            
            batch_report = {
                'batch_number': i,
                'files_count': len(batch),
                'successful_count': len(successful_results),
                'failed_count': failed_count,
                'processing_time': batch_time,
                'files_per_second': len(successful_results) / batch_time if batch_time > 0 else 0
            }
            
            batch_reports.append(batch_report)
            all_results.extend(successful_results)
            
            logger.success(f"✅ اكتملت الدفعة {i} في {batch_time:.2f}s")
            
            # حفظ النتائج المؤقتة
            await self._save_batch_report(output_directory, i, batch_report, successful_results)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # إنتاج التقرير النهائي
        final_report = {
            'processing_summary': {
                'total_files': total_files,
                'total_batches': len(batches),
                'successful_files': len(all_results),
                'failed_files': total_files - len(all_results),
                'total_processing_time': total_time,
                'overall_files_per_second': len(all_results) / total_time if total_time > 0 else 0
            },
            'batch_details': batch_reports,
            'performance_metrics': self._calculate_performance_metrics(all_results, total_time)
        }
        
        # حفظ التقرير النهائي
        await self._save_final_report(output_directory, final_report)
        
        logger.success(f"🎉 اكتملت المعالجة المجموعية الذكية في {total_time:.2f}s")
        logger.info(f"📊 معدل المعالجة: {final_report['processing_summary']['overall_files_per_second']:.2f} ملف/ثانية")
        
        return final_report

    async def _save_batch_report(self, output_dir: Path, batch_num: int, 
                               report: Dict, results: List[ProcessingResult]):
        """حفظ تقرير الدفعة"""
        batch_dir = output_dir / f"batch_{batch_num:03d}"
        batch_dir.mkdir(exist_ok=True)
        
        # حفظ تقرير الدفعة
        report_file = batch_dir / "batch_report.json"
        async with aiofiles.open(report_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report, ensure_ascii=False, indent=2))
        
        # حفظ النصوص المنظفة
        for i, result in enumerate(results):
            if result.cleaned_text.strip():
                cleaned_file = batch_dir / f"cleaned_{i:03d}.md"
                async with aiofiles.open(cleaned_file, 'w', encoding='utf-8') as f:
                    await f.write(result.cleaned_text)

    async def _save_final_report(self, output_dir: Path, report: Dict):
        """حفظ التقرير النهائي"""
        final_report_file = output_dir / "final_processing_report.json"
        async with aiofiles.open(final_report_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report, ensure_ascii=False, indent=2))

    def _calculate_performance_metrics(self, results: List[ProcessingResult], 
                                     total_time: float) -> Dict[str, Any]:
        """حساب مقاييس الأداء"""
        if not results:
            return {}
        
        # تحليل الأداء
        processing_times = [r.processing_time for r in results]
        reduction_percentages = [r.metadata.get('reduction_percentage', 0) for r in results]
        
        return {
            'average_file_processing_time': statistics.mean(processing_times),
            'median_file_processing_time': statistics.median(processing_times),
            'fastest_file_time': min(processing_times),
            'slowest_file_time': max(processing_times),
            'average_size_reduction': statistics.mean(reduction_percentages),
            'total_efficiency_score': (sum(reduction_percentages) / len(results)) * (len(results) / total_time) if total_time > 0 else 0,
            'throughput_files_per_minute': (len(results) / total_time) * 60 if total_time > 0 else 0
        }

# دوال مساعدة للاستخدام المباشر

async def process_single_file(file_path: str) -> ProcessingResult:
    """معالجة ملف واحد"""
    processor = AdvancedTextProcessor()
    return await processor.process_file_async(file_path)

async def process_directory(directory_path: str, extensions: List[str] = None) -> BatchProcessingResult:
    """معالجة مجلد كامل"""
    processor = AdvancedTextProcessor()
    return await processor.process_directory_batch(directory_path, extensions)

async def process_large_dataset(root_dir: str, output_dir: str = None) -> Dict[str, Any]:
    """معالجة مجموعة بيانات كبيرة"""
    batch_processor = SmartBatchProcessor()
    return await batch_processor.process_large_dataset(Path(root_dir), Path(output_dir) if output_dir else None)

# اختبار النظام
async def test_enhanced_system():
    """اختبار النظام المحسن"""
    print("🚀 اختبار نظام معالجة النصوص المحسن")
    print("=" * 60)
    
    # اختبار معالجة ملف واحد
    test_file = "d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results/extraction_20250705_172654/extracted_content.md"
    if Path(test_file).exists():
        print("📄 اختبار معالجة ملف واحد...")
        result = await process_single_file(test_file)
        print(f"✅ تم تنظيف {result.metadata['reduction_percentage']:.1f}% من النص")
        print(f"⏱️ وقت المعالجة: {result.processing_time:.3f}s")
        print(f"🎯 نوع المحتوى: {result.content_type.value}")
    
    # اختبار معالجة مجلد
    test_dir = "d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results"
    if Path(test_dir).exists():
        print(f"\n📁 اختبار معالجة مجلد: {test_dir}")
        batch_result = await process_directory(test_dir, ['.md', '.json'])
        print(f"✅ تم معالجة {batch_result.processed_files} ملف")
        print(f"⏱️ الوقت الإجمالي: {batch_result.total_time:.2f}s")
        print(f"🎯 متوسط التحسن: {batch_result.summary_stats.get('average_reduction_percentage', 0):.1f}%")

if __name__ == "__main__":
    # تشغيل الاختبار
    asyncio.run(test_enhanced_system())
