from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse # تم استيرادها هنا لضمان توفرها في get_absolute_url

# تم تغيير هذه الاستيرادات:
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


# Assuming User model is the default Django User model or a custom one
User = get_user_model()

# Assuming Subject model is available from files_manager app
# You might need to adjust this import based on your project structure
try:
    from files_manager.models import Subject
except ImportError:
    # Fallback if files_manager.models.Subject is not found
    # This is a placeholder; in a real project, ensure Subject is accessible
    class Subject(models.Model):
        name = models.CharField(max_length=255, unique=True, verbose_name="اسم المادة (Placeholder)")
        def __str__(self):
            return self.name
    print("Warning: files_manager.models.Subject not found. Using a placeholder Subject model in community app.")


# --- Study Groups Models ---

class StudyGroup(models.Model):
    """
    يمثل مجموعة دراسية يمكن للطلاب الانضمام إليها للتعاون.
    """
    name = models.CharField(max_length=255, unique=True, verbose_name="اسم المجموعة")
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='study_groups', 
        verbose_name="المادة"
    )
    description = models.TextField(blank=True, null=True, verbose_name="وصف المجموعة")
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_study_groups', 
        verbose_name="المنشئ"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "مجموعة دراسية"
        verbose_name_plural = "مجموعات دراسية"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # This will be defined in community/urls.py later
        return reverse('community:study_group_detail', args=[str(self.pk)])

class GroupMembership(models.Model):
    """
    يربط المستخدمين بالمجموعات الدراسية ويحدد دورهم.
    """
    GROUP_ROLES = (
        ('member', 'عضو'),
        ('admin', 'مسؤول'),
    )
    group = models.ForeignKey(
        StudyGroup, 
        on_delete=models.CASCADE, 
        related_name='memberships', 
        verbose_name="المجموعة"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='group_memberships', 
        verbose_name="المستخدم"
    )
    role = models.CharField(
        max_length=20, 
        choices=GROUP_ROLES, 
        default='member', 
        verbose_name="الدور"
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانضمام")

    class Meta:
        unique_together = ('group', 'user') # A user can only be a member of a group once
        verbose_name = "عضوية مجموعة"
        verbose_name_plural = "عضويات المجموعات"

    def __str__(self):
        return f"{self.user.username} في {self.group.name} كـ {self.get_role_display()}"

class GroupMessage(models.Model):
    """
    يمثل رسالة داخل الدردشة الجماعية لمجموعة دراسية.
    """
    group = models.ForeignKey(
        StudyGroup, 
        on_delete=models.CASCADE, 
        related_name='messages', 
        verbose_name="المجموعة"
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_group_messages', 
        verbose_name="المرسل"
    )
    content = models.TextField(verbose_name="المحتوى")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="الوقت")

    class Meta:
        ordering = ['timestamp']
        verbose_name = "رسالة مجموعة"
        verbose_name_plural = "رسائل المجموعات"

    def __str__(self):
        return f"رسالة من {self.sender.username} في {self.group.name} بتاريخ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# --- Private Messaging Models (Placeholder for future) ---

class PrivateMessage(models.Model):
    """
    يمثل رسالة خاصة بين مستخدمين اثنين.
    """
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_private_messages', 
        verbose_name="المرسل"
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_private_messages', 
        verbose_name="المستلم"
    )
    content = models.TextField(verbose_name="المحتوى")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="الوقت")
    is_read = models.BooleanField(default=False, verbose_name="مقروءة")

    class Meta:
        ordering = ['timestamp']
        verbose_name = "رسالة خاصة"
        verbose_name_plural = "رسائل خاصة"

    def __str__(self):
        return f"رسالة من {self.sender.username} إلى {self.receiver.username} بتاريخ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# --- Q&A Platform Models (Placeholder for future) ---

class Question(models.Model):
    """
    يمثل سؤالاً يطرحه طالب في منصة السؤال والجواب.
    """
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='asked_questions', 
        verbose_name="الكاتب"
    )
    title = models.CharField(max_length=255, verbose_name="عنوان السؤال")
    content = models.TextField(verbose_name="محتوى السؤال")
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='questions', 
        verbose_name="المادة"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    # Optional: For tracking votes
    upvotes = models.IntegerField(default=0, verbose_name="تصويتات إيجابية")
    downvotes = models.IntegerField(default=0, verbose_name="تصويتات سلبية")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "سؤال"
        verbose_name_plural = "أسئلة"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # This will be defined in community/urls.py later
        return reverse('community:question_detail', args=[str(self.pk)])

class Answer(models.Model):
    """
    يمثل إجابة على سؤال في منصة السؤال والجواب.
    """
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='answers', 
        verbose_name="السؤال"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='provided_answers', 
        verbose_name="الكاتب"
    )
    content = models.TextField(verbose_name="محتوى الإجابة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    # Optional: For tracking votes on answers
    upvotes = models.IntegerField(default=0, verbose_name="تصويتات إيجابية")
    downvotes = models.IntegerField(default=0, verbose_name="تصويتات سلبية")
    is_accepted = models.BooleanField(default=False, verbose_name="إجابة مقبولة") # For question author to mark best answer

    class Meta:
        ordering = ['-created_at']
        verbose_name = "إجابة"
        verbose_name_plural = "إجابات"

    def __str__(self):
        return f"إجابة من {self.author.username} على {self.question.title[:30]}"

class Vote(models.Model):
    """
    يمثل تصويتاً (إيجابياً/سلبياً) على سؤال أو إجابة.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستخدم")
    # Generic foreign key for voting on Questions or Answers
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE) # تم تصحيح هذا السطر
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id') # تم تصحيح هذا السطر
    
    vote_type = models.SmallIntegerField(choices=[(1, 'Upvote'), (-1, 'Downvote')], verbose_name="نوع التصويت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التصويت")

    class Meta:
        unique_together = ('user', 'content_type', 'object_id') # A user can vote once per object
        verbose_name = "تصويت"
        verbose_name_plural = "تصويتات"

    def __str__(self):
        return f"تصويت {self.get_vote_type_display()} من {self.user.username} على {self.content_object}"
