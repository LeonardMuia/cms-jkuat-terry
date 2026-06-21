# JKUAT Complaint Management System (CMS)

A professional web-based solution for Jomo Kenyatta University of Agriculture and Technology to manage, track, and resolve system-wide complaints with transparency.

## Features

- **Client Dashboard**: Submit complaints with categories and live tracking.
- **Officer Dashboard**: Manage assigned departmental complaints and update resolution status.
- **Dean Dashboard**: System-wide analytics, user management, and operational oversight.
- **Email Notifications**: Professional HTML notifications for assignments and status updates.
- **Modern UI**: Full dark-mode glassmorphism interface.

## Installation Guide

### 1. Prerequisites

- Python 3.9 or higher
- Pip (Python Package Manager)

### 2. Setup Environment

Extract the zip file to your preferred directory. Open a terminal/command prompt in that directory and run:

```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Initialization

The project comes with a pre-configured `db.sqlite3`. If you want to start fresh:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 6. Run the Application

```bash
python manage.py runserver
```

Access the portal at: `http://127.0.0.1:8000`

## Demo Accounts

If using the provided database:

- **Dean**: (Use createsuperuser to make your own)
- **Officer**: (Add via Dean dashboard)
- **Complainant**: (Self-register on the login page)

## Technologies Used

- Django (Backend Framework)
- Vanilla CSS (Styling & Glassmorphism)
- FontAwesome (Icons)
- SQLite (Database)
