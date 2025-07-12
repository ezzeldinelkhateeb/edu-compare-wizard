"""
مهام Celery المحسنة للمعالجة المتوازية السريعة
Optimized Celery Tasks for Fast Parallel Processing
"""

from celery import group, chain, chord
from celery_app.worker import celery_app
from loguru import logger
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Tuple
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

# إضافة المسار للاستيراد
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.services.landing_ai_service import LandingAIService
from app.services.visual_comparison_service import EnhancedVisualComparisonService

settings = get_settings()

# إعدادات المعالجة المتوازية
MAX_WORKERS = 6  # عدد الـ workers المتوازية
BATCH_SIZE = 2   # عدد الصور لكل batch


@celery_app.task(bind=True)
def parallel_extract_text_batch(self, image_paths: List[str], job_id: str = None) -> List[Dict[str, Any]]:
    """
    استخراج النص من مجموعة صور بشكل متوازي
    Extract text from multiple images in parallel
    """
    try:
        logger.info(f"🚀 بدء استخراج النص المتوازي من {len(image_paths)} صورة")
        
        # إنشاء خدمة LandingAI
        landing_service = LandingAIService()
        
        results = []
        
        # استخدام ThreadPoolExecutor لمعالجة متوازية حقيقية
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # إرسال جميع المهام للـ executor
            future_to_path = {
                executor.submit(self._extract_single_text, landing_service, path, job_id): path 
                for path in image_paths
            }
            
            # جمع النتائج بنفس ترتيب الإدخال
            path_to_result = {}
            completed = 0
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                completed += 1
                
                try:
                    result = future.result()
                    path_to_result[path] = result
                    
                    # تحديث التقدم
                    progress = int((completed / len(image_paths)) * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'progress': progress,
                            'message': f'تم استخراج النص من {completed}/{len(image_paths)} صورة',
                            'current_file': os.path.basename(path)
                        }
                    )
                    
                    logger.info(f"✅ تم استخراج النص من: {os.path.basename(path)}")
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في استخراج النص من {path}: {e}")
                    path_to_result[path] = {
                        "success": False,
                        "error": str(e),
                        "text": "",
                        "confidence": 0,
                        "processing_time": 0,
                        "service": "LandingAI_Error"
                    }
            
            # ترتيب النتائج بنفس ترتيب الإدخال
            results = [path_to_result[path] for path in image_paths]
        
        logger.info(f"🎉 اكتمل استخراج النص المتوازي من {len(image_paths)} صورة")
        return results
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح في استخراج النص المتوازي: {e}")
        raise

    def _extract_single_text(self, landing_service: LandingAIService, image_path: str, job_id: str = None) -> Dict[str, Any]:
        """
        استخراج النص من صورة واحدة (يتم تشغيلها في thread منفصل)
        Extract text from a single image (runs in separate thread)
        """
        try:
            # تشغيل async function في thread pool
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                extraction_result = loop.run_until_complete(
                    landing_service.extract_from_file(image_path, job_id=job_id)
                )
                
                if not extraction_result.success:
                    raise Exception(f"فشل استخراج LandingAI: {extraction_result.error_message}")
                
                # تحويل النتيجة للتنسيق المطلوب
                result = {
                    "success": True,
                    "text": extraction_result.markdown_content,
                    "confidence": extraction_result.confidence_score,
                    "word_count": len(extraction_result.markdown_content.split()),
                    "processing_time": extraction_result.processing_time,
                    "service": "LandingAI_Parallel",
                    "image_path": image_path,
                    "structured_analysis": extraction_result.structured_analysis.dict() if extraction_result.structured_analysis else None,
                    "total_chunks": extraction_result.total_chunks,
                    "chunks_by_type": extraction_result.chunks_by_type
                }
                
                return result
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ خطأ في استخراج النص من {image_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "confidence": 0,
                "processing_time": 0,
                "service": "LandingAI_Error",
                "image_path": image_path
            }


