from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings


# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)                    # Auto login after registration
            messages.success(request, f"Welcome {user.get_full_name() or user.username}! Your account has been created.")
            return redirect('accounts:login')        # Go to your landing page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model, logout
from django.contrib import messages

User = get_user_model()


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Allow both admin and regular users, but redirect differently"""
        user = form.get_user()
        
        # Safety check: Ensure user has a profile
        if not hasattr(user, 'profile'):
            messages.error(self.request, "Invalid user account.")
            logout(self.request)
            return self.form_invalid(form)

        # Allow login for everyone
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect user based on their role after successful login"""
        user = self.request.user
        
        if hasattr(user, 'profile'):
            role = user.profile.role
            
            if role == 'dean':
                return reverse_lazy('accounts:dean_dashboard')
            elif role == 'officer':
                return reverse_lazy('accounts:officer_dashboard')
            else:
                # Default for clients or any other role
                return reverse_lazy('accounts:client_dashboard')
        
        # Fallback (should rarely happen due to the check in form_valid)
        return reverse_lazy('accounts:client_dashboard')

    def form_invalid(self, form):
        """Handle wrong credentials"""
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from .models import Complaint


class OfficerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'officer/officer_dashboard.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        # Base queryset: Complaints assigned to this officer
        my_complaints = Complaint.objects.filter(
            assigned_to=user
        ).select_related('complainant', 'department')

        # === Statistics ===
        total_assigned = my_complaints.count()
        
        # Include 'escalated' in open complaints for full visibility
        open_complaints = my_complaints.filter(
            status__in=['open', 'in_progress', 'escalated']
        ).count()
        
        # Urgent: High + Urgent priorities
        urgent_complaints = my_complaints.filter(
            status__in=['open', 'in_progress', 'escalated'], 
            priority__in=['high', 'urgent']
        ).count()
        
        resolved_complaints = my_complaints.filter(status__in=['resolved', 'closed']).count()
        today_complaints = my_complaints.filter(date_submitted__date=today).count()

        # Resolution Percentage
        resolution_percentage = 0
        if total_assigned > 0:
            resolution_percentage = round((resolved_complaints / total_assigned) * 100)

        # Average Resolution Time (using pre-calculated model field)
        avg_resolution = my_complaints.filter(
            status__in=['resolved', 'closed'],
            resolution_time_days__isnull=False
        ).aggregate(avg=Avg('resolution_time_days'))['avg']

        avg_resolution_days = round(avg_resolution, 1) if avg_resolution else 0.0

        # Recent Complaints (last 8)
        recent_complaints = my_complaints.order_by('-date_submitted')[:8]

        context.update({
            'total_complaints': total_assigned,
            'open_complaints': open_complaints,
            'urgent_complaints': urgent_complaints,
            'resolved_complaints': resolved_complaints,
            'today_complaints': today_complaints,
            'avg_resolution': avg_resolution_days,
            'resolution_percentage': resolution_percentage,
            'recent_complaints': recent_complaints,
        })

        return context

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Complaint

class OfficerAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'officer/officer_analytics.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now()
        last_30_days = today - timedelta(days=30)

        # Get only complaints assigned to this officer
        my_complaints = Complaint.objects.filter(assigned_to=user)

        # Basic Stats
        total_complaints = my_complaints.count()
        resolved = my_complaints.filter(status='resolved').count()
        pending = my_complaints.filter(status__in=['open', 'in_progress', 'escalated']).count()
        
        avg_resolution = my_complaints.filter(
            status='resolved', 
            resolution_time_days__isnull=False
        ).aggregate(avg=Avg('resolution_time_days'))['avg'] or 0

        # Last 30 days trend
        trend_data = []
        trend_labels = []
        for i in range(29, -1, -1):
            date = (today - timedelta(days=i)).date()
            count = my_complaints.filter(
                date_submitted__date=date
            ).count()
            trend_labels.append(date.strftime('%d %b'))
            trend_data.append(count)

        # Complaints by Category (for officer)
        dept_data = my_complaints.values('category').annotate(count=Count('id')).order_by('-count')
        dept_labels = [item['category'] for item in dept_data]
        dept_values = [item['count'] for item in dept_data]

        # Key Insights
        insights = [
            {
                'title': 'Resolution Rate',
                'description': f'You have resolved {resolved} out of {total_complaints} complaints.',
                'color': 'success' if resolved > total_complaints * 0.6 else 'warning',
                'icon': '✓'
            },
            {
                'title': 'Avg Response Time',
                'description': f'Your average resolution time is {avg_resolution:.1f} days.',
                'color': 'info',
                'icon': '📊'
            },
        ]

        context.update({
            'page_title': 'My Analytics',
            'total_complaints': total_complaints,
            'resolved': resolved,
            'pending': pending,
            'avg_resolution_time': round(avg_resolution, 1),
            
            # Chart Data
            'trend_labels': trend_labels,
            'trend_data': trend_data,
            'dept_labels': dept_labels,
            'dept_data': dept_values,
            
            'insights': insights,
        })
        return context

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
@login_required
def officer_user(request):
    users = User.objects.select_related('profile').order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': users.count(),
    }
    return render(request, 'officer/officer_users.html', context)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.http import JsonResponse
