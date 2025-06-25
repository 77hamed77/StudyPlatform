    # استخدم صورة Python أساسية رسمية
    # استخدم python:3.11-slim-buster لتقليل حجم الصورة
    FROM python:3.11-slim-buster

    # تحديث قوائم الحزم وتثبيت التبعيات الأساسية المطلوبة للبناء
    # libpq-dev ضروري لـ psycopg2-binary إذا لم يكن pre-built wheel متاحًا
    # build-essential و pkg-config و default-libmysqlclient-dev (أو ما يعادله) يمكن أن يكون مفيدًا لحزم أخرى
    RUN apt-get update && \
        apt-get install -y --no-install-recommends \
            build-essential \
            libpq-dev \
            pkg-config \
            # إذا كنت تحتاج إلى أي أدوات تطوير أخرى، أضفها هنا
            # git (إذا كنت تستخدم GitPython مثلاً)
            # libmariadb-dev (إذا كنت تستخدم mysqlclient فعلاً، لكن يجب إزالته)
        && rm -rf /var/lib/apt/lists/*

    # تعيين دليل العمل داخل الحاوية
    WORKDIR /app

    # تثبيت التبعيات المطلوبة
    # نسخ ملف requirements.txt إلى دليل العمل
    COPY requirements.txt .

    # تثبيت تبعيات Python
    # استخدام --no-cache-dir لتقليل حجم الصورة
    # استخدام --default-timeout لزيادة المهلة الزمنية للتنزيل
    RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

    # نسخ باقي كود التطبيق إلى الحاوية
    COPY . .

    # جمع الملفات الثابتة
    # --noinput لتجنب أي مطالبات تفاعلية
    RUN python manage.py collectstatic --noinput

    # تعريف متغير PORT الذي سيتلقاه التطبيق من البيئة
    # Koyeb سيزوده تلقائياً
    ENV PORT=8000

    # أمر بدء التشغيل لـ Gunicorn
    # يستخدم المتغير PORT الذي يوفره Koyeb
    CMD ["gunicorn", "study_platform.wsgi", "--bind", "0.0.0.0:$(PORT)", "--workers", "2", "--timeout", "120"]
    