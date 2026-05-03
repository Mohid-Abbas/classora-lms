# Security Guide for Classora LMS

This guide helps you securely manage credentials and sensitive information in your Classora LMS deployment.

## 🔐 What's Protected by .gitignore

The `.gitignore` file ensures these sensitive items are never committed:

### API Keys & Tokens
- `GEMINI_API_KEY` - Google Gemini AI API key
- Any other AI service API keys
- Database credentials
- Email service credentials
- Cloud storage keys

### Configuration Files
- `.env` files (all variants)
- `secrets.json`
- `credentials.json`
- `local_settings.py`
- Database dump files
- SSL certificates

### User Data
- Media uploads
- User uploaded files
- Private documents

## 📋 Setup Checklist

### 1. Environment Variables
```bash
# Copy the example file
cp env.example .env

# Edit with your actual values
# NEVER commit .env to version control
```

### 2. Required Variables
- `SECRET_KEY` - Django secret key
- `DB_PASSWORD` - Database password
- `GEMINI_API_KEY` - AI service API key

### 3. Optional Variables
- Email configuration
- Cloud storage keys
- Redis configuration

## 🚨 Security Best Practices

### Development Environment
1. **Never hardcode credentials** in code
2. **Use environment variables** for all secrets
3. **Keep .env files local** (never commit)
4. **Use different keys** for dev/prod

### Production Environment
1. **Use environment variables** or secret management service
2. **Enable HTTPS** always
3. **Set DEBUG=False** in production
4. **Use strong passwords** and rotate regularly
5. **Monitor API usage** and set quotas

### API Key Management
1. **Get API keys from official sources only**
2. **Use the most restrictive permissions** possible
3. **Monitor usage** through provider dashboards
4. **Rotate keys** if compromised

## 🔍 Common Security Mistakes to Avoid

### ❌ Don't Do This
```python
# BAD: Hardcoded API key
API_KEY = "AIzaSyC-abc123def456ghi789"

# BAD: Committed .env file
.env
GEMINI_API_KEY=AIzaSyC-abc123def456ghi789
```

### ✅ Do This Instead
```python
# GOOD: Use environment variable
import os
API_KEY = os.getenv('GEMINI_API_KEY')

# GOOD: .env is in .gitignore
.env (ignored)
.env.example (committed as template)
```

## 🛡️ Additional Security Measures

### 1. Django Settings
```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

SECRET_KEY = os.getenv('SECRET_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
```

### 2. Database Security
- Use strong database passwords
- Limit database user permissions
- Enable SSL for database connections
- Regular backups (stored securely)

### 3. File Upload Security
- Validate file types
- Scan for malware
- Store uploads outside web root
- Use cloud storage when possible

## 🔐 Environment-Specific Security

### Development
```bash
# .env.development
DEBUG=True
SECRET_KEY=dev-secret-key-not-for-production
GEMINI_API_KEY=your-dev-api-key
```

### Production
```bash
# .env.production
DEBUG=False
SECRET_KEY=very-strong-production-secret
GEMINI_API_KEY=your-production-api-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 📊 Monitoring & Alerts

### Set up monitoring for:
1. **API usage spikes** - Could indicate key compromise
2. **Failed login attempts** - Brute force attacks
3. **Error rates** - Potential security issues
4. **Unusual access patterns** - Data scraping attempts

### Google AI Studio Dashboard
- Monitor Gemini API usage
- Set up alerts for quota limits
- Review API key permissions

## 🔄 Key Rotation Procedure

1. **Generate new API key** from provider
2. **Update environment variables**
3. **Restart application**
4. **Test functionality**
5. **Delete old API key** after confirmation

## 🚨 Incident Response

If credentials are compromised:

1. **Immediately rotate** all exposed keys
2. **Review access logs** for unusual activity
3. **Update passwords** for all services
4. **Notify users** if data was affected
5. **Document the incident** for future prevention

## 📚 Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [Google AI Studio Security](https://aistudio.google.com/security)
- [OWASP Security Guidelines](https://owasp.org/)

## ⚠️ Important Reminders

- **NEVER** commit `.env` files to version control
- **ALWAYS** use HTTPS in production
- **REGULARLY** rotate API keys and passwords
- **MONITOR** your API usage and logs
- **KEEP** your dependencies updated

---

**Remember**: Security is an ongoing process, not a one-time setup. Stay vigilant and keep your credentials safe!
