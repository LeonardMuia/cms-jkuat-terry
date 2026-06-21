from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Extra Information'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Or simply register Profile
admin.site.register(Profile)





# complaints/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Profile, Department, Complaint, ComplaintAttachment,
    ComplaintUpdate, Notification, AIInsight, AuditLog
)


# ====================== INLINE PROFILE FOR USER ADMIN ======================
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'groups', 'profile__role')

    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'


# Unregister default User and register customized one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ====================== DEPARTMENT ADMIN ======================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head_of_department', 'email')
    search_fields = ('name', 'code')
    list_filter = ('name',)
    autocomplete_fields = ['head_of_department']


# ====================== COMPLAINT ADMIN ======================
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_id', 'complainant', 'title', 'category', 
                    'department', 'status', 'priority', 'date_submitted')
    list_filter = ('status', 'priority', 'category', 'department', 'date_submitted')
    search_fields = ('complaint_id', 'title', 'description', 'complainant__username')
    
    readonly_fields = ('complaint_id', 'date_submitted', 'date_updated', 
                      'date_resolved', 'resolution_time_days')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('complaint_id', 'complainant', 'title', 'description', 'category')
        }),
        ('Assignment & Status', {
            'fields': ('department', 'assigned_to', 'status', 'priority')
        }),
        ('Timestamps', {
            'fields': ('date_submitted', 'date_updated', 'date_resolved', 'resolution_time_days')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # New complaint
            obj.complainant = request.user
        super().save_model(request, obj, form, change)


# ====================== COMPLAINT ATTACHMENT ======================
@admin.register(ComplaintAttachment)
class ComplaintAttachmentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'filename', 'uploaded_at')
    search_fields = ('complaint__complaint_id', 'filename')


# ====================== COMPLAINT UPDATES ======================
@admin.register(ComplaintUpdate)
class ComplaintUpdateAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'updated_by', 'new_status', 'date')
    list_filter = ('new_status', 'date')
    search_fields = ('complaint__complaint_id', 'comment')


# ====================== NOTIFICATIONS ======================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'is_read', 'created_at', 'notification_type')
    list_filter = ('is_read', 'notification_type', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')


# ====================== AI INSIGHTS ======================
@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ('title', 'insight_type', 'severity', 'is_active', 'created_at')
    list_filter = ('insight_type', 'severity', 'is_active')
    search_fields = ('title', 'description')


# ====================== AUDIT LOGS ======================
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'details')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'