@celery_app.task(bind=True)
def parallel_visual_comparison_batch(self, image_pairs: List[Tuple[str, str]], job_id: str = None) -> List[Dict[str, Any]]:
    """
    مقارنة بصرية متوازية لمجموعة أزواج من الصور
    Parallel visual comparison for multiple image pairs
    """
    try:
        logger.info(f"🖼️ بدء المقارنة البصرية المتوازية لـ {len(image_pairs)} زوج من الصور")
        
        # إنشاء خدمة المقارنة البصرية
        visual_service = EnhancedVisualComparisonService()
        
        results = []
        
        # استخدام ThreadPoolExecutor لمعالجة متوازية
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # إرسال جميع المهام للـ executor
            future_to_pair = {
                executor.submit(self._compare_single_pair, visual_service, old_path, new_path, job_id): (old_path, new_path)
                for old_path, new_path in image_pairs
            }
            
            # جمع النتائج
            pair_to_result = {}
            completed = 0
            
            for future in as_completed(future_to_pair):
                pair = future_to_pair[future]
                completed += 1
                
                try:
                    result = future.result()
                    pair_to_result[pair] = result
                    
                    # تحديث التقدم
                    progress = int((completed / len(image_pairs)) * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'progress': progress,
                            'message': f'تمت مقارنة {completed}/{len(image_pairs)} زوج من الصور',
                            'current_pair': f"{os.path.basename(pair[0])} vs {os.path.basename(pair[1])}"
                        }
                    )
                    
                    logger.info(f"✅ تمت المقارنة البصرية: {os.path.basename(pair[0])} vs {os.path.basename(pair[1])}")
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في المقارنة البصرية {pair}: {e}")
                    pair_to_result[pair] = {
                        "success": False,
                        "error": str(e),
                        "similarity": 0,
                        "processing_time": 0
                    }
            
            # ترتيب النتائج بنفس ترتيب الإدخال
            results = [pair_to_result[pair] for pair in image_pairs]
        
        logger.info(f"🎉 اكتملت المقارنة البصرية المتوازية لـ {len(image_pairs)} زوج")
        return results
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح في المقارنة البصرية المتوازية: {e}")
        raise

    def _compare_single_pair(self, visual_service: EnhancedVisualComparisonService, old_path: str, new_path: str, job_id: str = None) -> Dict[str, Any]:
        """
        مقارنة بصرية لزوج واحد من الصور (يتم تشغيلها في thread منفصل)
        Visual comparison for a single image pair (runs in separate thread)
        """
        try:
            # تشغيل async function في thread pool
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                comparison_result = loop.run_until_complete(
                    visual_service.compare_images(old_path, new_path)
                )
                
                if not comparison_result.get("success", False):
                    raise Exception(f"فشل في المقارنة البصرية: {comparison_result.get('error', 'خطأ غير محدد')}")
                
                return {
                    "success": True,
                    "similarity": comparison_result.get("similarity", 0),
                    "ssim_score": comparison_result.get("ssim_score", 0),
                    "phash_similarity": comparison_result.get("phash_similarity", 0),
                    "processing_time": comparison_result.get("processing_time", 0),
                    "changed_regions": comparison_result.get("changed_regions", []),
                    "old_image_path": old_path,
                    "new_image_path": new_path
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ خطأ في المقارنة البصرية {old_path} vs {new_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "similarity": 0,
                "processing_time": 0,
                "old_image_path": old_path,
                "new_image_path": new_path
            }


@celery_app.task(bind=True)
def parallel_gemini_analysis_batch(self, text_pairs: List[Tuple[str, str]], job_id: str = None) -> List[Dict[str, Any]]:
    """
    تحليل متوازي بـ Gemini لمجموعة أزواج من النصوص
    Parallel Gemini analysis for multiple text pairs
    """
    try:
        logger.info(f"🤖 بدء التحليل المتوازي بـ Gemini لـ {len(text_pairs)} زوج من النصوص")
        
        results = []
        
        # استخدام ThreadPoolExecutor مع عدد محدود من الـ workers لتجنب rate limiting
        max_gemini_workers = min(3, MAX_WORKERS)  # حد أقصى 3 workers لـ Gemini
        
        with ThreadPoolExecutor(max_workers=max_gemini_workers) as executor:
            # إرسال جميع المهام للـ executor
            future_to_pair = {
                executor.submit(self._analyze_single_text_pair, old_text, new_text, job_id): (old_text, new_text)
                for old_text, new_text in text_pairs
            }
            
            # جمع النتائج
            pair_to_result = {}
            completed = 0
            
            for future in as_completed(future_to_pair):
                pair = future_to_pair[future]
                completed += 1
                
                try:
                    result = future.result()
                    pair_to_result[pair] = result
                    
                    # تحديث التقدم
                    progress = int((completed / len(text_pairs)) * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'progress': progress,
                            'message': f'تم تحليل {completed}/{len(text_pairs)} زوج من النصوص بـ Gemini',
                            'current_analysis': f'نص {completed}'
                        }
                    )
                    
                    logger.info(f"✅ تم التحليل بـ Gemini للزوج {completed}")
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في تحليل Gemini للزوج {completed}: {e}")
                    pair_to_result[pair] = {
                        "success": False,
                        "error": str(e),
                        "similarity_percentage": 0,
                        "processing_time": 0
                    }
            
            # ترتيب النتائج بنفس ترتيب الإدخال
            results = [pair_to_result[pair] for pair in text_pairs]
        
        logger.info(f"🎉 اكتمل التحليل المتوازي بـ Gemini لـ {len(text_pairs)} زوج")
        return results
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح في التحليل المتوازي بـ Gemini: {e}")
        raise

    def _analyze_single_text_pair(self, old_text: str, new_text: str, job_id: str = None) -> Dict[str, Any]:
        """
        تحليل Gemini لزوج واحد من النصوص (يتم تشغيلها في thread منفصل)
        Gemini analysis for a single text pair (runs in separate thread)
        """
        try:
            # تشغيل async function في thread pool
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # استيراد خدمة Gemini
                from app.services.gemini_service import gemini_service
                
                analysis_result = loop.run_until_complete(
                    gemini_service.compare_educational_content(old_text, new_text)
                )
                
                if not analysis_result.get("success", False):
                    raise Exception(f"فشل في تحليل Gemini: {analysis_result.get('error', 'خطأ غير محدد')}")
                
                return {
                    "success": True,
                    "similarity_percentage": analysis_result.get("similarity_percentage", 0),
                    "content_changes": analysis_result.get("content_changes", []),
                    "summary": analysis_result.get("summary", ""),
                    "processing_time": analysis_result.get("processing_time", 0),
                    "detailed_analysis": analysis_result.get("detailed_analysis", {}),
                    "old_text_length": len(old_text),
                    "new_text_length": len(new_text)
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحليل Gemini: {e}")
            return {
                "success": False,
                "error": str(e),
                "similarity_percentage": 0,
                "processing_time": 0,
                "old_text_length": len(old_text),
                "new_text_length": len(new_text)
            }


@celery_app.task(bind=True)
def ultra_fast_comparison_workflow(self, session_id: str, old_image_paths: List[str], new_image_paths: List[str]) -> Dict[str, Any]:
    """
    سير عمل المقارنة السريع جداً مع معالجة متوازية كاملة
    Ultra-fast comparison workflow with full parallel processing
    """
    try:
        logger.info(f"⚡ بدء سير العمل السريع للمقارنة - الجلسة: {session_id}")
        start_time = datetime.now()
        
        total_pairs = min(len(old_image_paths), len(new_image_paths))
        
        # تحديث الحالة الأولية
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 5,
                'message': 'إعداد المعالجة المتوازية...',
                'total_pairs': total_pairs,
                'stage': 'initialization'
            }
        )
        
        # المرحلة 1: استخراج النص من جميع الصور بشكل متوازي
        logger.info("📝 المرحلة 1: استخراج النص المتوازي...")
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 10,
                'message': 'بدء استخراج النص من جميع الصور...',
                'stage': 'text_extraction'
            }
        )
        
        # استخراج النص من جميع الصور في نفس الوقت
        all_image_paths = old_image_paths + new_image_paths
        
        # تقسيم إلى batches لتجنب overload
        batches = [all_image_paths[i:i + BATCH_SIZE * 2] for i in range(0, len(all_image_paths), BATCH_SIZE * 2)]
        
        all_extraction_results = []
        for i, batch in enumerate(batches):
            batch_results = parallel_extract_text_batch.delay(batch, session_id).get(timeout=600)
            all_extraction_results.extend(batch_results)
            
            # تحديث التقدم
            progress = 10 + int(((i + 1) / len(batches)) * 30)
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'message': f'تم استخراج النص من batch {i+1}/{len(batches)}',
                    'stage': 'text_extraction'
                }
            )
        
        # تقسيم النتائج إلى old و new
        old_extraction_results = all_extraction_results[:len(old_image_paths)]
        new_extraction_results = all_extraction_results[len(old_image_paths):]
        
        # المرحلة 2: المقارنة البصرية المتوازية
        logger.info("🖼️ المرحلة 2: المقارنة البصرية المتوازية...")
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 45,
                'message': 'بدء المقارنة البصرية المتوازية...',
                'stage': 'visual_comparison'
            }
        )
        
        # إنشاء أزواج الصور للمقارنة
        image_pairs = list(zip(old_image_paths, new_image_paths))
        
        # تقسيم إلى batches
        visual_batches = [image_pairs[i:i + BATCH_SIZE] for i in range(0, len(image_pairs), BATCH_SIZE)]
        
        all_visual_results = []
        for i, batch in enumerate(visual_batches):
            batch_results = parallel_visual_comparison_batch.delay(batch, session_id).get(timeout=400)
            all_visual_results.extend(batch_results)
            
            # تحديث التقدم
            progress = 45 + int(((i + 1) / len(visual_batches)) * 25)
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'message': f'تمت المقارنة البصرية لـ batch {i+1}/{len(visual_batches)}',
                    'stage': 'visual_comparison'
                }
            )
        
        # المرحلة 3: تحليل Gemini المتوازي
        logger.info("🤖 المرحلة 3: تحليل Gemini المتوازي...")
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 75,
                'message': 'بدء تحليل Gemini المتوازي...',
                'stage': 'gemini_analysis'
            }
        )
        
        # إنشاء أزواج النصوص للتحليل
        text_pairs = []
        for old_result, new_result in zip(old_extraction_results, new_extraction_results):
            if old_result.get("success") and new_result.get("success"):
                text_pairs.append((old_result["text"], new_result["text"]))
            else:
                # إضافة زوج فارغ في حالة فشل الاستخراج
                text_pairs.append(("", ""))
        
        # تقسيم إلى batches
        gemini_batches = [text_pairs[i:i + BATCH_SIZE] for i in range(0, len(text_pairs), BATCH_SIZE)]
        
        all_gemini_results = []
        for i, batch in enumerate(gemini_batches):
            batch_results = parallel_gemini_analysis_batch.delay(batch, session_id).get(timeout=500)
            all_gemini_results.extend(batch_results)
            
            # تحديث التقدم
            progress = 75 + int(((i + 1) / len(gemini_batches)) * 15)
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'message': f'تم تحليل Gemini لـ batch {i+1}/{len(gemini_batches)}',
                    'stage': 'gemini_analysis'
                }
            )
        
        # المرحلة 4: تجميع النتائج النهائية
        logger.info("📊 المرحلة 4: تجميع النتائج النهائية...")
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 95,
                'message': 'تجميع النتائج النهائية...',
                'stage': 'results_compilation'
            }
        )
        
        # تجميع جميع النتائج
        final_results = []
        for i in range(total_pairs):
            pair_result = {
                "pair_index": i,
                "old_image_path": old_image_paths[i],
                "new_image_path": new_image_paths[i],
                "old_text_extraction": old_extraction_results[i],
                "new_text_extraction": new_extraction_results[i],
                "visual_comparison": all_visual_results[i],
                "gemini_analysis": all_gemini_results[i],
                "overall_similarity": self._calculate_overall_similarity(
                    all_visual_results[i], all_gemini_results[i]
                ),
                "processed_at": datetime.now().isoformat()
            }
            final_results.append(pair_result)
        
        # حساب الإحصائيات الإجمالية
        end_time = datetime.now()
        total_processing_time = (end_time - start_time).total_seconds()
        
        successful_pairs = len([r for r in final_results if 
                              r["old_text_extraction"].get("success") and 
                              r["new_text_extraction"].get("success") and
                              r["visual_comparison"].get("success") and
                              r["gemini_analysis"].get("success")])
        
        summary = {
            "session_id": session_id,
            "total_pairs": total_pairs,
            "successful_pairs": successful_pairs,
            "failed_pairs": total_pairs - successful_pairs,
            "success_rate": (successful_pairs / total_pairs) * 100 if total_pairs > 0 else 0,
            "total_processing_time": total_processing_time,
            "average_time_per_pair": total_processing_time / total_pairs if total_pairs > 0 else 0,
            "parallel_efficiency": self._calculate_parallel_efficiency(final_results, total_processing_time),
            "average_visual_similarity": sum(r["visual_comparison"].get("similarity", 0) for r in final_results) / total_pairs if total_pairs > 0 else 0,
            "average_text_similarity": sum(r["gemini_analysis"].get("similarity_percentage", 0) for r in final_results) / total_pairs if total_pairs > 0 else 0,
            "completed_at": end_time.isoformat()
        }
        
        final_response = {
            "summary": summary,
            "results": final_results,
            "processing_stats": {
                "text_extraction_time": sum(r["old_text_extraction"].get("processing_time", 0) + r["new_text_extraction"].get("processing_time", 0) for r in final_results),
                "visual_comparison_time": sum(r["visual_comparison"].get("processing_time", 0) for r in final_results),
                "gemini_analysis_time": sum(r["gemini_analysis"].get("processing_time", 0) for r in final_results),
                "total_parallel_time": total_processing_time
            }
        }
        
        logger.info(f"🎉 اكتمل سير العمل السريع! {total_pairs} أزواج في {total_processing_time:.2f} ثانية")
        logger.info(f"📈 معدل النجاح: {summary['success_rate']:.1f}%")
        logger.info(f"⚡ كفاءة المعالجة المتوازية: {summary['parallel_efficiency']:.1f}%")
        
        return final_response
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح في سير العمل السريع: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'progress': 0,
                'message': f'فشل في سير العمل: {str(e)}',
                'stage': 'failed'
            }
        )
        raise

    def _calculate_overall_similarity(self, visual_result: Dict[str, Any], gemini_result: Dict[str, Any]) -> float:
        """حساب درجة التشابه الإجمالية"""
        visual_sim = visual_result.get("similarity", 0) if visual_result.get("success") else 0
        text_sim = gemini_result.get("similarity_percentage", 0) / 100 if gemini_result.get("success") else 0
        
        # وزن أكبر للنص (70%) مقارنة بالصورة (30%)
        return (visual_sim * 0.3) + (text_sim * 0.7)

    def _calculate_parallel_efficiency(self, results: List[Dict[str, Any]], total_time: float) -> float:
        """حساب كفاءة المعالجة المتوازية"""
        # حساب الوقت الذي كان سيستغرقه لو تم تشغيله بشكل تسلسلي
        sequential_time = 0
        for result in results:
            sequential_time += result["old_text_extraction"].get("processing_time", 0)
            sequential_time += result["new_text_extraction"].get("processing_time", 0)
            sequential_time += result["visual_comparison"].get("processing_time", 0)
            sequential_time += result["gemini_analysis"].get("processing_time", 0)
        
        if total_time == 0:
            return 0
        
        # كفاءة المعالجة المتوازية = (الوقت التسلسلي / الوقت المتوازي) * 100
        efficiency = (sequential_time / total_time) * 100
        return min(efficiency, 100)  # حد أقصى 100%


