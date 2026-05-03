from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test email configuration'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Testing email configuration...')
            self.stdout.write(f'Email Host: {settings.EMAIL_HOST}')
            self.stdout.write(f'Email Port: {settings.EMAIL_PORT}')
            self.stdout.write(f'Email User: {settings.EMAIL_HOST_USER}')
            self.stdout.write(f'Use TLS: {settings.EMAIL_USE_TLS}')
            
            send_mail(
                subject='Test Email from Classora LMS',
                message='This is a test email to verify the email configuration is working.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['classora.lms@gmail.com'],  # Send to self for testing
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS('Email sent successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email: {e}'))
