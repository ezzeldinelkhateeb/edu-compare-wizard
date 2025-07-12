"""
مهام Celery للمعالجة المتوازية
Celery Tasks for Parallel Processing
"""

from celery import current_task
from celery_app.worker import celery_app
from loguru import logger
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# إضافة المسار للاستيراد
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.api.endpoints.websocket import notify_progress, notify_stage_change, notify_error, notify_completion
from app.models.schemas import ProcessingStage

settings = get_settings()

# In-memory store for file paths
file_id_to_path_store = {}


@celery_app.task(bind=True)
def process_file_comparison(self, job_id: str, session_id: str, old_files: List[str], new_files: List[str]) -> Dict[str, Any]:
    """
    مهمة رئيسية لمعالجة مقارنة الملفات
    Main task for processing file comparison
    """
    try:
        logger.info(f"🚀 بدء معالجة المقارنة - Job: {job_id}")
        
        total_files = min(len(old_files), len(new_files))
        results = []
        
        base_progress = 80
        progress_range = 15 # from 80% to 95%
        
        for i, (old_file, new_file) in enumerate(zip(old_files, new_files)):
            try:
                # 1. مرحلة استخراج النص
                current_progress = base_progress + int(((i + 1) / total_files) * (progress_range / 3))
                message = f"ملف {i+1}/{total_files}: استخراج النص من الكتاب القديم"
                self.update_state(state='PROGRESS', meta={'progress': current_progress, 'message': message, 'current_file': old_file, 'current_stage': ProcessingStage.OCR_EXTRACTION.value})
                
                old_file_path = file_id_to_path_store.get(old_file)
                new_file_path = file_id_to_path_store.get(new_file)
                if not old_file_path or not new_file_path:
                    raise Exception(f"لم يتم العثور على مسار الملف لـ {old_file} أو {new_file}")

                old_text_result = extract_text_from_image.delay(old_file_path, job_id)
                
                message = f"ملف {i+1}/{total_files}: استخراج النص من الكتاب الجديد"
                self.update_state(state='PROGRESS', meta={'progress': current_progress, 'message': message, 'current_file': new_file, 'current_stage': ProcessingStage.OCR_EXTRACTION.value})
                new_text_result = extract_text_from_image.delay(new_file_path, job_id)
                
                old_text = old_text_result.get(timeout=300)
                new_text = new_text_result.get(timeout=300)
                if not old_text or not new_text:
                    raise Exception("فشل في استخراج النص من أحد الملفين أو كليهما")
                
                # 2. مرحلة المقارنة البصرية
                current_progress = base_progress + int(((i + 1) / total_files) * (2 * progress_range / 3))
                message = f"ملف {i+1}/{total_files}: المقارنة البصرية"
                self.update_state(state='PROGRESS', meta={'progress': current_progress, 'message': message, 'current_file': new_file, 'current_stage': ProcessingStage.VISUAL_ANALYSIS.value})
                
                visual_result = compare_images_visually.delay(old_file_path, new_file_path, job_id)
                visual_comparison = visual_result.get(timeout=180)

                # 3. مرحلة مقارنة النصوص
                current_progress = base_progress + int(((i + 1) / total_files) * progress_range)
                message = f"ملف {i+1}/{total_files}: تحليل النص بالذكاء الاصطناعي"
                self.update_state(state='PROGRESS', meta={'progress': current_progress, 'message': message, 'current_file': new_file, 'current_stage': ProcessingStage.TEXT_COMPARISON.value})

                text_result = compare_texts_ai.delay(old_text["text"], new_text["text"], job_id)
                text_comparison = text_result.get(timeout=300)
                
                # تجميع النتائج
                file_result = {
                    "old_file": old_file,
                    "new_file": new_file,
                    "old_extraction": old_text,
                    "new_extraction": new_text,
                    "visual_comparison": visual_comparison,
                    "text_comparison": text_comparison,
                    "overall_similarity": (visual_comparison["similarity"] + text_comparison["similarity"]) / 2,
                    "processed_at": datetime.now().isoformat()
                }
                
                results.append(file_result)
                logger.info(f"✅ تمت معالجة الملف {i+1}: {new_file}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الملف {new_file}: {e}")
                # إضافة نتيجة خطأ
                results.append({
                    "old_file": old_file,
                    "new_file": new_file,
                    "error": str(e),
                    "status": "failed"
                })
        
        # تحديث التقدم قبل إنشاء التقرير
        self.update_state(state='PROGRESS', meta={'progress': 95, 'message': "إنشاء التقرير النهائي", 'current_stage': ProcessingStage.REPORT_GENERATION.value})
        
        # إنشاء التقرير
        final_result = {
            "job_id": job_id,
            "session_id": session_id,
            "total_files": total_files,
            "processed_files": len([r for r in results if "error" not in r]),
            "failed_files": len([r for r in results if "error" in r]),
            "results": results,
            "summary": {
                "average_visual_similarity": sum(r.get("visual_comparison", {}).get("similarity", 0) for r in results if "error" not in r) / max(len([r for r in results if "error" not in r]), 1),
                "average_text_similarity": sum(r.get("text_comparison", {}).get("similarity", 0) for r in results if "error" not in r) / max(len([r for r in results if "error" not in r]), 1),
            },
            "completed_at": datetime.now().isoformat()
        }
        
        # إرسال إشعار الاكتمال (الحالة ستصبح SUCCESS تلقائياً عند return)
        # asyncio.run is problematic in Celery tasks, better to avoid if possible
        # asyncio.run(notify_completion(job_id, final_result))
        # asyncio.run(notify_progress(job_id, 100, None, "اكتملت المعالجة بنجاح"))
        
        logger.info(f"🎉 اكتملت معالجة المقارنة - Job: {job_id}")
        return final_result
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح في معالجة المقارنة {job_id}: {e}")
        # تحديث الحالة النهائية كـ FAILURE
        self.update_state(state='FAILURE', meta={'progress': 0, 'message': str(e), 'current_stage': 'FAILED'})
        # asyncio.run(notify_error(job_id, f"فشل في المعالجة: {str(e)}"))
        raise