@celery_app.task(bind=True)
def quick_dual_comparison(self, session_id: str, old_image_path: str, new_image_path: str) -> Dict[str, Any]:
    """
    مقارنة سريعة لصورتين مع معالجة متوازية كاملة
    Quick comparison of two images with full parallel processing
    """
    try:
        logger.info(f"⚡ بدء المقارنة السريعة للصورتين - الجلسة: {session_id}")
        start_time = datetime.now()
        
        # تحديث الحالة الأولية
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 5,
                'message': 'إعداد المقارنة السريعة...',
                'stage': 'initialization'
            }
        )
        
        # تشغيل جميع المهام بشكل متوازي
        with ThreadPoolExecutor(max_workers=4) as executor:
            # إرسال جميع المهام في نفس الوقت
            future_old_text = executor.submit(self._extract_text_worker, old_image_path, session_id)
            future_new_text = executor.submit(self._extract_text_worker, new_image_path, session_id)
            future_visual = executor.submit(self._compare_visual_worker, old_image_path, new_image_path, session_id)
            
            # تحديث التقدم
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': 20,
                    'message': 'تشغيل استخراج النص والمقارنة البصرية...',
                    'stage': 'parallel_extraction'
                }
            )
            
            # انتظار النتائج
            old_extraction = future_old_text.result()
            new_extraction = future_new_text.result()
            visual_comparison = future_visual.result()
            
            # تحديث التقدم
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': 70,
                    'message': 'تحليل النصوص بـ Gemini...',
                    'stage': 'gemini_analysis'
                }
            )
            
            # تحليل Gemini للنصوص
            gemini_result = {"success": False, "similarity_percentage": 0, "error": "لم يتم التحليل"}
            if old_extraction.get("success") and new_extraction.get("success"):
                future_gemini = executor.submit(
                    self._analyze_gemini_worker, 
                    old_extraction["text"], 
                    new_extraction["text"], 
                    session_id
                )
                gemini_result = future_gemini.result()
        
        # تجميع النتائج النهائية
        end_time = datetime.now()
        total_processing_time = (end_time - start_time).total_seconds()
        
        overall_similarity = self._calculate_overall_similarity(visual_comparison, gemini_result)
        
        final_result = {
            "session_id": session_id,
            "old_image_path": old_image_path,
            "new_image_path": new_image_path,
            "old_text_extraction": old_extraction,
            "new_text_extraction": new_extraction,
            "visual_comparison": visual_comparison,
            "gemini_analysis": gemini_result,
            "overall_similarity": overall_similarity,
            "total_processing_time": total_processing_time,
            "parallel_efficiency": self._calculate_efficiency(
                old_extraction, new_extraction, visual_comparison, gemini_result, total_processing_time
            ),
            "success": all([
                old_extraction.get("success", False),
                new_extraction.get("success", False),
                visual_comparison.get("success", False),
                gemini_result.get("success", False)
            ]),
            "completed_at": end_time.isoformat()
        }
        
        logger.info(f"🎉 اكتملت المقارنة السريعة في {total_processing_time:.2f} ثانية")
        logger.info(f"📊 التشابه الإجمالي: {overall_similarity:.1%}")
        
        return final_result
        
    except Exception as e:
        logger.error(f"❌ خطأ في المقارنة السريعة: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'progress': 0,
                'message': f'فشل في المقارنة: {str(e)}',
                'stage': 'failed'
            }
        )
        raise

    def _extract_text_worker(self, image_path: str, session_id: str) -> Dict[str, Any]:
        """Worker لاستخراج النص"""
        try:
            from app.services.landing_ai_service import LandingAIService
            landing_service = LandingAIService()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    landing_service.extract_from_file(image_path, job_id=session_id)
                )
                
                return {
                    "success": result.success,
                    "text": result.markdown_content,
                    "confidence": result.confidence_score,
                    "word_count": len(result.markdown_content.split()),
                    "processing_time": result.processing_time,
                    "service": "LandingAI_Parallel",
                    "image_path": image_path
                }
            finally:
                loop.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "confidence": 0,
                "processing_time": 0,
                "service": "LandingAI_Error"
            }

    def _compare_visual_worker(self, old_path: str, new_path: str, session_id: str) -> Dict[str, Any]:
        """Worker للمقارنة البصرية"""
        try:
            from app.services.visual_comparison_service import EnhancedVisualComparisonService
            visual_service = EnhancedVisualComparisonService()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    visual_service.compare_images(old_path, new_path)
                )
                
                return {
                    "success": result.get("success", False),
                    "similarity": result.get("similarity", 0),
                    "ssim_score": result.get("ssim_score", 0),
                    "processing_time": result.get("processing_time", 0),
                    "changed_regions": result.get("changed_regions", [])
                }
            finally:
                loop.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "similarity": 0,
                "processing_time": 0
            }

    def _analyze_gemini_worker(self, old_text: str, new_text: str, session_id: str) -> Dict[str, Any]:
        """Worker لتحليل Gemini"""
        try:
            from app.services.gemini_service import gemini_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    gemini_service.compare_educational_content(old_text, new_text)
                )
                
                return {
                    "success": result.get("success", False),
                    "similarity_percentage": result.get("similarity_percentage", 0),
                    "content_changes": result.get("content_changes", []),
                    "summary": result.get("summary", ""),
                    "processing_time": result.get("processing_time", 0)
                }
            finally:
                loop.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "similarity_percentage": 0,
                "processing_time": 0
            }

    def _calculate_efficiency(self, old_extraction: Dict, new_extraction: Dict, 
                            visual_comparison: Dict, gemini_result: Dict, 
                            total_time: float) -> float:
        """حساب كفاءة المعالجة المتوازية"""
        sequential_time = (
            old_extraction.get("processing_time", 0) +
            new_extraction.get("processing_time", 0) +
            visual_comparison.get("processing_time", 0) +
            gemini_result.get("processing_time", 0)
        )
        
        if total_time == 0:
            return 0
        
        return min((sequential_time / total_time) * 100, 100) 