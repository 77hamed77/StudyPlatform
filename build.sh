#!/usr/bin/env bash
# exit on error
set -o errexit

echo "-----> Installing requirements..."
pip install -r requirements.txt

echo "-----> Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "-----> Applying database migrations..."
python manage.py migrate --no-input

# يمكنك إضافة أي أوامر بناء أخرى هنا (مثل إنشاء superuser إذا كان هذا نشرًا أوليًا)
# echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'password')" | python manage.py shell