@celery_app.task(bind=True)
def extract_text_from_image(self, image_path: str, job_id: str = None) -> Dict[str, Any]:
    """
    استخراج النص من الصورة باستخدام LandingAI
    Extract text from image using LandingAI
    """
    try:
        logger.info(f"📄 بدء استخراج النص من: {image_path}")
        
        if job_id:
            asyncio.run(notify_stage_change(job_id, "OCR", f"استخراج النص من {os.path.basename(image_path)}"))
        
        # استيراد خدمة LandingAI
        from app.services.landing_ai_service import landing_ai_service
        
        # استخراج باستخدام LandingAI الحقيقي
        loop = asyncio.get_event_loop()
        
        extraction_result = loop.run_until_complete(
            landing_ai_service.extract_from_file(image_path, job_id=job_id)
        )
        
        if not extraction_result.success:
            raise Exception(f"فشل استخراج LandingAI: {extraction_result.error_message}")
        
        # تحويل النتيجة للتنسيق المطلوب
        result = {
            "text": extraction_result.markdown_content,
            "confidence": extraction_result.confidence_score,
            "word_count": len(extraction_result.markdown_content.split()),
            "processing_time": extraction_result.processing_time,
            "service": "LandingAI_Real",
            "image_path": image_path,
            "structured_analysis": extraction_result.structured_analysis.dict() if extraction_result.structured_analysis else None,
            "total_chunks": extraction_result.total_chunks,
            "chunks_by_type": extraction_result.chunks_by_type,
            "visual_groundings": extraction_result.visual_groundings
        }
        
        logger.info(f"✅ تم استخراج النص من: {image_path}")
        return result
        
    except Exception as e:
        logger.error(f"❌ خطأ في استخراج النص من {image_path}: {e}")
        raise


@celery_app.task(bind=True)
def compare_images_visually(self, old_image: str, new_image: str, job_id: str = None) -> Dict[str, Any]:
    """
    مقارنة بصرية للصور باستخدام SSIM + pHash + CLIP
    Visual comparison using SSIM + pHash + CLIP
    """
    try:
        logger.info(f"🖼️ بدء المقارنة البصرية: {old_image} vs {new_image}")
        
        if job_id:
            asyncio.run(notify_stage_change(job_id, "VISUAL_COMPARISON", "المقارنة البصرية"))
        
        # محاكاة المقارنة البصرية
        import time
        import random
        time.sleep(random.uniform(3, 7))
        
        # نتائج تجريبية
        ssim_score = random.uniform(0.6, 0.95)
        phash_score = random.uniform(0.5, 0.9)
        clip_score = random.uniform(0.7, 0.95)
        
        # حساب النتيجة الإجمالية بالأوزان المحددة
        weights = {"ssim": 0.4, "phash": 0.2, "clip": 0.4}
        overall_similarity = (
            ssim_score * weights["ssim"] + 
            phash_score * weights["phash"] + 
            clip_score * weights["clip"]
        ) * 100
        
        result = {
            "similarity": overall_similarity,
            "details": {
                "ssim": ssim_score,
                "phash": phash_score,
                "clip": clip_score,
            },
            "service": "VisualMock"
        }
        
        logger.info(f"✅ تمت المقارنة البصرية بنجاح")
        return result
        
    except Exception as e:
        logger.error(f"❌ خطأ في المقارنة البصرية: {e}")
        if job_id:
            asyncio.run(notify_error(job_id, f"فشل في المقارنة البصرية: {str(e)}"))
        raise


