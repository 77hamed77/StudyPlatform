from django.contrib import admin
from .models import Subject, Lecturer, FileType, MainFile, StudentSummary, UserFileInteraction
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
import os # تأكد من استيراد os إذا كنت تستخدم os.path.basename أو ما شابه

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'main_files_count', 'student_summaries_count')
    search_fields = ('name',)

    @admin.display(description=_('عدد الملفات الرئيسية'))
    def main_files_count(self, obj):
        return obj.main_files.count()

    @admin.display(description=_('عدد ملخصات الطلاب'))
    def student_summaries_count(self, obj):
        return obj.student_summaries.count()

@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'files_count')
    search_fields = ('name',)

    @admin.display(description=_('عدد الملفات المرتبطة'))
    def files_count(self, obj):
        return obj.main_files.count() # افتراض أن المحاضر مرتبط فقط بـ MainFile

@admin.register(FileType)
class FileTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'files_count')
    search_fields = ('name',)
    # يمكنك إضافة حقل icon_class هنا إذا أضفته للموديل

    @admin.display(description=_('عدد الملفات من هذا النوع'))
    def files_count(self, obj):
        return obj.main_files.count()


@admin.register(MainFile)
class MainFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'file_type', 'lecturer', 'uploaded_by_username', 'uploaded_at', 'file_size_display', 'get_file_link')
    list_filter = ('subject', 'file_type', 'lecturer', 'uploaded_at', 'uploaded_by')
    search_fields = ('title', 'description', 'subject__name', 'lecturer__name', 'uploaded_by__username')
    # file_extension أضف إلى readonly_fields لأنه يتم تعيينه تلقائياً
    readonly_fields = ('uploaded_at', 'updated_at', 'uploaded_by', 'file_extension')
    autocomplete_fields = ['subject', 'lecturer', 'file_type'] # أزل 'uploaded_by' من هنا
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'file')
        }),
        (_('التصنيف والمعلومات الإضافية'), {
            'fields': ('subject', 'lecturer', 'file_type')
        }),
        (_('معلومات الرفع'), {
            'fields': ('uploaded_by', 'uploaded_at', 'updated_at', 'file_extension'), # أضف file_extension هنا
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('اسم الرافع'), ordering='uploaded_by__username')
    def uploaded_by_username(self, obj):
        return obj.uploaded_by.username if obj.uploaded_by else '-'

    @admin.display(description=_('حجم الملف'))
    def file_size_display(self, obj):
        if obj.file and obj.file.name: # تأكد أن obj.file.name موجود
            try:
                size_in_bytes = obj.file.size
                if size_in_bytes < 1024:
                    return f"{size_in_bytes} Bytes"
                elif size_in_bytes < 1024 * 1024:
                    return f"{size_in_bytes / 1024:.2f} KB"
                elif size_in_bytes < 1024 * 1024 * 1024:
                    return f"{size_in_bytes / (1024 * 1024):.2f} MB"
                else:
                    return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"
            except FileNotFoundError:
                return _("ملف غير موجود") # رسالة واضحة للملفات المفقودة
            except Exception as e: # للتعامل مع أي أخطاء أخرى غير متوقعة
                return _(f"خطأ في الحجم ({e})")
        return "-" # إذا لم يكن هناك ملف

    @admin.display(description=_('رابط الملف'))
    def get_file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" download="{}{}">تنزيل الملف</a>', obj.file.url, obj.title, obj.file_extension)
        return _("لا يوجد ملف")
    get_file_link.short_description = _("الملف") # لتغيير اسم العمود في قائمة الأدمن

    def save_model(self, request, obj, form, change):
        if not change: # عند الإنشاء فقط
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subject', 'lecturer', 'file_type', 'uploaded_by')


@admin.register(StudentSummary)
class StudentSummaryAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'uploaded_by_username', 'status', 'uploaded_at_display', 'file_link', 'file_size_display')
    list_filter = ('status', 'subject', 'uploaded_by', 'uploaded_at')
    search_fields = ('title', 'subject__name', 'uploaded_by__username', 'admin_notes')
    list_editable = ('status',) # السماح بتعديل الحالة مباشرة
    readonly_fields = ('uploaded_by', 'uploaded_at', 'file_extension') # أضف file_extension
    actions = ['approve_summaries', 'reject_summaries_with_note'] # تحسين اسم الإجراء
    autocomplete_fields = ['subject'] # أزل 'uploaded_by' من هنا
    fieldsets = (
        (None, {
            'fields': ('title', 'file', 'subject')
        }),
        (_('حالة المراجعة'), {
            'fields': ('status', 'admin_notes')
        }),
        (_('معلومات الرفع'), {
            'fields': ('uploaded_by', 'uploaded_at', 'file_extension'), # أضف file_extension هنا
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('اسم الرافع'), ordering='uploaded_by__username')
    def uploaded_by_username(self, obj):
        return obj.uploaded_by.username

    @admin.display(description=_('تاريخ الرفع'), ordering='uploaded_at')
    def uploaded_at_display(self, obj):
        return obj.uploaded_at.strftime("%Y-%m-%d %H:%M")

    @admin.display(description=_('الملف'))
    def file_link(self, obj):
        if obj.file:
            # obj.file.url سيعيد URL الصحيح سواء كان محلياً أو Cloudinary
            # os.path.basename(obj.file.name) لا يزال مفيدًا للحصول على اسم الملف فقط
            return format_html("<a href='{url}' target='_blank'>{name}</a>", url=obj.file.url, name=os.path.basename(obj.file.name))
        return _("لا يوجد ملف")

    @admin.display(description=_('حجم الملف'))
    def file_size_display(self, obj):
        if obj.file and obj.file.name:
            try:
                size_in_bytes = obj.file.size
                if size_in_bytes < 1024:
                    return f"{size_in_bytes} Bytes"
                elif size_in_bytes < 1024 * 1024:
                    return f"{size_in_bytes / 1024:.2f} KB"
                elif size_in_bytes < 1024 * 1024 * 1024:
                    return f"{size_in_bytes / (1024 * 1024):.2f} MB"
                else:
                    return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"
            except FileNotFoundError:
                return _("ملف غير موجود")
            except Exception as e:
                return _(f"خطأ في الحجم ({e})")
        return "-"

    def approve_summaries(self, request, queryset):
        updated_count = queryset.update(status='approved', admin_notes=_("تمت الموافقة."))
        self.message_user(request, _(f"{updated_count} ملخص/ملخصات تم اعتمادها بنجاح."))
        # يمكنك إرسال إشعار للمستخدم هنا

    approve_summaries.short_description = _("الموافقة على الملخصات المحددة")

    def reject_summaries_with_note(self, request, queryset):
        # يمكنك هنا تطوير هذا الإجراء ليسمح بإدخال ملاحظة مخصصة لكل ملخص مرفوض
        # للتبسيط، سنستخدم ملاحظة عامة
        note = _("تم الرفض من قبل الإدارة. يرجى مراجعة معايير الملخصات.")
        updated_count = queryset.update(status='rejected', admin_notes=note)
        self.message_user(request, _(f"{updated_count} ملخص/ملخصات تم رفضها."))
        # يمكنك إرسال إشعار للمستخدم هنا

    reject_summaries_with_note.short_description = _("رفض الملخصات المحددة (مع ملاحظة عامة)")


@admin.register(UserFileInteraction)
class UserFileInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'main_file_title', 'marked_as_read', 'marked_at')
    list_filter = ('marked_as_read', 'user', 'main_file__subject') # فلترة حسب مادة الملف الرئيسي
    search_fields = ('user__username', 'main_file__title')
    autocomplete_fields = ['user', 'main_file']
    readonly_fields = ('marked_at',)

    @admin.display(description=_('عنوان الملف'), ordering='main_file__title')
    def main_file_title(self, obj):
        return obj.main_file.title