@login_required
def officer_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, 'profile', None)
    
    return render(request, 'accounts/user_detail_modal.html.html', {
        'user': user,
        'profile': profile,
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta
from .models import Complaint


@login_required
def dean_dashboard(request):
    today = timezone.now().date()

    # === Main Statistics ===
    total_complaints = Complaint.objects.count()
    
    open_complaints = Complaint.objects.filter(
        status__in=['open', 'in_progress', 'escalated']
    ).count()
    
    urgent_complaints = Complaint.objects.filter(
        status__in=['open', 'in_progress', 'escalated'],
        priority__in=['high', 'urgent']
    ).count()
    
    today_complaints = Complaint.objects.filter(
        date_submitted__date=today
    ).count()

    # === Overall Resolved Complaints (for percentage) ===
    resolved_complaints = Complaint.objects.filter(status__in=['resolved', 'closed']).count()

    # === Resolution Percentage ===
    resolution_percentage = 0
    if total_complaints > 0:
        resolution_percentage = round((resolved_complaints / total_complaints) * 100)

    # === Average Resolution Time ===
    # Use the pre-calculated field in the model for efficiency
    avg_resolution = Complaint.objects.filter(
        status__in=['resolved', 'closed'],
        resolution_time_days__isnull=False
    ).aggregate(
        avg=Avg('resolution_time_days')
    )['avg']

    avg_resolution_days = round(avg_resolution, 1) if avg_resolution else 0.0

    # === Recent Complaints ===
    recent_complaints = Complaint.objects.select_related('complainant', 'department')\
                        .order_by('-date_submitted')[:10]

    context = {
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
        'urgent_complaints': urgent_complaints,
        'today_complaints': today_complaints,
        'avg_resolution': avg_resolution_days,
        'resolution_percentage': resolution_percentage,
        'resolved_complaints': resolved_complaints,
        'recent_complaints': recent_complaints,
        'satisfaction_rate': resolution_percentage,
    }

    return render(request, 'accounts/dean_dashboard.html', context)

@login_required
def dean_complaints(request):
    complaints = Complaint.objects.select_related('complainant', 'department', 'assigned_to')\
                    .order_by('-date_submitted')
    
    context = {
        'complaints': complaints,
    }
    return render(request, 'accounts/complaints.html', context)

from django.shortcuts import get_object_or_404


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Complaint, ComplaintUpdate


@login_required
def dean_complaint_detail(request, complaint_id):
    # Optimized query with all related objects
    complaint = get_object_or_404(
        Complaint.objects.select_related(
            'complainant', 
            'department', 
            'assigned_to', 
            'assigned_to__profile'
        ),
        complaint_id=complaint_id
    )

    # Officers for assignment dropdown
    officers = User.objects.filter(
        profile__role='officer'
    ).select_related('profile').order_by('first_name', 'last_name')

    # Update history
    updates = ComplaintUpdate.objects.filter(
        complaint=complaint
    ).select_related('updated_by', 'updated_by__profile')\
     .order_by('-date')

    if request.method == 'POST':
        assigned_to_id = request.POST.get('assigned_to')
        
        if assigned_to_id:
            try:
                officer = User.objects.get(id=assigned_to_id)
                complaint.assigned_to = officer
                complaint.save()

                # Log the assignment
                ComplaintUpdate.objects.create(
                    complaint=complaint,
                    updated_by=request.user,
                    new_status=complaint.status,
                    comment=f"Assigned to {officer.get_full_name() or officer.username}"
                )
                
                messages.success(request, f"Successfully assigned to {officer.get_full_name() or officer.username}")
                return redirect('accounts:complaint_detail', complaint_id=complaint.complaint_id)
                
            except User.DoesNotExist:
                messages.error(request, "Officer not found.")
        else:
            messages.error(request, "Please select an officer.")

    context = {
        'complaint': complaint,
        'updates': updates,
        'officers': officers,
    }

    return render(request, 'accounts/complaint_detail.html', context)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Complaint, ComplaintUpdate   # Import both


@login_required
def complaint_detail(request, pk):
    # Get complaint with security check
    complaint = get_object_or_404(Complaint, id=pk, complainant=request.user)
    
    # Get updates for this specific complaint
    updates = ComplaintUpdate.objects.filter(
        complaint=complaint
    ).select_related('updated_by')

    context = {
        'complaint': complaint,
        'updates': updates,
    }
    return render(request, 'clients/complaint_detail.html', context)

from .models import *

@login_required
def dean_officers(request):
    departments = Department.objects.select_related('head_of_department').all()
    officers = User.objects.filter(profile__role='officer').select_related('profile')
    
    context = {
        'departments': departments,
        'officers': officers,
    }
    return render(request, 'accounts/officers.html', context)

@login_required
def dean_officer_detail(request, officer_id):
    officer = User.objects.select_related('profile').get(id=officer_id)

    context = {
        'officer': officer
    }
    return render(request, 'accounts/officer_detail.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, F
from django.db.models.functions import TruncDate
from datetime import timedelta
from .models import Complaint

@login_required
def dean_analytics(request):
    # Basic Stats
    total_complaints = Complaint.objects.count()
    resolved = Complaint.objects.filter(status='resolved').count()
    pending = Complaint.objects.filter(status='pending').count()

    # Average Resolution Time (in days)
    avg_resolution = Complaint.objects.filter(
        status='resolved',
        date_resolved__isnull=False
    ).aggregate(
        avg_days=Avg(F('date_resolved') - F('date_submitted'))
    )['avg_days']

    avg_resolution_time = round(avg_resolution.days, 1) if avg_resolution else 0

    # Trend - Last 30 Days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    trend_data = Complaint.objects.filter(
        date_submitted__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('date_submitted')
    ).values('date').annotate(count=Count('id')).order_by('date')

    trend_labels = [entry['date'].strftime('%d %b') for entry in trend_data]
    trend_values = [entry['count'] for entry in trend_data]

    # Complaints by Department
    dept_data = Complaint.objects.values('department__name').annotate(
        count=Count('id')
    ).order_by('-count')[:8]

    dept_labels = [item['department__name'] or "Unknown" for item in dept_data]
    dept_values = [item['count'] for item in dept_data]

    # Sample Insights (You can make this dynamic later)
    insights = [
        {
            'icon': '📈',
            'title': 'ICT Department leads complaints',
            'description': f'{dept_values[0] if dept_values else 0} complaints this month',
            'color': 'green'
        },
        {
            'icon': '⏳',
            'title': 'Average Resolution Time',
            'description': f'{avg_resolution_time} days',
            'color': 'gold'
        },
    ]

    context = {
        'total_complaints': total_complaints,
        'resolved': resolved,
        'pending': pending,
        'avg_resolution_time': avg_resolution_time,
        'trend_labels': trend_labels or ['No Data'],
        'trend_data': trend_values or [0],
        'dept_labels': dept_labels,
        'dept_data': dept_values,
        'insights': insights,
    }

    return render(request, 'accounts/analytics.html', context)

@login_required
def dean_insights(request):
    insights = AIInsight.objects.filter(is_active=True).order_by('-created_at')
    context = {'insights': insights}
    return render(request, 'accounts/insights.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


@login_required
def dean_users(request):
    users = User.objects.select_related('profile').order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': users.count(),
    }
    return render(request, 'accounts/users.html', context)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.http import JsonResponse

def dean_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, 'profile', None)
    
    return render(request, 'accounts/user_detail_modal.html', {
        'user': user,
        'profile': profile,
    })

from django.core.paginator import Paginator

def dean_audit(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)

    return render(request, 'accounts/audit.html', {'logs': logs_page})


@login_required
def dean_settings(request):
    total_users = User.objects.count()
    total_complaints = Complaint.objects.count()
    context = {
        'total_users': total_users,
        'total_complaints': total_complaints,
    }
    return render(request, 'accounts/settings.html', context)



@login_required
def officer_settings(request):
    total_users = User.objects.count()
    total_complaints = Complaint.objects.count()
    context = {
        'total_users': total_users,
        'total_complaints': total_complaints,
    }
    return render(request, 'officer/settings.html', context)


@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})

