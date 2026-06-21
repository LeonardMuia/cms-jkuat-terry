from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
        all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20] # Last 20 notifications
        return {
            'unread_notifications_count': unread_notifications.count(),
            'notifications_list': all_notifications
        }
    return {
        'unread_notifications_count': 0,
        'notifications_list': []
    }
