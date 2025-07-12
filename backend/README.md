# نظام مقارنة المناهج التعليمية - Backend
# Educational Content Comparison System - Backend

نظام ذكي لمقارنة المناهج التعليمية باستخدام الذكاء الاصطناعي المتقدم.

## 🚀 الميزات الرئيسية

### ✅ خدمات الذكاء الاصطناعي المتكاملة
- **LandingAI Agentic Document Extraction**: استخراج ذكي للمحتوى من المستندات المعقدة
- **Google Gemini AI**: تحليل ومقارنة النصوص بدقة عالية
- **Visual Comparison**: مقارنة بصرية باستخدام SSIM + pHash + CLIP

### ✅ البنية التقنية
- **FastAPI**: API سريع وحديث مع توثيق تلقائي
- **Celery + Redis**: معالجة متوازية وغير متزامنة
- **WebSocket**: تحديثات مباشرة للمستخدمين
- **Docker**: نشر مبسط ومحمول

### ✅ إمكانيات المعالجة
- دعم PDF وجميع صيغ الصور
- معالجة متوازية للملفات الكبيرة
- استخراج منظم للبيانات التعليمية
- Visual Groundings للعناصر المستخرجة
- تقارير شاملة بصيغ متعددة

## 📋 متطلبات النظام

### البرمجيات المطلوبة
```bash
Python 3.9+
Redis Server
Docker (اختياري)
```

### مفاتيح API المطلوبة
```bash
# LandingAI
VISION_AGENT_API_KEY=your-landing-ai-key

# Google Gemini
GEMINI_API_KEY=your-gemini-key

# Redis (محلي أو سحابي)
REDIS_URL=redis://localhost:6379/0
```

## 🛠️ التثبيت والإعداد

### 1. تحضير البيئة
```bash
# استنساخ المشروع
git clone <repository-url>
cd edu-compare-wizard/backend

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate     # Windows

# تثبيت التبعيات
pip install -r requirements.txt
```

### 2. إعداد متغيرات البيئة
```bash
# نسخ قالب البيئة
cp .env.template .env

# تحرير الملف وإضافة مفاتيحك
nano .env
```

**المفاتيح الأساسية المطلوبة:**
```bash
# LandingAI - احصل عليه من https://landing.ai
VISION_AGENT_API_KEY=your-landing-ai-vision-agent-key

# Google Gemini - احصل عليه من https://ai.google.dev
GEMINI_API_KEY=your-google-gemini-api-key

# Redis (استخدم المحلي أو سحابي)
REDIS_URL=redis://localhost:6379/0
```

### 3. تشغيل Redis
```bash
# تثبيت Redis محلياً
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# استخدم Docker أو WSL

# تشغيل Redis
redis-server
```

### 4. تشغيل النظام

#### الطريقة السريعة (مطور واحد)
```bash
# تشغيل كل شيء بأمر واحد
python run.py
```

#### الطريقة المفصلة (للتطوير المتقدم)
```bash
# Terminal 1: FastAPI Server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Celery Worker
celery -A celery_app.worker worker --loglevel=info

# Terminal 3: Celery Flower (مراقبة)
celery -A celery_app.worker flower --port=5555
```

#### استخدام Docker
```bash
# تشغيل كامل باستخدام Docker Compose
docker-compose up -d

# مراقبة اللوجز
docker-compose logs -f
```

## 🔧 الاستخدام والاختبار

### 1. فحص صحة النظام
```bash
# فحص سريع
curl http://localhost:8000/api/v1/health

# فحص مفصل لجميع الخدمات
curl http://localhost:8000/api/v1/health/detailed

# فحص خدمات الذكاء الاصطناعي
curl http://localhost:8000/api/v1/health/ai-services
```

### 2. رفع الملفات
```bash
# رفع ملف PDF
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@curriculum.pdf" \
  -F "category=old"
```

### 3. بدء المقارنة
```bash
# بدء مقارنة جديدة
curl -X POST "http://localhost:8000/api/v1/compare/start" \
  -H "Content-Type: application/json" \
  -d '{
    "old_files": ["file1.pdf"],
    "new_files": ["file2.pdf"],
    "comparison_settings": {
      "enable_visual_comparison": true,
      "enable_text_comparison": true,
      "ai_analysis_depth": "detailed"
    }
  }'
```

### 4. مراقبة التقدم
```bash
# الحصول على حالة المهمة
curl http://localhost:8000/api/v1/compare/status/JOB_ID

# WebSocket للتحديثات المباشرة
# اتصل بـ ws://localhost:8000/api/v1/ws/JOB_ID
```

## 📊 واجهات API

### 🔍 Health Check Endpoints
- `GET /api/v1/health` - فحص سريع
- `GET /api/v1/health/detailed` - فحص شامل
- `GET /api/v1/health/ai-services` - فحص خدمات AI

### 📁 File Upload Endpoints
- `POST /api/v1/upload` - رفع ملفات
- `GET /api/v1/upload/sessions` - قائمة الجلسات
- `DELETE /api/v1/upload/session/{session_id}` - حذف جلسة

