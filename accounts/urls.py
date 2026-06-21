from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import *
app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dean/dashboard/', views.dean_dashboard, name='dean_dashboard'),
    path('dean/complaints/', views.dean_complaints, name='dean_complaints'),
    path('dean/officers/', views.dean_officers, name='dean_officers'),
    path('dean/analytics/', views.dean_analytics, name='dean_analytics'),
    path('dean/insights/', views.dean_insights, name='dean_insights'),
    path('dean/users/', views.dean_users, name='dean_users'),
    path('dean/audit/', views.dean_audit, name='dean_audit'),
    path('dean/settings/', views.dean_settings, name='dean_settings'),
        # Client URLs
    path('client/dashboard/', views.client_dashboard, name='client_dashboard'),
        # Client URLs
    path('client/submit/', views.submit_complaint, name='submit_complaint'),
    path('client/my-complaints/', views.my_complaints, name='my_complaints'),
    path('complaint/<int:pk>/', views.complaint_detail, name='detail'),   # ← Add this
    path('client/track/', views.track_complaints, name='track_complaints'),
    path('client/analytics/', views.client_analytics, name='client_analytics'),
    path('client/notifications/', views.client_notifications, name='client_notifications'),
    path('client/profile/', views.profile, name='profile'),
    path('dean/complaints/<str:complaint_id>/', views.dean_complaint_detail, name='complaint_detail'),
    path('dean/officers/<int:officer_id>/', views.dean_officer_detail, name='dean_officer_detail'),
    path('dean/user/detail/<int:user_id>/', views.dean_user_detail, name='dean_user_detail'),
    path('dean/user/edit/<int:user_id>/', views.dean_edit_user, name='dean_edit_user'),
    path('dean/user/delete/<int:user_id>/', views.dean_delete_user, name='dean_delete_user'),

    path('officer/dashboard/', OfficerDashboardView.as_view(), name='officer_dashboard'),
    path('officer/settings/', views.officer_settings, name='officer_settings'),
    path('officer/analytics/', OfficerAnalyticsView.as_view(), name='officer_analytics'),
    path('officer/my-complaints/', OfficerMyComplaintsView.as_view(), name='officer_my_complaints'),
    path('officer/complaint/<str:complaint_id>/', OfficerComplaintDetailView.as_view(), name='officer_complaint_detail'),
    
    # Notification URLs
    path('notifications/mark-read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('search/', views.global_search, name='global_search'),
    path('api/notifications/', views.get_notifications_ajax, name='get_notifications_ajax'),
]