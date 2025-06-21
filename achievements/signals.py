from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

# استيراد الموديلات من تطبيقات أخرى (تأكد من صحة المسارات)
try:
    from tasks.models import Task
except ImportError:
    Task = None # أو قم بإنشاء موديل وهمي إذا كان الاختبار يتطلب ذلك

try:
    from files_manager.models import StudentSummary
except ImportError:
    StudentSummary = None

from .models import Badge, UserBadge
from core.models import Notification # افترض أن موديل الإشعار في core

# --- تعريفات الشارات ---
# من الأفضل نقل هذا الجزء إلى ملف إعدادات أو مكان مركزي
# إذا أردت أن تكون الشارات نفسها مُدارة من Django Admin،
# ستحتاج لإنشاء كائنات Badge هناك ثم الإشارة إليها هنا بمفتاحها (badge_type_key)
# أو البحث عنها بالاسم/المفتاح.

# مثال باستخدام badge_type_key:
BADGE_TASK_COMPLETER_1_KEY = 'TASK_COMPLETER_1'
BADGE_TASK_COMPLETER_5_KEY = 'TASK_COMPLETER_5'
BADGE_SUMMARY_CONTRIBUTOR_1_KEY = 'SUMMARY_CONTRIBUTOR_1'

# يمكنك تعريف تفاصيل الشارات هنا إذا لم تكن ستُدار بالكامل من Admin
# أو يمكنك جلبها من قاعدة البيانات بناءً على المفتاح.
# للتبسيط، سنفترض أن كائنات Badge موجودة في قاعدة البيانات
# وسيتم البحث عنها باستخدام badge_type_key أو إنشاؤها إذا لم تكن موجودة.

def award_badge_to_user(user, badge_key, default_badge_details=None):
    """
    يمنح شارة لمستخدم إذا لم يكن قد حصل عليها بالفعل، وينشئ إشعارًا.
    default_badge_details: قاموس يحتوي على name, description, icon_class لتفاصيل الشارة إذا لم تكن موجودة.
    """
    if not user or not badge_key:
        return False

    badge = None
    if default_badge_details and 'name' in default_badge_details:
        badge, badge_created = Badge.objects.get_or_create(
            badge_type_key=badge_key,
            defaults={
                'name': default_badge_details['name'],
                'description': default_badge_details.get('description', ''),
                'icon_class': default_badge_details.get('icon_class', 'fas fa-medal'),
                'criteria_description': default_badge_details.get('criteria', '')
            }
        )
    else: # محاولة جلب الشارة الموجودة فقط
        try:
            badge = Badge.objects.get(badge_type_key=badge_key)
        except Badge.DoesNotExist:
            print(f"Warning: Badge with key '{badge_key}' not found in database and no default details provided.")
            return False # لا يمكن منح شارة غير موجودة إذا لم يتم توفير تفاصيل لإنشائها

    if badge:
        user_badge, created_user_badge = UserBadge.objects.get_or_create(user=user, badge=badge)

        if created_user_badge:
            target_content_type = ContentType.objects.get_for_model(Badge)
            Notification.objects.create(
                recipient=user,
                verb=_("حصلت على شارة جديدة!"),
                target_content_type=target_content_type,
                target_object_id=badge.pk,
                description=_("تهانينا! لقد حصلت على شارة: ") + f"'{badge.name}'"
            )
            return True
    return False


# --- إشارات المهام ---
if Task: # تحقق من أن موديل Task مُستورد بنجاح
    @receiver(post_save, sender=Task)
    def check_task_completion_badges(sender, instance, created, **kwargs):
        if instance.status == 'completed' and instance.user:
            user = instance.user
            completed_tasks_count = Task.objects.filter(user=user, status='completed').count()

            if completed_tasks_count >= 1:
                award_badge_to_user(user, BADGE_TASK_COMPLETER_1_KEY, {
                    'name': _('مُنجز مبتدئ'),
                    'description': _('أكملت مهمتك الأولى بنجاح!'),
                    'icon_class': 'fas fa-check-circle',
                    'criteria': _('إكمال أول مهمة')
                })
            
            if completed_tasks_count >= 5:
                award_badge_to_user(user, BADGE_TASK_COMPLETER_5_KEY, {
                    'name': _('مُنجز مواظب'),
                    'description': _('رائع! لقد أكملت 5 مهام.'),
                    'icon_class': 'fas fa-star',
                    'criteria': _('إكمال 5 مهام')
                })
            # أضف المزيد من شارات المهام هنا


# --- إشارات ملخصات الطلاب ---
if StudentSummary: # تحقق من أن موديل StudentSummary مُستورد بنجاح
    @receiver(post_save, sender=StudentSummary)
    def handle_summary_events_and_badges(sender, instance, created, **kwargs):
        if not instance.uploaded_by:
            return

        user = instance.uploaded_by
        verb_text = ""
        description_text = ""
        notification_needed = False
        
        # التحقق مما إذا كان حقل 'status' قد تم تحديثه (لتجنب إرسال إشعارات متكررة)
        # هذا يتطلب فحص kwargs.get('update_fields')
        status_updated = 'status' in (kwargs.get('update_fields') or [])

        if status_updated or created: # إرسال إشعار عند الإنشاء بحالة معينة أو عند تحديث الحالة
            if instance.status == 'approved':
                verb_text = _("تمت الموافقة على ملخصك")
                description_text = _("تمت الموافقة على ملخصك ") + f"'{instance.title[:30]}{'...' if len(instance.title) > 30 else ''}'."
                notification_needed = True
            elif instance.status == 'rejected':
                verb_text = _("تم رفض ملخصك")
                description_text = _("تم رفض ملخصك ") + f"'{instance.title[:30]}{'...' if len(instance.title) > 30 else ''}'."
                if instance.admin_notes:
                    description_text += " " + _("ملاحظة المشرف: ") + f"{instance.admin_notes[:50]}{'...' if len(instance.admin_notes) > 50 else ''}"
                notification_needed = True
        
        if notification_needed and verb_text:
            target_content_type = ContentType.objects.get_for_model(instance)
            # يمكن ترك الفاعل فارغًا (النظام) أو تتبع من قام بالتعديل في StudentSummaryAdmin
            Notification.objects.create(
                recipient=user,
                verb=verb_text,
                target_content_type=target_content_type,
                target_object_id=instance.pk,
                description=description_text
            )

        # شارات المساهمة بالملخصات (فقط عند الموافقة)
        if instance.status == 'approved':
            approved_summaries_count = StudentSummary.objects.filter(
                uploaded_by=user,
                status='approved'
            ).count()

            if approved_summaries_count >= 1:
                award_badge_to_user(user, BADGE_SUMMARY_CONTRIBUTOR_1_KEY, {
                    'name': _('المساهم الأول بالملخصات'),
                    'description': _('تمت الموافقة على أول ملخص قمت برفعه! شكرًا لمساهمتك.'),
                    'icon_class': 'fas fa-file-signature',
                    'criteria': _('الموافقة على أول ملخص مرفوع')
                })
            # أضف المزيد من شارات الملخصات هنا (مثلاً لـ 3 أو 5 ملخصات معتمدة)