### ⚖️ Comparison Endpoints
- `POST /api/v1/compare/start` - بدء مقارنة
- `GET /api/v1/compare/status/{job_id}` - حالة المهمة
- `GET /api/v1/compare/result/{job_id}` - النتائج
- `GET /api/v1/compare/jobs` - قائمة المهام

### 🔌 WebSocket Endpoints
- `WS /api/v1/ws/{job_id}` - تحديثات مباشرة

## 🧪 الاختبار

### اختبار خدمات الذكاء الاصطناعي
```python
# اختبار LandingAI
from app.services.landing_ai_service import landing_ai_service
result = await landing_ai_service.extract_from_file("test.pdf")

# اختبار Gemini
from app.services.gemini_service import gemini_service
comparison = await gemini_service.compare_texts("نص قديم", "نص جديد")

# اختبار المقارنة البصرية
from app.services.visual_comparison_service import visual_comparison_service
visual_result = await visual_comparison_service.compare_images("img1.jpg", "img2.jpg")
```

### اختبار الأداء
```bash
# اختبار الحمولة باستخدام Apache Bench
ab -n 100 -c 10 http://localhost:8000/api/v1/health

# مراقبة استخدام الذاكرة
docker stats

# مراقبة Celery
celery -A celery_app.worker inspect active
```

## 📈 المراقبة والصيانة

### مراقبة Celery
- **Flower Dashboard**: http://localhost:5555
- **Redis CLI**: `redis-cli monitor`
- **Logs**: `docker-compose logs -f worker`

### مراقبة FastAPI
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Metrics**: http://localhost:8000/metrics (إذا مفعل)

### تنظيف الملفات
```bash
# تنظيف الملفات المؤقتة (أقدم من 7 أيام)
find uploads/ -type f -mtime +7 -delete

# تنظيف نتائج المعالجة القديمة
find uploads/results/ -type d -mtime +30 -exec rm -rf {} +
```

## 🔧 إعدادات متقدمة

### تخصيص LandingAI
```bash
# في ملف .env
LANDINGAI_BATCH_SIZE=4                    # عدد الملفات المتوازية
LANDINGAI_MAX_WORKERS=2                   # عدد العمليات
LANDINGAI_MAX_RETRIES=50                  # عدد المحاولات
LANDINGAI_SAVE_VISUAL_GROUNDINGS=True     # حفظ المناطق البصرية
```

### تخصيص Gemini
```bash
GEMINI_MODEL=gemini-1.5-pro              # نموذج Gemini
GEMINI_TEMPERATURE=0.3                   # درجة الإبداع
GEMINI_MAX_OUTPUT_TOKENS=8192            # الحد الأقصى للإخراج
```

### تخصيص المقارنة البصرية
```bash
VISUAL_COMPARISON_SSIM_WEIGHT=0.4        # وزن SSIM
VISUAL_COMPARISON_PHASH_WEIGHT=0.2       # وزن pHash
VISUAL_COMPARISON_CLIP_WEIGHT=0.4        # وزن CLIP
VISUAL_COMPARISON_THRESHOLD=0.85         # عتبة التشابه
```

## 🚨 استكشاف الأخطاء

### مشاكل شائعة

#### 1. خطأ في اتصال Redis
```bash
# التحقق من تشغيل Redis
redis-cli ping

# إعادة تشغيل Redis
sudo systemctl restart redis
```

#### 2. خطأ في مفاتيح API
```bash
# التحقق من صحة مفتاح Gemini
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# اختبار LandingAI
python -c "
import os
from agentic_doc.parse import parse
print('LandingAI Key:', 'OK' if os.getenv('VISION_AGENT_API_KEY') else 'Missing')
"
```

#### 3. مشاكل في المعالجة
```bash
# مراقبة Celery Workers
celery -A celery_app.worker inspect active

# إعادة تشغيل Workers
celery -A celery_app.worker control shutdown
celery -A celery_app.worker worker --loglevel=info
```

#### 4. مشاكل في الذاكرة
```bash
# مراقبة استخدام الذاكرة
htop
docker stats

# تقليل عدد Workers
export MAX_WORKERS=1
export LANDINGAI_BATCH_SIZE=2
```

## 📚 الموارد والمراجع

### وثائق API
- **LandingAI**: https://docs.landing.ai/
- **Google Gemini**: https://ai.google.dev/docs
- **FastAPI**: https://fastapi.tiangolo.com/
- **Celery**: https://docs.celeryproject.org/

### أمثلة الاستخدام
- راجع مجلد `examples/` للأمثلة الكاملة
- اختبر باستخدام `test_data/` للملفات التجريبية

### الدعم والمساعدة
- فحص اللوجز: `docker-compose logs -f`
- مراقبة الصحة: `/api/v1/health/detailed`
- تقارير الأخطاء: راجع ملفات اللوج في `logs/`

---

## 🎯 الخطوات التالية

1. **إضافة PowerPoint Export**: تصدير النتائج لـ PowerPoint
2. **تحسين الأداء**: تحسين خوارزميات المقارنة
3. **اختبارات شاملة**: إضافة اختبارات وحدة ودمج
4. **مراقبة متقدمة**: إضافة Prometheus/Grafana
5. **أمان محسن**: إضافة authentication وauthorization

**🚀 النظام جاهز للاستخدام مع LandingAI و Gemini الحقيقيين!** 