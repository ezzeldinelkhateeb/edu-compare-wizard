# استكشاف الأخطاء وإصلاحها
# Troubleshooting Guide

## مشكلة: المقارنة تتوقف عند 0% "إنشاء جلسة رفع"

### الأسباب المحتملة:
1. **الخادم الخلفي غير يعمل**
2. **مشكلة في Redis** 
3. **مشكلة في Celery Worker**
4. **مشكلة في CORS**

### الحلول:

#### 1. تأكد من تشغيل جميع الخدمات

**في Terminal/PowerShell الأول - تشغيل Redis:**
```bash
# تأكد من تشغيل Redis
redis-server.exe
# أو إذا كان مُثبت كخدمة
net start redis
```

**في Terminal الثاني - تشغيل Celery Worker:**
```bash
cd backend
celery -A celery_app.worker worker --loglevel=info --pool=solo
```

**في Terminal الثالث - تشغيل FastAPI Server:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**في Terminal الرابع - تشغيل Frontend:**
```bash
npm run dev
```

#### 2. اختبار الخادم الخلفي

```bash
# اختبار صحة الخادم
curl http://localhost:8000/health

# اختبار إنشاء جلسة
curl -X POST http://localhost:8000/api/v1/upload/session \
  -H "Content-Type: application/json" \
  -d '{"session_name":"test","description":"test"}'
```

#### 3. فحص الـ Logs

**فحص logs الخادم الخلفي:**
- تحقق من Terminal FastAPI للأخطاء
- تحقق من Terminal Celery للأخطاء

**فحص logs Frontend:**
- افتح Developer Tools (F12)
- تحقق من Console للأخطاء
- تحقق من Network tab للطلبات الفاشلة

#### 4. إعادة تشغيل جميع الخدمات

```bash
# إيقاف جميع العمليات (Ctrl+C في كل Terminal)
# ثم إعادة تشغيلها بالترتيب:

# 1. Redis
# 2. Celery Worker  
# 3. FastAPI Server
# 4. Frontend
```

### رسائل الخطأ الشائعة:

#### "انتهت مهلة الاتصال - تأكد من تشغيل الخادم الخلفي"
- **الحل:** تأكد من تشغيل FastAPI على http://localhost:8000

#### "Backend غير متاح"
- **الحل:** تأكد من تشغيل Redis وعدم وجود أخطاء في بدء التشغيل

#### "فشل في إنشاء الجلسة: 500"
- **الحل:** تحقق من logs الخادم الخلفي وتأكد من عمل Celery

### متطلبات النظام:
- Python 3.8+
- Node.js 18+
- Redis Server
- جميع dependencies مُثبتة 