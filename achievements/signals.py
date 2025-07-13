from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils import timezone # Import timezone for datetime operations
from django.db import transaction # For atomic updates

# Import models from other apps (ensure paths are correct)
try:
    from tasks.models import Task
except ImportError:
    Task = None
    print("Warning: tasks.models.Task not found. Task-related signals will be skipped.")

try:
    from files_manager.models import StudentSummary
except ImportError:
    StudentSummary = None
    print("Warning: files_manager.models.StudentSummary not found. StudentSummary-related signals will be skipped.")

# Assuming Notification model is in core app
try:
    from core.models import Notification
except ImportError:
    Notification = None
    print("Warning: core.models.Notification not found. Notifications will not be created.")


from .models import Badge, UserBadge, UserAchievementStats, XPTransaction, StudyChallenge, UserStudyChallenge

# --- Badge Definitions (can be managed from Django Admin or defined here) ---
# It's better to create these Badges via Django Admin and refer to them by their badge_type_key
# For demonstration, we'll define them here with defaults for get_or_create.

BADGE_TASK_COMPLETER_1_KEY = 'TASK_COMPLETER_1'
BADGE_TASK_COMPLETER_5_KEY = 'TASK_COMPLETER_5'
BADGE_TASK_COMPLETER_10_KEY = 'TASK_COMPLETER_10' # New badge
BADGE_SUMMARY_CONTRIBUTOR_1_KEY = 'SUMMARY_CONTRIBUTOR_1'
BADGE_SUMMARY_CONTRIBUTOR_3_KEY = 'SUMMARY_CONTRIBUTOR_3' # New badge
BADGE_LEVEL_UP_5_KEY = 'LEVEL_UP_5' # New badge for reaching level 5

# XP Rewards Configuration
XP_REWARDS = {
    'task_completed': 50,
    'summary_approved': 100,
    'challenge_completed': 200, # Base XP for challenge completion, plus challenge-specific reward
    'level_up': 0, # XP is gained, not awarded on level up itself
}

def award_xp_to_user(user, amount, activity, related_object=None):
    """
    يضيف نقاط خبرة للمستخدم ويسجل المعاملة.
    """
    if not user or amount <= 0:
        return False

    with transaction.atomic(): # Ensure atomicity for XP updates
        stats, created = UserAchievementStats.objects.get_or_create(user=user)
        old_level = stats.level
        stats.add_xp(amount) # This method handles level up and saves stats

        # Record the XP transaction
        xp_transaction = XPTransaction.objects.create(
            user=user,
            amount=amount,
            activity=activity,
            content_object=related_object
        )

        # Notify user if they leveled up
        if Notification and stats.level > old_level:
            Notification.objects.create(
                recipient=user,
                verb=_("لقد ارتفع مستواك!"),
                description=_("تهانينا! لقد وصلت إلى المستوى ") + f"{stats.level}!"
            )
            # Check for level-specific badges
            if stats.level >= 5:
                award_badge_to_user(user, BADGE_LEVEL_UP_5_KEY, {
                    'name': _('المستوى الخامس'),
                    'description': _('لقد وصلت إلى المستوى 5! استمر في التقدم!'),
                    'icon_class': 'fas fa-trophy',
                    'criteria': _('الوصول إلى المستوى 5')
                })
        return True
    return False


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
    else:
        try:
            badge = Badge.objects.get(badge_type_key=badge_key)
        except Badge.DoesNotExist:
            print(f"Warning: Badge with key '{badge_key}' not found in database and no default details provided.")
            return False

    if badge:
        user_badge, created_user_badge = UserBadge.objects.get_or_create(user=user, badge=badge)

        if created_user_badge:
            if Notification:
                target_content_type = ContentType.objects.get_for_model(Badge)
                Notification.objects.create(
                    recipient=user,
                    verb=_("حصلت على شارة جديدة!"),
                    target_content_type=target_content_type,
                    target_object_id=badge.pk,
                    description=_("تهانينا! لقد حصلت على شارة: ") + f"'{badge.name}'"
                )
            # Award XP for earning a badge (optional, can be configured)
            # award_xp_to_user(user, 100, _("اكتساب شارة"), badge)
            return True
    return False