@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


from django.contrib.auth import authenticate, login, logout

def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from .models import Complaint


@login_required
def client_dashboard(request):
    user = request.user
    today = timezone.now().date()

    # Base queryset for current user
    user_complaints = Complaint.objects.filter(complainant=user)

    total_complaints = user_complaints.count()
    open_complaints = user_complaints.filter(status__in=['open', 'in_progress']).count()
    urgent_complaints = user_complaints.filter(
        status__in=['open', 'in_progress'], 
        priority='urgent'
    ).count()
    
    resolved_this_month = user_complaints.filter(
        status='resolved',
        date_resolved__gte=today.replace(day=1)
    ).count()

    today_complaints = user_complaints.filter(date_submitted__date=today).count()

    # Resolution Percentage
    resolved_complaints = user_complaints.filter(status='resolved').count()
    resolution_percentage = 0
    if total_complaints > 0:
        resolution_percentage = round((resolved_complaints / total_complaints) * 100)

    # Average Resolution Time
    avg_resolution = user_complaints.filter(
        status='resolved',
        date_resolved__isnull=False
    ).annotate(
        resolution_time=ExpressionWrapper(
            F('date_resolved') - F('date_submitted'),
            output_field=fields.DurationField()
        )
    ).aggregate(avg=Avg('resolution_time'))['avg']

    avg_resolution_days = round(avg_resolution.total_seconds() / (3600 * 24), 1) if avg_resolution else 0.0

    # Recent Complaints
    recent_complaints = user_complaints.select_related('department')\
                        .order_by('-date_submitted')[:6]

    context = {
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
        'urgent_complaints': urgent_complaints,
        'resolved_this_month': resolved_this_month,
        'today_complaints': today_complaints,
        'avg_resolution': avg_resolution_days,
        'resolution_percentage': resolution_percentage,
        'recent_complaints': recent_complaints,
    }

    return render(request, 'clients/dashboard.html', context)

