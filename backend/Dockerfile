# استخدام Python 3.11 كقاعدة
FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# تثبيت التبعيات النظام
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملف التبعيات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إنشاء المجلدات المطلوبة
RUN mkdir -p uploads logs && \
    chmod 755 uploads logs

# إنشاء مستخدم غير جذر
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# الصحة
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# تشغيل التطبيق
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 