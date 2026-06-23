# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import uuid

# ====================== YOUR EXISTING PROFILE (Improved) ======================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    reg_id = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True, 
        verbose_name="Registration / Staff ID"
    )
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    ROLE_CHOICES = [
        ('complainant', 'Complainant'),
        ('officer', 'Departmental Officer'),
        ('dean', 'Dean'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='complainant')

    def __str__(self):
        return f"{self.user.username} - {self.full_name or 'No name'}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# Auto-create Profile when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# ====================== DEPARTMENT MODEL ======================
class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code e.g. ICT, FIN, LIB, ENG")
    description = models.TextField(blank=True)
    head_of_department = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='department_head'
    )
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


# ====================== COMPLAINT CORE MODELS ======================
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    CATEGORY_CHOICES = [
        ('academic', 'Academic Services'),
        ('ict', 'ICT & Infrastructure'),
        ('hostel', 'Hostel & Accommodation'),
        ('finance', 'Finance & Fees'),
        ('library', 'Library Services'),
        ('health', 'Health & Wellness'),
        ('other', 'Other'),
    ]

    # Auto-generated unique ID like CMS-4821
    complaint_id = models.CharField(max_length=20, unique=True, editable=False)

    complainant = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='complaints_made'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='department_complaints'
    )
    
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_complaints'
    )

    date_submitted = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_resolved = models.DateTimeField(null=True, blank=True)

    resolution_time_days = models.FloatField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        # Generate complaint_id if not exists
        if not self.complaint_id:
            last_complaint = Complaint.objects.order_by('-id').first()
            next_id = 1 if not last_complaint else int(last_complaint.complaint_id.split('-')[1]) + 1
            self.complaint_id = f"CMS-{next_id:04d}"

        # Auto calculate resolution time
        if self.status == 'resolved' and not self.date_resolved:
            self.date_resolved = timezone.now()
            if self.date_submitted:
                delta = self.date_resolved - self.date_submitted
                self.resolution_time_days = round(delta.days + delta.seconds / 86400, 1)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_id} - {self.title[:50]}"


class ComplaintAttachment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='complaints/attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment: {self.filename} ({self.complaint.complaint_id})"


# ====================== COMPLAINT UPDATES / HISTORY ======================
class ComplaintUpdate(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaint_updates')
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES)
    comment = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Update on {self.complaint.complaint_id} by {self.updated_by}"


# ====================== NOTIFICATIONS ======================
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(
        max_length=50, 
        choices=[
            ('new_complaint', 'New Complaint'),
            ('status_update', 'Status Update'),
            ('assignment', 'Assignment'),
            ('general', 'General'),
        ],
        default='general'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}"


# ====================== AI INSIGHTS (for Admin Dashboard) ======================
class AIInsight(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    insight_type = models.CharField(max_length=50, choices=[
        ('recurring', 'Recurring Issue'),
        ('prediction', 'Prediction'),
        ('recommendation', 'Recommendation'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# ====================== AUDIT LOG ======================
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"
    











from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime

def get_dean_emails():
    return list(User.objects.filter(profile__role='dean').values_list('email', flat=True))

@receiver(post_save, sender=Complaint)
def send_new_complaint_emails(sender, instance, created, **kwargs):
    """Notify Dean and Officer when a new complaint is filed."""
    if not created:
        return

    subject = f"[{instance.complaint_id}] {instance.title}"
    dean_emails = get_dean_emails()
    recipients = set(dean_emails)
    
    if instance.assigned_to and instance.assigned_to.email:
        recipients.add(instance.assigned_to.email)
    
    if not recipients:
        return

    context = {
        'subject': subject,
        'complaint': instance,
        'year': datetime.now().year,
        'site_url': 'http://127.0.0.1:8000', # In production, use actual domain
        'type': 'new_complaint'
    }

    html_message = render_to_string('emails/new_complaint.html', context)
    plain_message = strip_tags(html_message)

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=list(recipients),
            headers={'Message-ID': f"<{instance.complaint_id}@cmsjkuat.ac.ke>"}
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
    except Exception as e:
        print(f"Failed to send new complaint email: {e}")

@receiver(post_save, sender=ComplaintUpdate)
def send_complaint_update_notifications(sender, instance, created, **kwargs):
    """Notify Complainant and Dean when status changes."""
    if not created:
        return

    complaint = instance.complaint
    complainant = complaint.complainant

    # 1. In-app Notification for complainant
    Notification.objects.create(
        recipient=complainant,
        complaint=complaint,
        title=f"Update: {complaint.complaint_id}",
        message=f"Status changed to {instance.get_new_status_display()}. {instance.comment or ''}",
        notification_type='assignment'
    )

    # 2. Email Notification (Threaded)
    subject = f"[{complaint.complaint_id}] {complaint.title}"
    dean_emails = get_dean_emails()
    recipients = set(dean_emails)
    if complainant.email:
        recipients.add(complainant.email)

    if not recipients:
        return

    context = {
        'subject': subject,
        'update': instance,
        'complaint': complaint,
        'year': datetime.now().year,
        'site_url': 'http://127.0.0.1:8000',
        'type': 'status_update'
    }

    html_message = render_to_string('emails/status_update.html', context)
    plain_message = strip_tags(html_message)

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=list(recipients),
            headers={
                'In-Reply-To': f"<{complaint.complaint_id}@cmsjkuat.ac.ke>",
                'References': f"<{complaint.complaint_id}@cmsjkuat.ac.ke>"
            }
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
    except Exception as e:
        print(f"Failed to send status update email: {e}")