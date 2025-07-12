"""
يقوم هذا الملف بضبط إعدادات مكتبة agentic-doc عند بدء التشغيل
لتحسين الأداء وتقليل أوقات الانتظار.

This file configures the agentic-doc library settings on startup
to improve performance and reduce waiting times.
"""

from loguru import logger

try:
    import agentic_doc.config as adc
    
    # الإعدادات الجديدة (باستخدام snake_case الصحيح)
    NEW_SETTINGS = {
        "max_retries": 5,              # زيادة عدد المحاولات من 3 إلى 5
        "max_retry_wait_time": 20,     # مهلة الانتظار بين المحاولات (بالثواني)
        "retry_logging_style": "log_msg", # "log_msg" لرؤية الأخطاء، "none" للصمت
        "split_size": 2048,            # حجم الشرائح للصور الكبيرة
        "extraction_split_size": 2048, # حجم شرائح الاستخراج
        "max_workers": 6,              # عدد الـ workers المتوازية
        "http_timeout": 120,           # زيادة مهلة HTTP من 5 ثوانٍ إلى 120 ثانية
        "timeout": 120,                # مهلة بديلة في حال عدم دعم http_timeout
        "request_timeout": 120,        # مهلة بديلة أخرى في حال عدم دعم الخيارات السابقة
    }
    
    logger.info("⚙️ تطبيق إعدادات agentic-doc المحسّنة...")
    
    for key, value in NEW_SETTINGS.items():
        if hasattr(adc, key):
            setattr(adc, key, value)
            logger.info(f"  ✅ {key}: {getattr(adc, key)}")
        else:
            logger.warning(f"  ⚠️ لم يتم العثور على الإعداد: {key}")
            
    logger.info("✅ تم تطبيق إعدادات agentic-doc المحسّنة بنجاح.")

    # تطبيق إعدادات مكتبة requests إذا كانت مستخدمة
    try:
        import requests
        # زيادة مهلة الانتظار الافتراضية لمكتبة requests
        requests.adapters.DEFAULT_RETRIES = 5
        logger.info("  ✅ تم ضبط requests.adapters.DEFAULT_RETRIES: 5")
    except (ImportError, AttributeError) as e:
        logger.warning(f"  ⚠️ لم يتم العثور على مكتبة requests أو خطأ في الوصول: {e}")

except ImportError:
    logger.warning("⚠️ مكتبة agentic-doc غير مثبتة، تم تخطي تطبيق الإعدادات.")
except Exception as e:
    logger.error(f"❌ فشل في تطبيق إعدادات agentic-doc: {e}") 