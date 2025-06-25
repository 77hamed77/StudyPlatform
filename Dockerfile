    # استخدم صورة Python أساسية رسمية
    # استخدم python:3.11-slim-buster أو python:3.11-slim لتقليل حجم الصورة
    FROM python:3.11-slim-buster

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

    # يمكن إضافة هذا إذا كنت تخدم ملفات الميديا عبر Whitenoise أيضاً (للملفات الصغيرة)
    # ولكن للتخزين السحابي (Cloudinary)، لن يكون له تأثير مباشر على ملفات الميديا المرفوعة
    