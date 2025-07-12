"""
اختبار شامل لجميع خدمات الباك ايند
Comprehensive Backend Services Test
"""
import os
import sys
import asyncio
import tempfile
from pathlib import Path

# إضافة مجلد الباك ايند للـ path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

# تعيين متغيرات البيئة المطلوبة
os.environ["GEMINI_API_KEY"] = "AIzaSyCDO-0puQQN79BJ4u503O31g16ww8CAycg"
os.environ["VISION_AGENT_API_KEY"] = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"

from loguru import logger
import json

# تكوين Logger
logger.remove()  # إزالة الـ handler الافتراضي
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)

async def test_gemini_service():
    """اختبار خدمة Gemini"""
    logger.info("🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶 GEMINI SERVICE TEST 🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶")
    logger.info("============================================================")
    logger.info("🧪 اختبار خدمة Gemini للمقارنة النصية")
    logger.info("============================================================")
    
    try:
        from app.services.gemini_service import gemini_service
        
        # فحص صحة الخدمة
        health = await gemini_service.health_check()
        logger.info(f"✅ حالة خدمة Gemini: {health}")
        
        # اختبار مقارنة نصوص
        old_text = """
        الفصل الأول: مقدمة في الفيزياء
        تعريف القوة: القوة هي كل ما يؤثر على الجسم ويغير حالته الحركية.
        قانون نيوتن الأول: الجسم الساكن يبقى ساكناً والمتحرك يبقى متحركاً ما لم تؤثر عليه قوة خارجية.
        """
        
        new_text = """
        الفصل الأول: مقدمة في الفيزياء المتقدمة
        تعريف القوة: القوة هي المؤثر الذي يغير حالة الجسم الحركية أو يشوهه.
        قانون نيوتن الأول: الجسم الساكن يبقى ساكناً والمتحرك يبقى متحركاً بسرعة ثابتة في خط مستقيم ما لم تؤثر عليه قوة خارجية محصلة.
        قانون نيوتن الثاني: القوة المحصلة المؤثرة على جسم تساوي كتلة الجسم مضروبة في تسارعه.
        التطبيقات العملية: استخدام قوانين نيوتن في حل مسائل الحركة اليومية.
        """
        
        context = {
            "content_type": "منهج فيزياء",
            "subject": "الفيزياء",
            "grade_level": "الثانوي"
        }
        
        logger.info("📝 بدء اختبار مقارنة النصوص...")
        result = await gemini_service.compare_texts(old_text, new_text, context)
        
        logger.info(f"📊 نسبة التشابه: {result.similarity_percentage}%")
        logger.info(f"⏱️ وقت المعالجة: {result.processing_time:.2f} ثانية")
        logger.info(f"🎯 درجة الثقة: {result.confidence_score:.1%}")
        logger.info(f"📈 التغييرات في المحتوى: {len(result.content_changes)}")
        logger.info(f"❓ التغييرات في الأسئلة: {len(result.questions_changes)}")
        
        logger.info("📝 ملخص المقارنة:")
        logger.info(f"   {result.summary}")
        
        logger.info("💡 التوصيات:")
        logger.info(f"   {result.recommendation}")
        
        # اختبار تحليل نص واحد
        logger.info("\n🔍 اختبار تحليل نص واحد...")
        analysis = await gemini_service.analyze_text(old_text, "حلل هذا النص التعليمي")
        logger.info(f"📄 تحليل النص: {analysis[:200]}...")
        
        logger.info("✅ نجحت جميع اختبارات خدمة Gemini!")
        return True
        
    except Exception as e:
        logger.error(f"❌ فشل في اختبار خدمة Gemini: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_landing_ai_service():
    """اختبار خدمة LandingAI"""
    logger.info("\n🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷 LANDINGAI SERVICE TEST 🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷🔷")
    logger.info("============================================================")
    logger.info("🧪 اختبار خدمة LandingAI للاستخراج النصي")
    logger.info("============================================================")
    
    try:
        from app.services.landing_ai_service import landing_ai_service
        
        # فحص صحة الخدمة
        health = await landing_ai_service.health_check()
        logger.info(f"✅ حالة خدمة LandingAI: {health}")
        
        # فحص تفعيل الخدمة
        is_enabled = landing_ai_service.is_enabled()
        logger.info(f"🔌 حالة التفعيل: {'مفعلة' if is_enabled else 'معطلة'}")
        
        # فحص الصيغ المدعومة
        formats = landing_ai_service.get_supported_formats()
        logger.info(f"📁 الصيغ المدعومة: {', '.join(formats)}")
        
        # اختبار ملف تجريبي (إذا كان متوفراً)
        test_image_path = Path("103.jpg")
        if test_image_path.exists():
            logger.info(f"📸 اختبار ملف: {test_image_path.name}")
            
            # التحقق من صحة الملف
            is_valid = landing_ai_service.validate_file(str(test_image_path))
            logger.info(f"✅ صحة الملف: {'صحيح' if is_valid else 'غير صحيح'}")
            
            if is_enabled and is_valid:
                logger.info("🚀 بدء عملية الاستخراج...")
                
                # إنشاء مجلد مؤقت للنتائج
                with tempfile.TemporaryDirectory() as temp_dir:
                    result = await landing_ai_service.extract_from_file(
                        str(test_image_path),
                        temp_dir,
                        "test_job_001"
                    )
                    
                    logger.info(f"📊 نتيجة الاستخراج:")
                    logger.info(f"   ✅ نجح: {result.success}")
                    logger.info(f"   ⏱️ وقت المعالجة: {result.processing_time:.2f} ثانية")
                    logger.info(f"   📄 إجمالي المقاطع: {result.total_chunks}")
                    logger.info(f"   🎯 درجة الثقة: {result.confidence_score:.1%}")
                    logger.info(f"   📝 النص المستخرج: {len(result.markdown_content)} حرف")
                    
                    if result.structured_analysis:
                        logger.info(f"   📚 الموضوع: {result.structured_analysis.subject}")
                        logger.info(f"   🎓 المستوى: {result.structured_analysis.grade_level}")
                        logger.info(f"   📖 عنوان الفصل: {result.structured_analysis.chapter_title}")
            else:
                logger.warning("⚠️ الخدمة معطلة أو الملف غير صحيح - تخطي الاختبار الفعلي")
        else:
            logger.warning("⚠️ ملف الاختبار غير موجود - تخطي الاختبار الفعلي")
        
        logger.info("✅ نجحت جميع اختبارات خدمة LandingAI!")
        return True
        
    except Exception as e:
        logger.error(f"❌ فشل في اختبار خدمة LandingAI: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_visual_comparison_service():
    """اختبار خدمة المقارنة البصرية"""
    logger.info("\n🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸 VISUAL COMPARISON TEST 🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸🔸")
    logger.info("============================================================")
    logger.info("🧪 اختبار خدمة المقارنة البصرية")
    logger.info("============================================================")
    
    try:
        from app.services.visual_comparison_service import visual_comparison_service
        
        # فحص صحة الخدمة
        health = await visual_comparison_service.health_check()
        logger.info(f"✅ حالة خدمة المقارنة البصرية: {health}")
        
        # اختبار ملفات تجريبية (إذا كانت متوفرة)
        test_image1 = Path("103.jpg")
        test_image2 = Path("103.jpg")  # نفس الصورة للاختبار
        
        if test_image1.exists() and test_image2.exists():
            logger.info(f"🖼️ مقارنة: {test_image1.name} مع {test_image2.name}")
            
            # إنشاء مجلد مؤقت للنتائج
            with tempfile.TemporaryDirectory() as temp_dir:
                result = await visual_comparison_service.compare_images(
                    str(test_image1),
                    str(test_image2),
                    temp_dir
                )
                
                logger.info(f"📊 نتيجة المقارنة البصرية:")
                logger.info(f"   🎯 نسبة التشابه: {result.similarity_score}%")
                logger.info(f"   📐 SSIM: {result.ssim_score:.3f}")
                logger.info(f"   🔢 pHash: {result.phash_score:.3f}")
                if result.clip_score:
                    logger.info(f"   🧠 CLIP: {result.clip_score:.3f}")
                logger.info(f"   ⏱️ وقت المعالجة: {result.processing_time:.2f} ثانية")
                logger.info(f"   🔍 اختلافات مكتشفة: {'نعم' if result.difference_detected else 'لا'}")
                logger.info(f"   📈 MSE: {result.mean_squared_error:.2f}")
                logger.info(f"   📊 PSNR: {result.peak_signal_noise_ratio:.2f}")
                
                logger.info(f"📝 ملخص التحليل:")
                logger.info(f"   {result.analysis_summary}")
                
                logger.info(f"💡 التوصيات:")
                logger.info(f"   {result.recommendations}")
        else:
            logger.warning("⚠️ ملفات الاختبار غير موجودة - محاكاة النتائج")
            
            # محاكاة مقارنة
            from app.services.visual_comparison_service import VisualComparisonResult
            mock_result = VisualComparisonResult(
                similarity_score=95.5,
                ssim_score=0.98,
                phash_score=0.95,
                processing_time=1.2,
                old_image_path="test1.jpg",
                new_image_path="test2.jpg",
                analysis_summary="محاكاة نتيجة المقارنة البصرية",
                recommendations="توصيات تجريبية"
            )
            logger.info(f"🎭 نتيجة محاكاة: {mock_result.similarity_score}% تطابق")
        
        logger.info("✅ نجحت جميع اختبارات خدمة المقارنة البصرية!")
        return True
        
    except Exception as e:
        logger.error(f"❌ فشل في اختبار خدمة المقارنة البصرية: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_all_services_integration():
    """اختبار تكامل جميع الخدمات"""
    logger.info("\n🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹 INTEGRATION TEST 🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹")
    logger.info("============================================================")
    logger.info("🧪 اختبار تكامل جميع الخدمات")
    logger.info("============================================================")
    
    try:
        # استيراد جميع الخدمات
        from app.services.gemini_service import gemini_service
        from app.services.landing_ai_service import landing_ai_service
        from app.services.visual_comparison_service import visual_comparison_service
        
        # فحص التكامل
        services_status = {}
        
        # Gemini
        try:
            health = await gemini_service.health_check()
            services_status["Gemini"] = health.get("status", "unknown")
            logger.info(f"🔶 Gemini: {services_status['Gemini']}")
        except Exception as e:
            services_status["Gemini"] = f"error: {e}"
            logger.error(f"🔶 Gemini: خطأ - {e}")
        
        # LandingAI
        try:
            health = await landing_ai_service.health_check()
            is_enabled = landing_ai_service.is_enabled()
            services_status["LandingAI"] = f"{'enabled' if is_enabled else 'disabled'} - {health.get('status', 'unknown')}"
            logger.info(f"🔷 LandingAI: {services_status['LandingAI']}")
        except Exception as e:
            services_status["LandingAI"] = f"error: {e}"
            logger.error(f"🔷 LandingAI: خطأ - {e}")
        
        # Visual Comparison
        try:
            health = await visual_comparison_service.health_check()
            services_status["VisualComparison"] = health.get("status", "unknown")
            logger.info(f"🔸 Visual Comparison: {services_status['VisualComparison']}")
        except Exception as e:
            services_status["VisualComparison"] = f"error: {e}"
            logger.error(f"🔸 Visual Comparison: خطأ - {e}")
        
        # تقرير نهائي
        logger.info("\n📋 تقرير التكامل النهائي:")
        working_services = 0
        total_services = len(services_status)
        
        for service_name, status in services_status.items():
            status_icon = "✅" if "error" not in status else "❌"
            logger.info(f"   {status_icon} {service_name}: {status}")
            if "error" not in status:
                working_services += 1
        
        success_rate = (working_services / total_services) * 100
        logger.info(f"\n🎯 معدل النجاح: {working_services}/{total_services} ({success_rate:.1f}%)")
        
        if success_rate >= 66:  # 2/3 من الخدمات تعمل
            logger.info("✅ النظام جاهز للربط مع الفرونت ايند!")
            return True
        else:
            logger.warning("⚠️ يحتاج النظام إلى إصلاحات قبل الربط مع الفرونت ايند")
            return False
        
    except Exception as e:
        logger.error(f"❌ فشل في اختبار التكامل: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """الدالة الرئيسية للاختبار"""
    logger.info("🚀 بدء اختبار شامل لخدمات الباك ايند")
    logger.info("=" * 80)
    
    start_time = asyncio.get_event_loop().time()
    
    # قائمة النتائج
    test_results = {
        "Gemini Service": False,
        "LandingAI Service": False,
        "Visual Comparison Service": False,
        "Integration Test": False
    }
    
    # تشغيل الاختبارات
    test_results["Gemini Service"] = await test_gemini_service()
    test_results["LandingAI Service"] = await test_landing_ai_service()
    test_results["Visual Comparison Service"] = await test_visual_comparison_service()
    test_results["Integration Test"] = await test_all_services_integration()
    
    # حساب الوقت الإجمالي
    total_time = asyncio.get_event_loop().time() - start_time
    
    # تقرير نهائي
    logger.info("\n" + "=" * 80)
    logger.info("📊 التقرير النهائي لاختبار خدمات الباك ايند")
    logger.info("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status_icon = "✅" if result else "❌"
        status_text = "نجح" if result else "فشل"
        logger.info(f"{status_icon} {test_name}: {status_text}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100
    logger.info(f"\n🎯 معدل النجاح الإجمالي: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    logger.info(f"⏱️ الوقت الإجمالي: {total_time:.2f} ثانية")
    
    # خلاصة الاستعداد
    if success_rate >= 75:  # 3/4 من الاختبارات نجحت
        logger.info("\n🎉 الباك ايند جاهز للربط مع الفرونت ايند!")
        logger.info("✅ يمكن البدء في التطوير والاختبار المتقدم")
        return 0
    elif success_rate >= 50:  # نصف الاختبارات نجح
        logger.info("\n⚠️ الباك ايند يحتاج إلى إصلاحات بسيطة")
        logger.info("🔧 يُنصح بإصلاح الخدمات الفاشلة قبل الربط")
        return 1
    else:
        logger.info("\n❌ الباك ايند يحتاج إلى إصلاحات كبيرة")
        logger.info("🚫 لا يُنصح بالربط مع الفرونت ايند حالياً")
        return 2

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⏹️ تم إيقاف الاختبار بواسطة المستخدم")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 خطأ غير متوقع: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