@login_required
def submit_complaint(request):
    departments = Department.objects.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        department_id = request.POST.get('department')

        if title and description and category and department_id:
            try:
                department = Department.objects.get(id=department_id)
                complaint = Complaint.objects.create(
                    complainant=request.user,
                    title=title,
                    description=description,
                    category=category,
                    department=department,
                    status='open'
                )

                # Handle file attachment
                attachment_file = request.FILES.get('attachment')
                if attachment_file:
                    ComplaintAttachment.objects.create(
                        complaint=complaint,
                        file=attachment_file,
                        filename=attachment_file.name
                    )

                # Auto-assignment logic
                from django.db.models import Count, Q
                
                # Find officers in this department
                # We match by department name since profile.department is a string
                officers = User.objects.filter(
                    profile__role='officer',
                    profile__department__iexact=department.name
                ).annotate(
                    active_complaints_count=Count(
                        'assigned_complaints', 
                        filter=Q(assigned_complaints__status__in=['open', 'in_progress', 'escalated'])
                    )
                ).order_by('active_complaints_count')

                if officers.exists():
                    assigned_officer = officers.first()
                    complaint.assigned_to = assigned_officer
                    complaint.save()
                    
                    # Create a notification for the officer
                    Notification.objects.create(
                        recipient=assigned_officer,
                        complaint=complaint,
                        title="New Complaint Assigned",
                        message=f"You have been assigned a new complaint: {complaint.complaint_id}",
                        notification_type='assignment'
                    )

                    # Send Email to Officer
                    if assigned_officer.email:
                        try:
                            subject = f"New Complaint Assigned: {complaint.title}"
                            email_msg = f"Hello {assigned_officer.first_name or assigned_officer.username},\n\nYou have been assigned a new complaint.\n\nSubject: {complaint.title}\nDescription: {complaint.description}\n\nPlease log in to the portal to manage it."
                            send_mail(subject, email_msg, settings.DEFAULT_FROM_EMAIL, [assigned_officer.email])
                        except Exception as e:
                            print(f"Failed to send email to officer: {e}")
                    
                    messages.success(request, f"Complaint submitted and assigned to {assigned_officer.get_full_name() or assigned_officer.username}. ID: {complaint.complaint_id}")
                else:
                    messages.success(request, f"Complaint submitted successfully! ID: {complaint.complaint_id} (Awaiting assignment)")

                # 2. Notification for Dean(s)
                deans = User.objects.filter(profile__role='dean')
                assignment_text = f"Assigned to {complaint.assigned_to.get_full_name() or complaint.assigned_to.username}" if complaint.assigned_to else "Awaiting Assignment"
                for dean in deans:
                    Notification.objects.create(
                        recipient=dean,
                        complaint=complaint,
                        title=f"New Complaint: {complaint.complaint_id}",
                        message=f"A new complaint has been filed by {request.user.username}. {assignment_text}",
                        notification_type='new_complaint'
                    )

                
                return redirect('accounts:my_complaints')
            except Department.DoesNotExist:
                messages.error(request, "Selected department does not exist.")
    
    return render(request, 'clients/submit_complaint.html', {'departments': departments})