# --- Task Signals ---
if Task:
    @receiver(post_save, sender=Task)
    def handle_task_events_and_badges(sender, instance, created, **kwargs):
        if instance.status == 'completed' and instance.user:
            user = instance.user
            completed_tasks_count = Task.objects.filter(user=user, status='completed').count()

            # Award XP for task completion
            award_xp_to_user(user, XP_REWARDS['task_completed'], _("إكمال مهمة"), instance)

            # Award Badges for task completion
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
            
            if completed_tasks_count >= 10: # New badge
                award_badge_to_user(user, BADGE_TASK_COMPLETER_10_KEY, {
                    'name': _('مُنجز محترف'),
                    'description': _('مذهل! لقد أكملت 10 مهام.'),
                    'icon_class': 'fas fa-award',
                    'criteria': _('إكمال 10 مهام')
                })
            
            # Update Study Challenges related to task completion
            active_challenges = StudyChallenge.objects.filter(
                challenge_type='tasks_completed',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
                is_active=True
            )
            for challenge in active_challenges:
                user_challenge, created_uc = UserStudyChallenge.objects.get_or_create(
                    user=user,
                    challenge=challenge
                )
                if not user_challenge.completed:
                    user_challenge.update_progress(amount=1) # Increment by 1 for each completed task


# --- Student Summary Signals ---
if StudentSummary:
    @receiver(post_save, sender=StudentSummary)
    def handle_summary_events_and_badges(sender, instance, created, **kwargs):
        if not instance.uploaded_by:
            return

        user = instance.uploaded_by
        
        # Check if 'status' field was updated (to avoid duplicate notifications/XP on other field saves)
        update_fields = kwargs.get('update_fields')
        status_updated = update_fields is not None and 'status' in update_fields

        # Handle notifications for summary status changes
        verb_text = ""
        description_text = ""
        notification_needed = False

        if status_updated or created:
            if instance.status == 'approved':
                verb_text = _("تمت الموافقة على ملخصك")
                description_text = _("تمت الموافقة على ملخصك ") + f"'{instance.title[:30]}{'...' if len(instance.title) > 30 else ''}'."
                notification_needed = True
                # Award XP for approved summary
                award_xp_to_user(user, XP_REWARDS['summary_approved'], _("الموافقة على ملخص"), instance)

                # Award Badges for approved summaries
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
                if approved_summaries_count >= 3: # New badge
                    award_badge_to_user(user, BADGE_SUMMARY_CONTRIBUTOR_3_KEY, {
                        'name': _('مساهم ملخصات نشط'),
                        'description': _('لقد تمت الموافقة على 3 ملخصات لك. عمل رائع!'),
                        'icon_class': 'fas fa-book-reader',
                        'criteria': _('الموافقة على 3 ملخصات مرفوعة')
                    })
                
                # Update Study Challenges related to approved summaries
                active_challenges = StudyChallenge.objects.filter(
                    challenge_type='files_read', # Assuming 'files_read' can also cover approved summaries as content contributions
                    start_date__lte=timezone.now(),
                    end_date__gte=timezone.now(),
                    is_active=True
                )
                for challenge in active_challenges:
                    user_challenge, created_uc = UserStudyChallenge.objects.get_or_create(
                        user=user,
                        challenge=challenge
                    )
                    if not user_challenge.completed:
                        user_challenge.update_progress(amount=1) # Increment by 1 for each approved summary

            elif instance.status == 'rejected':
                verb_text = _("تم رفض ملخصك")
                description_text = _("تم رفض ملخصك ") + f"'{instance.title[:30]}{'...' if len(instance.title) > 30 else ''}'."
                if instance.admin_notes:
                    description_text += " " + _("ملاحظة المشرف: ") + f"{instance.admin_notes[:50]}{'...' if len(instance.admin_notes) > 50 else ''}"
                notification_needed = True
        
        if notification_needed and verb_text and Notification:
            target_content_type = ContentType.objects.get_for_model(instance)
            Notification.objects.create(
                recipient=user,
                verb=verb_text,
                target_content_type=target_content_type,
                target_object_id=instance.pk,
                description=description_text
            )


# --- Study Challenge Completion Signal ---
@receiver(post_save, sender=UserStudyChallenge)
def handle_user_challenge_completion(sender, instance, created, **kwargs):
    if instance.completed and (created or 'completed' in (kwargs.get('update_fields') or [])):
        user = instance.user
        challenge = instance.challenge

        # Award XP for challenge completion
        total_xp_reward = XP_REWARDS['challenge_completed'] + challenge.xp_reward
        award_xp_to_user(user, total_xp_reward, _("إكمال تحدي دراسي"), challenge)

        # Award Badge for challenge completion if defined
        if challenge.badge_reward:
            award_badge_to_user(user, challenge.badge_reward.badge_type_key, {
                'name': challenge.badge_reward.name,
                'description': challenge.badge_reward.description,
                'icon_class': challenge.badge_reward.icon_class,
                'criteria': challenge.badge_reward.criteria_description
            })
        
        # Notify user about challenge completion
        if Notification:
            target_content_type = ContentType.objects.get_for_model(StudyChallenge)
            Notification.objects.create(
                recipient=user,
                verb=_("أكملت تحديًا دراسيًا!"),
                target_content_type=target_content_type,
                target_object_id=challenge.pk,
                description=_("تهانينا! لقد أكملت التحدي: ") + f"'{challenge.name}'"
            )

