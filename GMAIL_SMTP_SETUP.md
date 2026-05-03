# Gmail SMTP Setup for Production

To enable real email sending for password reset functionality in production, follow these steps:

## 1. Enable 2-Factor Authentication (2FA)

1. Go to your Google Account: https://myaccount.google.com/
2. Click on "Security"
3. Enable 2-Step Verification if not already enabled

## 2. Generate an App Password

1. After enabling 2FA, go to: https://myaccount.google.com/apppasswords
2. Select "Mail" for the app
3. Select "Other (Custom name)" and enter "Classora LMS"
4. Click "Generate"
5. Copy the 16-character password (formatted as: xxxx xxxx xxxx xxxx)

## 3. Update Django Settings

In `classora/settings.py`, uncomment and update the email configuration:

```python
# Email configuration for Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'classora.lms@gmail.com'
EMAIL_HOST_PASSWORD = 'your-16-character-app-password'  # No spaces
DEFAULT_FROM_EMAIL = 'Classora LMS <classora.lms@gmail.com>'
EMAIL_TIMEOUT = 30
```

## 4. Test Email Configuration

Run the test command to verify email sending works:

```bash
python manage.py test_email
```

## 5. Security Notes

- Never commit the app password to version control
- Use environment variables in production for sensitive credentials
- Consider using a dedicated email service like SendGrid for production
- Monitor email sending quotas and limits

## 6. Alternative: Environment Variables

For better security, use environment variables:

```python
import os

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', f'Classora LMS <{EMAIL_HOST_USER}>')
```

## 7. Troubleshooting

If emails fail to send:

1. Verify the app password is correct (no spaces)
2. Check that 2FA is enabled on the Google account
3. Ensure the app password hasn't been revoked
4. Check Gmail SMTP connectivity and firewall settings
5. Review Django logs for specific error messages