@login_required
def my_complaints(request):
    complaints = Complaint.objects.filter(complainant=request.user).order_by('-date_submitted')
    context = {'complaints': complaints}
    return render(request, 'clients/my_complaints.html', context)


@login_required
def track_complaints(request):
    # Show updates for user's complaints
    updates = ComplaintUpdate.objects.filter(
        complaint__complainant=request.user
    ).select_related('complaint', 'updated_by').order_by('-date')
    
    context = {'updates': updates}
    return render(request, 'clients/track.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMonth   # ← This was missing
from django.utils import timezone
from datetime import timedelta

from .models import Complaint   # Change if your model is in another app
from django.db.models.functions import TruncMonth

@login_required
def client_analytics(request):
    user = request.user
    today = timezone.now()

    # Total Complaints
    total_complaints = Complaint.objects.filter(complainant=user).count()

    # Status Breakdown
    status_data = Complaint.objects.filter(complainant=user).values('status').annotate(count=Count('id'))
    
    status_dict = {item['status']: item['count'] for item in status_data}

    pending = status_dict.get('pending', 0)
    in_progress = status_dict.get('in_progress', 0)
    resolved = status_dict.get('resolved', 0)

    # Complaints Trend - Last 6 Months
    six_months_ago = today - timedelta(days=180)
    
    trend_data = Complaint.objects.filter(
        complainant=user,
        date_submitted__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date_submitted')
    ).values('month').annotate(count=Count('id')).order_by('month')

    # Prepare data for charts
    labels = []
    trend_values = []
    
    for entry in trend_data:
        labels.append(entry['month'].strftime('%b %Y'))
        trend_values.append(entry['count'])

    # If no data, show dummy labels
    if not labels:
        labels = ['No Data Yet']
        trend_values = [0]

    context = {
        'total_complaints': total_complaints,
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved,
        'labels': labels,
        'trend_values': trend_values,
        'resolution_rate': round((resolved / total_complaints * 100), 1) if total_complaints > 0 else 0,
    }
    
    return render(request, 'clients/analytics.html', context)

@login_required
def client_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]
    context = {'notifications': notifications}
    return render(request, 'clients/notifications.html', context)


@login_required
def profile(request):
    total_complaints = Complaint.objects.filter(complainant=request.user).count()
    open_complaints = Complaint.objects.filter(complainant=request.user, status='open').count()
    
    context = {
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
    }
    return render(request, 'clients/profile.html', context)




# views.py
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Complaint

class OfficerMyComplaintsView(LoginRequiredMixin, ListView):
    model = Complaint
    template_name = 'officer/officer_my_complaints.html'
    context_object_name = 'complaints'
    paginate_by = 12

    def get_queryset(self):
        queryset = Complaint.objects.filter(
            assigned_to=self.request.user
        ).select_related('complainant', 'department').order_by('-date_submitted')

        # Apply status filter
        status = self.request.GET.get('status')
        if status and status in ['open', 'in_progress', 'resolved', 'closed', 'escalated']:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        total_complaints = self.get_queryset().count()   # Count after filter
        
        context.update({
            'page_title': 'My Complaints',
            'total_complaints': total_complaints,
            'current_filter': self.request.GET.get('status', 'all'),
        })
        return context
    
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from .models import Complaint


