#!/usr/bin/env python3
"""
نظام المعالجة المتوازية السريع للمجلدات - Fast Parallel Folder Processing System
نظام متقدم لمعالجة مجلدات كاملة من الملفات بسرعة عالية

الميزات:
1. معالجة متوازية للمجلدات الكاملة
2. تسريع العمليات باستخدام async/await ومتعددة المعالجات
3. نظام ذكي لإدارة الذاكرة والموارد
4. تتبع التقدم في الوقت الفعلي
5. إنتاج تقارير مفصلة وإحصائيات الأداء
6. دعم أنواع متعددة من الملفات
7. نظام استرداد من الأخطاء
"""

import os
import asyncio
import aiofiles
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
from dataclasses import dataclass, asdict
from enum import Enum
import time
import psutil
import queue
import threading
from loguru import logger
import hashlib
import pickle
from contextlib import asynccontextmanager
import signal
import sys
from collections import defaultdict, deque
import statistics
import resource
import gc

# إعداد الـ logging المتقدم
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{extra[component]}</cyan> | {message}",
    level="INFO"
)

class ProcessingStatus(Enum):
    """حالات المعالجة"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

@dataclass
class FileTask:
    """مهمة معالجة ملف"""
    file_path: Path
    task_id: str
    priority: int = 0
    estimated_time: float = 0.0
    status: ProcessingStatus = ProcessingStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    result_path: Optional[Path] = None
    metadata: Dict[str, Any] = None

@dataclass
class ProcessingStats:
    """إحصائيات المعالجة"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_time: float = 0.0
    average_time_per_file: float = 0.0
    files_per_second: float = 0.0
    total_size_reduction: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

