from django.db import migrations
from django.contrib.auth.hashers import make_password

def setup_data(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('accounts', 'Profile')
    Department = apps.get_model('accounts', 'Department')
    Complaint = apps.get_model('accounts', 'Complaint')

    # 1. Remove dummy complaints
    Complaint.objects.all().delete()

    # 2. Rename existing 'admin' roles to 'dean'
    Profile.objects.filter(role='admin').update(role='dean')

    # 3. Create BBIT Department
    bbit_dept, _ = Department.objects.get_or_create(
        name='BBIT', 
        defaults={'code': 'BBIT', 'description': 'Bachelor of Business Information Technology'}
    )

    # 4. Create Users
    users_to_create = [
        {
            'username': 'officerdavisjoy',
            'email': 'davisjoy561@gmail.com',
            'first_name': 'Davis',
            'last_name': 'Joy',
            'password': '123456789!',
            'role': 'officer',
            'department': 'BBIT'
        },
        {
            'username': 'terryosunga',
            'email': 'osungaterry@gmail.com',
            'first_name': 'Terry',
            'last_name': 'Osunga',
            'password': '123456789!',
            'role': 'dean',
            'department': 'Administration'
        },
        {
            'username': 'frida',
            'email': 'rennaguilder@gmail.com',
            'first_name': 'Frida',
            'last_name': '',
            'password': '123456789!',
            'role': 'complainant',
            'department': 'Student Body'
        }
    ]

    for user_data in users_to_create:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'password': make_password(user_data['password']),
            }
        )
        if created:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = user_data['role']
            profile.department = user_data['department']
            profile.full_name = f"{user_data['first_name']} {user_data['last_name']}".strip()
            profile.save()

def reverse_setup_data(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_aiinsight_auditlog_complaint_complaintattachment_and_more'),
    ]

    operations = [
        migrations.RunPython(setup_data, reverse_setup_data),
    ]