class OfficerComplaintDetailView(LoginRequiredMixin, DetailView):
    model = Complaint
    template_name = 'officer/officer_complaint_detail.html'
    context_object_name = 'complaint'
    slug_field = 'complaint_id'
    slug_url_kwarg = 'complaint_id'

    def get_queryset(self):
        """Ensure officer can only view their own assigned complaints"""
        return super().get_queryset().filter(assigned_to=self.request.user)

    def post(self, request, *args, **kwargs):
        complaint = self.get_object()
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')

        # Allowed statuses for officers (Added 'closed' as per request)
        allowed_statuses = ['in_progress', 'resolved', 'closed']

        if new_status in allowed_statuses:
            previous_status = complaint.status
            complaint.status = new_status
            
            if new_status == 'resolved':
                complaint.date_resolved = timezone.now()
            
            complaint.save()

            # Create an Update History record so it shows in Activity History
            ComplaintUpdate.objects.create(
                complaint=complaint,
                updated_by=request.user,
                previous_status=previous_status,
                new_status=new_status,
                comment=comment
            )
            
            messages.success(request, f"Complaint status updated to {complaint.get_status_display()}.")
        else:
            messages.error(request, f"Invalid status '{new_status}' selected.")

        return redirect('accounts:officer_complaint_detail', complaint_id=complaint.complaint_id)

@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        next_url = request.META.get('HTTP_REFERER')
        return redirect(next_url if next_url else 'accounts:login')
    
    from .models import Complaint
    complaint = Complaint.objects.filter(complaint_id__iexact=query).first()
    
    if not complaint:
        messages.error(request, f"Complaint {query} not found.")
        role = getattr(request.user.profile, 'role', 'client')
        if role == 'dean':
            return redirect('accounts:dean_dashboard')
        elif role == 'officer':
            return redirect('accounts:officer_dashboard')
        else:
            return redirect('accounts:client_dashboard')

    role = getattr(request.user.profile, 'role', 'client')
    if role == 'dean':
        return redirect('accounts:complaint_detail', complaint_id=complaint.complaint_id)
    elif role == 'officer':
        if complaint.assigned_to == request.user:
            return redirect('accounts:officer_complaint_detail', complaint_id=complaint.complaint_id)
        else:
            messages.error(request, "Access denied. You are not assigned to this complaint.")
            return redirect('accounts:officer_dashboard')
    else:
        if complaint.complainant == request.user:
             return redirect('accounts:detail', pk=complaint.id)
        else:
            messages.error(request, "Access denied. This complaint does not belong to you.")
            return redirect('accounts:client_dashboard')

from django.http import JsonResponse
@login_required
def get_notifications_ajax(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    notif_data = []
    for n in notifications:
        notif_data.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'type': n.notification_type or 'bell'
        })
    
    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notif_data
    })
@login_required
def dean_edit_user(request, user_id):
    if getattr(request.user.profile, 'role', 'client') != 'dean':
        messages.error(request, "Access denied.")
        return redirect('accounts:login')
    
    user_to_edit = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=user_to_edit)
    
    if request.method == 'POST':
        user_to_edit.username = request.POST.get('username')
        user_to_edit.email = request.POST.get('email')
        
        full_name = request.POST.get('full_name', '')
        if full_name:
            parts = full_name.split(' ', 1)
            user_to_edit.first_name = parts[0]
            user_to_edit.last_name = parts[1] if len(parts) > 1 else ''
        
        user_to_edit.save()
        
        profile.full_name = full_name
        profile.reg_id = request.POST.get('reg_id')
        profile.phone = request.POST.get('phone')
        profile.department = request.POST.get('department')
        profile.role = request.POST.get('role')
        profile.save()
        
        messages.success(request, f"User {user_to_edit.username} updated successfully.")
        return redirect('accounts:dean_users')
    
    from .models import Department
    departments = Department.objects.all()
    return render(request, 'accounts/edit_user.html', {
        'user_to_edit': user_to_edit,
        'profile': profile,
        'departments': departments,
        'role_choices': Profile.ROLE_CHOICES
    })

@login_required
def dean_delete_user(request, user_id):
    if getattr(request.user.profile, 'role', 'client') != 'dean':
        messages.error(request, "Access denied.")
        return redirect('accounts:login')
    
    user_to_delete = get_object_or_404(User, id=user_id)
    
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('accounts:dean_users')
    
    username = user_to_delete.username
    user_to_delete.delete()
    
    messages.success(request, f"User {username} and all associated data have been permanently deleted.")
    return redirect('accounts:dean_users')
