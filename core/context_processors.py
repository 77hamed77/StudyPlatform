from .models import UserProfile, Notification # تأكد من استيراد موديل Notification إذا لم يكن كذلك

def common_context(request):
    """
    معالج سياق عام لإضافة بيانات مشتركة لجميع القوالب.
    """
    context_data = {
        'user_profile': None,
        'unread_notifications_count': 0,
        'latest_notifications_for_dropdown': [],
    }
    if request.user.is_authenticated:
        try:
            # استخدام select_related('user') إذا كان UserProfile ليس المفتاح الأساسي هو user
            # لكن بما أن user هو primary_key، فلا حاجة لـ select_related هنا
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            context_data['user_profile'] = profile
        except AttributeError: # هذا الشرط نادر الحدوث للمستخدمين المسجلين
            pass # يبقى user_profile هو None

        # جلب الإشعارات بكفاءة
        user_notifications = Notification.objects.filter(recipient=request.user)
        context_data['unread_notifications_count'] = user_notifications.filter(unread=True).count()
        # استخدام select_related للفاعل والهدف إذا كنت ستعرضهما في القائمة المنسدلة
        context_data['latest_notifications_for_dropdown'] = user_notifications.select_related(
            'actor_content_type', 'target_content_type' # لتحسين جلب الفاعل والهدف
        ).order_by('-timestamp')[:5] # جلب أحدث 5
        
    return context_data