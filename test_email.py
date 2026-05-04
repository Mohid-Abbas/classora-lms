import os
import django
import sys

# Set up Django
sys.path.append(r'd:\Projects\FSE_Project\classora-lms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classora.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    print(f"Testing email with:")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    print(f"Password: {settings.EMAIL_HOST_PASSWORD[:4]}****")
    
    try:
        send_mail(
            'Test Email',
            'This is a test email from Classora LMS.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        print("Success! Email sent.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_email()