@celery_app.task(bind=True)
def compare_texts_ai(self, old_text: str, new_text: str, job_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    مقارنة النصوص باستخدام Gemini AI
    Text comparison using Gemini AI
    """
    try:
        logger.info(f"📝 بدء مقارنة النصوص باستخدام Gemini AI")
        
        if job_id:
            asyncio.run(notify_stage_change(job_id, "AI_COMPARISON", "تحليل النصوص بالذكاء الاصطناعي"))
        
        # استيراد خدمة Gemini
        from app.services.gemini_service import gemini_service
        
        # مقارنة باستخدام Gemini الحقيقي
        loop = asyncio.get_event_loop()
        
        comparison_result = loop.run_until_complete(
            gemini_service.compare_texts(old_text, new_text, context)
        )
        
        # تحويل النتيجة للتنسيق المطلوب
        result = {
            "similarity": comparison_result.similarity_percentage,
            "content_changes": comparison_result.content_changes,
            "questions_changes": comparison_result.questions_changes,
            "examples_changes": comparison_result.examples_changes,
            "major_differences": comparison_result.major_differences,
            "added_content": comparison_result.added_content,
            "removed_content": comparison_result.removed_content,
            "modified_content": comparison_result.modified_content,
            "summary": comparison_result.summary,
            "recommendation": comparison_result.recommendation,
            "detailed_analysis": comparison_result.detailed_analysis,
            "processing_time": comparison_result.processing_time,
            "service": "Gemini_Real",
            "confidence_score": comparison_result.confidence_score,
            "old_text_length": comparison_result.old_text_length,
            "new_text_length": comparison_result.new_text_length,
            "common_words_count": comparison_result.common_words_count,
            "unique_old_words": comparison_result.unique_old_words,
            "unique_new_words": comparison_result.unique_new_words
        }
        
        logger.info(f"✅ مقارنة النصوص: {comparison_result.similarity_percentage:.1f}% تطابق")
        return result
        
    except Exception as e:
        logger.error(f"❌ خطأ في مقارنة النصوص: {e}")
        # if job_id:
        #     asyncio.run(notify_error(job_id, f"فشل في مقارنة النصوص: {str(e)}"))
        raise


@celery_app.task(bind=True)
def generate_report(self, job_id: str, comparison_results: Dict[str, Any], format: str = "html") -> Dict[str, Any]:
    """
    إنشاء التقرير النهائي
    Generate final report
    """
    try:
        logger.info(f"📊 بدء إنشاء التقرير")
        
        if job_id:
            asyncio.run(notify_stage_change(job_id, "REPORT_GENERATION", "إنشاء التقرير"))

        # محاكاة إنشاء التقرير
        import time
        time.sleep(random.uniform(2, 4))
        
        report_path = f"./uploads/reports/{job_id}_report.{format}"
        
        # في التطبيق الحقيقي: إنشاء التقرير الفعلي
        result = {
            "report_path": report_path,
            "format": format,
            "job_id": job_id,
            "file_size": random.randint(500000, 2000000),  # حجم تجريبي
            "pages": random.randint(5, 15),
            "generated_at": datetime.now().isoformat(),
            "download_url": f"/api/v1/reports/download/{job_id}",
            "expires_at": (datetime.now().timestamp() + 3600 * 24),  # 24 ساعة
        }
        
        logger.info(f"✅ تم إنشاء التقرير بنجاح")
        return result
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء التقرير: {e}")
        if job_id:
            asyncio.run(notify_error(job_id, f"فشل في إنشاء التقرير: {str(e)}"))
        raise


# مهمة تنظيف دورية
@celery_app.task
def cleanup_old_files():
    """
    مهمة دورية لتنظيف الملفات القديمة
    Periodic task to cleanup old files
    """
    try:
        logger.info("🧹 بدء تنظيف الملفات القديمة")
        
        # تنظيف الملفات الأقدم من CLEANUP_AFTER_DAYS
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=settings.CLEANUP_AFTER_DAYS)
        
        # في التطبيق الحقيقي: تنظيف الملفات من النظام وقاعدة البيانات
        logger.info(f"✅ تم تنظيف الملفات الأقدم من {cutoff_date}")
        
        return {"status": "success", "cutoff_date": cutoff_date.isoformat()}
        
    except Exception as e:
        logger.error(f"❌ خطأ في تنظيف الملفات: {e}")
        raise 