class ProgressReporter:
    """مراقب التقدم في الوقت الفعلي"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.stats = ProcessingStats()
        self.start_time = datetime.now()
        self.last_update = time.time()
        self.completed_files = deque(maxlen=100)  # آخر 100 ملف
        self.is_running = False
        
    def start(self):
        """بدء مراقبة التقدم"""
        self.is_running = True
        self.start_time = datetime.now()
        
    def stop(self):
        """إيقاف مراقبة التقدم"""
        self.is_running = False
        
    def update_file_completed(self, task: FileTask, processing_time: float):
        """تحديث عند اكتمال ملف"""
        self.stats.processed_files += 1
        self.completed_files.append(processing_time)
        
        # حساب الإحصائيات
        if self.completed_files:
            self.stats.average_time_per_file = sum(self.completed_files) / len(self.completed_files)
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        self.stats.total_time = elapsed_time
        
        if elapsed_time > 0:
            self.stats.files_per_second = self.stats.processed_files / elapsed_time
        
        # تحديث استخدام الذاكرة والمعالج
        process = psutil.Process()
        self.stats.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        self.stats.cpu_usage_percent = process.cpu_percent()
        
        # طباعة التقدم
        if time.time() - self.last_update >= self.update_interval:
            self._print_progress()
            self.last_update = time.time()
    
    def update_file_failed(self, task: FileTask, error: str):
        """تحديث عند فشل ملف"""
        self.stats.failed_files += 1
        
    def _print_progress(self):
        """طباعة تقرير التقدم"""
        completion_rate = (self.stats.processed_files / self.stats.total_files * 100) if self.stats.total_files > 0 else 0
        
        eta_seconds = 0
        if self.stats.files_per_second > 0 and self.stats.total_files > 0:
            remaining_files = self.stats.total_files - self.stats.processed_files - self.stats.failed_files
            eta_seconds = remaining_files / self.stats.files_per_second
        
        eta_str = str(timedelta(seconds=int(eta_seconds))) if eta_seconds > 0 else "غير معروف"
        
        logger.info("", 
                   component="PROGRESS",
                   extra={
                       "component": "PROGRESS",
                       "progress": f"{completion_rate:.1f}% ({self.stats.processed_files}/{self.stats.total_files})",
                       "speed": f"{self.stats.files_per_second:.2f} ملف/ثانية",
                       "eta": eta_str,
                       "memory": f"{self.stats.memory_usage_mb:.1f}MB",
                       "cpu": f"{self.stats.cpu_usage_percent:.1f}%"
                   })

class ResourceManager:
    """مدير الموارد والذاكرة"""
    
    def __init__(self, max_memory_mb: int = 4096, max_cpu_percent: float = 80.0):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.monitoring = False
        
    async def monitor_resources(self) -> bool:
        """مراقبة الموارد والتحكم في الاستخدام"""
        process = psutil.Process()
        
        # فحص الذاكرة
        memory_mb = process.memory_info().rss / 1024 / 1024
        if memory_mb > self.max_memory_mb:
            logger.warning("", component="RESOURCE", extra={"component": "RESOURCE"})
            logger.warning(f"⚠️ استخدام ذاكرة عالي: {memory_mb:.1f}MB")
            gc.collect()  # تنظيف الذاكرة
            await asyncio.sleep(0.1)
            return False
        
        # فحص المعالج
        cpu_percent = process.cpu_percent()
        if cpu_percent > self.max_cpu_percent:
            logger.warning("", component="RESOURCE", extra={"component": "RESOURCE"})
            logger.warning(f"⚠️ استخدام معالج عالي: {cpu_percent:.1f}%")
            await asyncio.sleep(0.2)
            return False
        
        return True

class FastFolderProcessor:
    """معالج المجلدات السريع"""
    
    def __init__(self, 
                 max_workers: int = None,
                 chunk_size: int = 100,
                 max_memory_mb: int = 4096,
                 progress_interval: float = 1.0):
        """
        تهيئة المعالج
        
        Args:
            max_workers: عدد العمليات المتوازية
            chunk_size: حجم الدفعة الواحدة
            max_memory_mb: أقصى استخدام للذاكرة
            progress_interval: فترة تحديث التقدم
        """
        self.max_workers = max_workers or min(16, mp.cpu_count() * 2)
        self.chunk_size = chunk_size
        self.resource_manager = ResourceManager(max_memory_mb)
        self.progress_reporter = ProgressReporter(progress_interval)
        
        # قوائم انتظار المهام
        self.task_queue: asyncio.Queue = None
        self.result_queue: asyncio.Queue = None
        
        # إحصائيات ومتغيرات الحالة
        self.is_running = False
        self.workers: List[asyncio.Task] = []
        self.processed_tasks: List[FileTask] = []
        
        # نظام إدارة الأخطاء
        self.error_log: List[Dict[str, Any]] = []
        self.retry_queue: List[FileTask] = []
        
        logger.info("", component="INIT", extra={"component": "INIT"})
        logger.info(f"🚀 تم تهيئة معالج المجلدات السريع مع {self.max_workers} عامل")

    async def process_folder_structure(self, 
                                     root_path: Union[str, Path], 
                                     output_path: Union[str, Path] = None,
                                     file_patterns: List[str] = None,
                                     recursive: bool = True,
                                     preserve_structure: bool = True) -> Dict[str, Any]:
        """
        معالجة هيكل مجلد كامل
        
        Args:
            root_path: المجلد الجذر
            output_path: مجلد الإخراج
            file_patterns: أنماط الملفات المراد معالجتها
            recursive: معالجة المجلدات الفرعية
            preserve_structure: الحفاظ على هيكل المجلدات
            
        Returns:
            Dict: تقرير شامل عن المعالجة
        """
        root_path = Path(root_path)
        output_path = Path(output_path) if output_path else root_path / "processed_fast"
        file_patterns = file_patterns or ["*.md", "*.txt", "*.json"]
        
        logger.info("", component="MAIN", extra={"component": "MAIN"})
        logger.info(f"📁 بدء معالجة المجلد: {root_path}")
        logger.info(f"📤 مجلد الإخراج: {output_path}")
        
        # إنشاء مجلد الإخراج
        output_path.mkdir(parents=True, exist_ok=True)
        
        start_time = datetime.now()
        
        try:
            # 1. اكتشاف الملفات
            files_to_process = await self._discover_files(root_path, file_patterns, recursive)
            total_files = len(files_to_process)
            
            if total_files == 0:
                logger.warning("", component="MAIN", extra={"component": "MAIN"})
                logger.warning("⚠️ لم يتم العثور على ملفات للمعالجة")
                return self._create_empty_report()
            
            logger.info("", component="MAIN", extra={"component": "MAIN"})
            logger.info(f"📊 تم اكتشاف {total_files} ملف للمعالجة")
            
            # 2. إنشاء المهام
            tasks = await self._create_file_tasks(files_to_process, root_path, output_path, preserve_structure)
            
            # 3. تهيئة نظام المعالجة
            self.task_queue = asyncio.Queue()
            self.result_queue = asyncio.Queue()
            
            # إضافة المهام إلى القائمة
            for task in tasks:
                await self.task_queue.put(task)
            
            # 4. بدء المعالجة
            self.progress_reporter.stats.total_files = total_files
            self.progress_reporter.start()
            
            results = await self._process_tasks_parallel()
            
            # 5. إنتاج التقرير النهائي
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            report = await self._generate_final_report(
                root_path, output_path, results, total_time, total_files
            )
            
            # حفظ التقرير
            await self._save_report(output_path, report)
            
            logger.success("", component="MAIN", extra={"component": "MAIN"})
            logger.success(f"🎉 اكتملت المعالجة في {total_time:.2f}s")
            logger.success(f"📊 معدل المعالجة: {total_files / total_time:.2f} ملف/ثانية")
            
            return report
            
        except Exception as e:
            logger.error("", component="ERROR", extra={"component": "ERROR"})
            logger.error(f"❌ فشل في معالجة المجلد: {e}")
            raise
        finally:
            self.progress_reporter.stop()

    async def _discover_files(self, root_path: Path, patterns: List[str], recursive: bool) -> List[Path]:
        """اكتشاف الملفات المراد معالجتها"""
        logger.info("", component="DISCOVER", extra={"component": "DISCOVER"})
        logger.info("🔍 بدء اكتشاف الملفات...")
        
        files = []
        
        for pattern in patterns:
            if recursive:
                found_files = list(root_path.rglob(pattern))
            else:
                found_files = list(root_path.glob(pattern))
            files.extend(found_files)
        
        # إزالة التكرارات وترتيب حسب الحجم (الملفات الصغيرة أولاً للتسريع)
        unique_files = list(set(files))
        unique_files.sort(key=lambda f: f.stat().st_size)
        
        logger.info("", component="DISCOVER", extra={"component": "DISCOVER"})
        logger.info(f"✅ تم اكتشاف {len(unique_files)} ملف")
        
        return unique_files

    async def _create_file_tasks(self, files: List[Path], root_path: Path, 
                               output_path: Path, preserve_structure: bool) -> List[FileTask]:
        """إنشاء مهام المعالجة"""
        logger.info("", component="TASKS", extra={"component": "TASKS"})
        logger.info("📋 إنشاء مهام المعالجة...")
        
        tasks = []
        
        for i, file_path in enumerate(files):
            # تحديد مسار الإخراج
            if preserve_structure:
                relative_path = file_path.relative_to(root_path)
                output_file_path = output_path / relative_path.parent / f"{relative_path.stem}_processed.md"
            else:
                output_file_path = output_path / f"{file_path.stem}_processed.md"
            
            # تقدير وقت المعالجة بناءً على حجم الملف
            file_size = file_path.stat().st_size
            estimated_time = min(file_size / 50000, 10.0)  # تقدير تقريبي
            
            task = FileTask(
                file_path=file_path,
                task_id=f"task_{i:06d}",
                priority=0,  # يمكن تحسينه لاحقاً
                estimated_time=estimated_time,
                result_path=output_file_path,
                metadata={'file_size': file_size, 'index': i}
            )
            
            tasks.append(task)
        
        logger.info("", component="TASKS", extra={"component": "TASKS"})
        logger.info(f"✅ تم إنشاء {len(tasks)} مهمة")
        
        return tasks

    async def _process_tasks_parallel(self) -> List[FileTask]:
        """معالجة المهام بشكل متوازي"""
        logger.info("", component="WORKER", extra={"component": "WORKER"})
        logger.info(f"⚡ بدء المعالجة المتوازية مع {self.max_workers} عامل")
        
        self.is_running = True
        
        # إنشاء العمال
        self.workers = []
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker_{i}"))
            self.workers.append(worker)
        
        # انتظار اكتمال جميع المهام
        await self.task_queue.join()
        
        # إيقاف العمال
        self.is_running = False
        for worker in self.workers:
            worker.cancel()
        
        # جمع النتائج
        results = []
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                results.append(result)
            except asyncio.QueueEmpty:
                break
        
        return results

    async def _worker(self, worker_name: str):
        """عامل معالجة المهام"""
        logger.debug("", component=worker_name.upper(), extra={"component": worker_name.upper()})
        logger.debug(f"🔧 بدء العامل: {worker_name}")
        
        processed_count = 0
        
        while self.is_running:
            try:
                # فحص الموارد
                if not await self.resource_manager.monitor_resources():
                    await asyncio.sleep(0.5)
                    continue
                
                # الحصول على مهمة
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # معالجة المهمة
                task.status = ProcessingStatus.PROCESSING
                task.start_time = datetime.now()
                
                try:
                    await self._process_single_task(task)
                    task.status = ProcessingStatus.COMPLETED
                    
                    processing_time = (datetime.now() - task.start_time).total_seconds()
                    self.progress_reporter.update_file_completed(task, processing_time)
                    
                    processed_count += 1
                    
                except Exception as e:
                    task.status = ProcessingStatus.FAILED
                    task.error_message = str(e)
                    self.progress_reporter.update_file_failed(task, str(e))
                    
                    logger.error("", component=worker_name.upper(), extra={"component": worker_name.upper()})
                    logger.error(f"❌ فشل معالجة {task.file_path.name}: {e}")
                
                finally:
                    task.end_time = datetime.now()
                    await self.result_queue.put(task)
                    self.task_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("", component=worker_name.upper(), extra={"component": worker_name.upper()})
                logger.error(f"❌ خطأ في العامل {worker_name}: {e}")
        
        logger.debug("", component=worker_name.upper(), extra={"component": worker_name.upper()})
        logger.debug(f"🏁 انتهى العامل {worker_name} (معالج: {processed_count} ملف)")

    async def _process_single_task(self, task: FileTask):
        """معالجة مهمة واحدة"""
        from enhanced_text_processing_system import AdvancedTextProcessor
        
        # إنشاء معالج نص
        processor = AdvancedTextProcessor(num_workers=1)
        
        # معالجة الملف
        result = await processor.process_file_async(task.file_path)
        
        # إنشاء مجلد الإخراج
        task.result_path.parent.mkdir(parents=True, exist_ok=True)
        
        # حفظ النتيجة
        async with aiofiles.open(task.result_path, 'w', encoding='utf-8') as f:
            await f.write(result.cleaned_text)
        
        # تحديث معلومات المهمة
        task.metadata.update({
            'original_length': len(result.original_text),
            'cleaned_length': len(result.cleaned_text),
            'reduction_percentage': result.metadata.get('reduction_percentage', 0),
            'content_type': result.content_type.value
        })

    async def _generate_final_report(self, root_path: Path, output_path: Path, 
                                   results: List[FileTask], total_time: float, 
                                   total_files: int) -> Dict[str, Any]:
        """إنتاج التقرير النهائي"""
        logger.info("", component="REPORT", extra={"component": "REPORT"})
        logger.info("📊 إنتاج التقرير النهائي...")
        
        # تصنيف النتائج
        completed_tasks = [t for t in results if t.status == ProcessingStatus.COMPLETED]
        failed_tasks = [t for t in results if t.status == ProcessingStatus.FAILED]
        
        # حساب الإحصائيات
        stats = {
            'total_files': total_files,
            'completed_files': len(completed_tasks),
            'failed_files': len(failed_tasks),
            'success_rate': (len(completed_tasks) / total_files * 100) if total_files > 0 else 0,
            'total_processing_time': total_time,
            'average_time_per_file': total_time / total_files if total_files > 0 else 0,
            'files_per_second': total_files / total_time if total_time > 0 else 0
        }
        
        # إحصائيات التحسين
        if completed_tasks:
            reductions = [t.metadata.get('reduction_percentage', 0) for t in completed_tasks if t.metadata]
            original_sizes = [t.metadata.get('original_length', 0) for t in completed_tasks if t.metadata]
            cleaned_sizes = [t.metadata.get('cleaned_length', 0) for t in completed_tasks if t.metadata]
            
            optimization_stats = {
                'average_reduction_percentage': statistics.mean(reductions) if reductions else 0,
                'median_reduction_percentage': statistics.median(reductions) if reductions else 0,
                'total_original_size': sum(original_sizes),
                'total_cleaned_size': sum(cleaned_sizes),
                'total_size_saved': sum(original_sizes) - sum(cleaned_sizes)
            }
        else:
            optimization_stats = {}
        
        # تحليل الأخطاء
        error_analysis = {}
        if failed_tasks:
            error_types = defaultdict(int)
            for task in failed_tasks:
                error_types[task.error_message or 'Unknown'] += 1
            error_analysis = dict(error_types)
        
        report = {
            'processing_summary': stats,
            'optimization_summary': optimization_stats,
            'error_analysis': error_analysis,
            'configuration': {
                'root_path': str(root_path),
                'output_path': str(output_path),
                'max_workers': self.max_workers,
                'chunk_size': self.chunk_size
            },
            'performance_metrics': {
                'peak_memory_mb': self.progress_reporter.stats.memory_usage_mb,
                'average_cpu_usage': self.progress_reporter.stats.cpu_usage_percent,
                'throughput_efficiency': (stats['files_per_second'] * stats['success_rate']) / 100
            },
            'file_details': [
                {
                    'file_path': str(task.file_path),
                    'status': task.status.value,
                    'processing_time': (task.end_time - task.start_time).total_seconds() if task.start_time and task.end_time else 0,
                    'metadata': task.metadata or {}
                } for task in results
            ]
        }
        
        return report

    async def _save_report(self, output_path: Path, report: Dict[str, Any]):
        """حفظ التقرير"""
        report_file = output_path / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        async with aiofiles.open(report_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        
        logger.info("", component="REPORT", extra={"component": "REPORT"})
        logger.info(f"💾 تم حفظ التقرير: {report_file}")

    def _create_empty_report(self) -> Dict[str, Any]:
        """إنشاء تقرير فارغ"""
        return {
            'processing_summary': {
                'total_files': 0,
                'completed_files': 0,
                'failed_files': 0,
                'success_rate': 0,
                'total_processing_time': 0,
                'average_time_per_file': 0,
                'files_per_second': 0
            },
            'optimization_summary': {},
            'error_analysis': {},
            'configuration': {},
            'performance_metrics': {},
            'file_details': []
        }

# دوال مساعدة سريعة

async def quick_process_folder(folder_path: str, output_path: str = None, 
                             max_workers: int = None) -> Dict[str, Any]:
    """معالجة سريعة لمجلد"""
    processor = FastFolderProcessor(max_workers=max_workers)
    return await processor.process_folder_structure(folder_path, output_path)

async def benchmark_processing_speed(test_folder: str, worker_counts: List[int] = None) -> Dict[str, Any]:
    """قياس سرعة المعالجة مع عدد مختلف من العمال"""
    worker_counts = worker_counts or [1, 2, 4, 8, 16]
    results = {}
    
    logger.info("", component="BENCHMARK", extra={"component": "BENCHMARK"})
    logger.info("🏁 بدء قياس الأداء...")
    
    for worker_count in worker_counts:
        logger.info("", component="BENCHMARK", extra={"component": "BENCHMARK"})
        logger.info(f"⚡ اختبار مع {worker_count} عامل...")
        
        start_time = time.time()
        processor = FastFolderProcessor(max_workers=worker_count)
        
        result = await processor.process_folder_structure(
            test_folder, 
            output_path=f"{test_folder}_benchmark_{worker_count}workers"
        )
        
        end_time = time.time()
        
        results[f"{worker_count}_workers"] = {
            'total_time': end_time - start_time,
            'files_per_second': result['processing_summary']['files_per_second'],
            'success_rate': result['processing_summary']['success_rate'],
            'memory_usage': result['performance_metrics']['peak_memory_mb']
        }
    
    # تحليل النتائج
    best_performance = max(results.values(), key=lambda x: x['files_per_second'])
    
    benchmark_report = {
        'test_folder': test_folder,
        'worker_performance': results,
        'best_configuration': best_performance,
        'recommendations': _generate_performance_recommendations(results)
    }
    
    return benchmark_report

def _generate_performance_recommendations(results: Dict[str, Any]) -> Dict[str, str]:
    """إنتاج توصيات الأداء"""
    recommendations = {}
    
    # العثور على أفضل إعداد
    best_speed = max(results.values(), key=lambda x: x['files_per_second'])
    best_config = [k for k, v in results.items() if v == best_speed][0]
    
    recommendations['optimal_workers'] = f"أفضل عدد عمال: {best_config}"
    
    # تحليل استخدام الذاكرة
    high_memory_configs = [k for k, v in results.items() if v['memory_usage'] > 2048]
    if high_memory_configs:
        recommendations['memory_warning'] = f"إعدادات تستخدم ذاكرة عالية: {', '.join(high_memory_configs)}"
    
    return recommendations

# نظام مراقبة في الوقت الفعلي
class RealTimeMonitor:
    """مراقب الأداء في الوقت الفعلي"""
    
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self.is_monitoring = False
        self.stats_history = deque(maxlen=100)
        
    async def start_monitoring(self, processor: FastFolderProcessor):
        """بدء المراقبة"""
        self.is_monitoring = True
        
        while self.is_monitoring:
            stats = {
                'timestamp': datetime.now(),
                'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                'cpu_percent': psutil.cpu_percent(),
                'processed_files': processor.progress_reporter.stats.processed_files,
                'files_per_second': processor.progress_reporter.stats.files_per_second
            }
            
            self.stats_history.append(stats)
            
            # طباعة الإحصائيات
            logger.info("", component="MONITOR", extra={"component": "MONITOR"})
            logger.info(f"📊 ذاكرة: {stats['memory_mb']:.1f}MB | معالج: {stats['cpu_percent']:.1f}% | سرعة: {stats['files_per_second']:.2f} ملف/ثانية")
            
            await asyncio.sleep(self.update_interval)
    
    def stop_monitoring(self):
        """إيقاف المراقبة"""
        self.is_monitoring = False
        
    def get_stats_summary(self) -> Dict[str, Any]:
        """الحصول على ملخص الإحصائيات"""
        if not self.stats_history:
            return {}
        
        memory_values = [s['memory_mb'] for s in self.stats_history]
        cpu_values = [s['cpu_percent'] for s in self.stats_history]
        speed_values = [s['files_per_second'] for s in self.stats_history if s['files_per_second'] > 0]
        
        return {
            'average_memory_mb': statistics.mean(memory_values),
            'peak_memory_mb': max(memory_values),
            'average_cpu_percent': statistics.mean(cpu_values),
            'peak_cpu_percent': max(cpu_values),
            'average_speed': statistics.mean(speed_values) if speed_values else 0,
            'peak_speed': max(speed_values) if speed_values else 0
        }

# اختبار النظام
async def test_fast_folder_processor():
    """اختبار نظام معالجة المجلدات السريع"""
    print("🚀 اختبار نظام معالجة المجلدات السريع")
    print("=" * 60)
    
    test_folder = "d:/ezz/compair/edu-compare-wizard/backend/uploads/landingai_results"
    
    if Path(test_folder).exists():
        # اختبار المعالجة العادية
        print("📁 اختبار معالجة مجلد...")
        result = await quick_process_folder(test_folder, max_workers=8)
        
        print(f"✅ تم معالجة {result['processing_summary']['completed_files']} ملف")
        print(f"⏱️ الوقت الإجمالي: {result['processing_summary']['total_processing_time']:.2f}s")
        print(f"🚀 السرعة: {result['processing_summary']['files_per_second']:.2f} ملف/ثانية")
        print(f"📊 معدل النجاح: {result['processing_summary']['success_rate']:.1f}%")
        
        # اختبار قياس الأداء
        print(f"\n🏁 اختبار قياس الأداء...")
        benchmark_result = await benchmark_processing_speed(test_folder, [2, 4, 8])
        print(f"🏆 أفضل إعداد: {benchmark_result['recommendations']['optimal_workers']}")
    
    else:
        print(f"❌ المجلد غير موجود: {test_folder}")

if __name__ == "__main__":
    # تشغيل الاختبار
    asyncio.run(test_fast_folder_processor())
