# news/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .models import NewsItem # تأكد من أن هذا هو موديل الأخبار الصحيح
from core.models import Notification # استيراد موديل الإشعار من core
from django.utils.translation import gettext_lazy as _ # <--- هذا هو السطر الذي يجب إضافته

@receiver(post_save, sender=NewsItem)
def create_news_notification_on_important_published(sender, instance, created, **kwargs):
    send_notification = False
    if created and instance.is_important and instance.is_published:
        send_notification = True
    elif not created:
        if kwargs.get('update_fields') is None or \
           'is_important' in kwargs.get('update_fields') or \
           'is_published' in kwargs.get('update_fields'):
            if instance.is_important and instance.is_published:
                send_notification = True

    if send_notification:
        author = instance.author
        recipients = User.objects.filter(is_active=True).exclude(pk=author.pk if author else -1)

        actor_content_type = ContentType.objects.get_for_model(author) if author else None
        actor_object_id = author.pk if author else None
        target_content_type = ContentType.objects.get_for_model(instance)

        notifications_to_create = [
            Notification(
                recipient=user,
                actor_content_type=actor_content_type,
                actor_object_id=actor_object_id,
                verb=_("نشر خبرًا هامًا"), # <--- هنا يتم استخدام الدالة _
                target_content_type=target_content_type,
                target_object_id=instance.pk,
                description=f"{_('خبر جديد')}: {instance.title[:70]}{'...' if len(instance.title) > 70 else ''}" # <--- وهنا أيضًا
            )
            for user in recipients
        ]
        
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create, ignore_conflicts=True)