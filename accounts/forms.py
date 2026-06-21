from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile   

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-input',
        'placeholder': 'john.doe@jkuat.ac.ke'
    }))
    
    reg_id = forms.CharField(
        label="Registration / Staff ID",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., ENG/22001'
        })
    )

    full_name = forms.CharField(
        label="Full Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., John Doe'
        })
    )

    phone = forms.CharField(
        label="Phone Number",
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+254 700 000000'
        })
    )

    department = forms.ChoiceField(
        choices=[
            ('', 'Select your department'),
            ('engineering', 'School of Engineering'),
            ('computing', 'School of Computing & IT'),
            ('business', 'School of Business'),
            ('agriculture', 'School of Agriculture'),
            ('medicine', 'School of Medicine'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['reg_id', 'full_name', 'username', 'email', 'phone', 
                  'department', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add proper classes to default fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Create secure password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        
        # Save extra data to Profile
        profile = user.profile
        profile.reg_id = self.cleaned_data.get('reg_id')
        profile.full_name = self.cleaned_data.get('full_name')
        profile.phone = self.cleaned_data.get('phone')
        profile.department = self.cleaned_data.get('department')
        profile.role = 'complainant'  # Force every new user to be a complainant
        profile.save()
        
        return user
    








# complaints/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import (
    Complaint, ComplaintAttachment, ComplaintUpdate, 
    Department, Profile
)


class ComplaintForm(forms.ModelForm):
    """Form for students/complainants to submit a new complaint"""
    
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'department']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Faulty Wi-Fi in Lecture Hall B'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 6,
                'placeholder': 'Please describe your complaint in detail...'
            }),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'department': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'title': 'Subject / Title *',
            'description': 'Detailed Description *',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make department optional in form but required in view if needed
        self.fields['department'].required = False
        self.fields['department'].queryset = Department.objects.all().order_by('name')


class ComplaintUpdateForm(forms.ModelForm):
    """Form used by officers/admins to update complaint status"""
    
    class Meta:
        model = ComplaintUpdate
        fields = ['new_status', 'comment']
        widgets = {
            'new_status': forms.Select(attrs={'class': 'form-input'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Add your comment or resolution details...'
            }),
        }


class ProfileForm(forms.ModelForm):
    """Form for users to update their profile"""
    
    class Meta:
        model = Profile
        fields = ['full_name', 'reg_id', 'phone', 'department']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input'}),
            'reg_id': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'department': forms.TextInput(attrs={'class': 'form-input'}),
        }


class AssignComplaintForm(forms.ModelForm):
    """Form for admins/officers to assign complaint to an officer"""
    
    class Meta:
        model = Complaint
        fields = ['assigned_to', 'department', 'priority']
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-input'}),
            'department': forms.Select(attrs={'class': 'form-input'}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users who are officers or admins
        self.fields['assigned_to'].queryset = User.objects.filter(
            profile__role__in=['officer', 'admin']
        ).select_related('profile')


# Optional: Attachment upload form
class ComplaintAttachmentForm(forms.ModelForm):
    class Meta:
        model = ComplaintAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-input'})
        }