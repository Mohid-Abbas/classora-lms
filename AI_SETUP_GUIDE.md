# AI Integration Setup Guide

This guide will help you set up the AI Assistant feature in Classora LMS using Google Gemini API.

## Prerequisites

1. Google Account (for Gemini API access)
2. Python 3.8+ installed
3. Virtual environment activated

## Step 1: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click on "Get API Key" in the left sidebar
4. Create a new API key (it's free for development and limited production use)
5. Copy your API key

## Step 2: Configure API Key

### Option A: Environment Variable (Recommended)
```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

### Option B: Add to Django settings
Add to `classora/settings.py`:
```python
GEMINI_API_KEY = 'your_api_key_here'
```

## Step 3: Install Dependencies

```bash
pip install google-generativeai==0.8.3
```

## Step 4: Restart Django Server

```bash
python manage.py runserver
```

## Step 5: Test the Integration

1. Login to your Classora LMS
2. Click on "AI Assistant" in the sidebar
3. You should see the AI Assistant interface with status "Online"

## Features Available

### 1. AI Chat
- Ask questions about your courses
- Get help with assignments
- Educational support

### 2. Quiz Generator
- Generate multiple-choice questions
- Choose difficulty level
- Specify number of questions
- Get explanations for answers

### 3. Assignment Feedback
- Paste student submissions
- Get AI-generated feedback
- Optional rubric support
- Overall scoring

### 4. Study Recommendations
- Personalized study plans
- Focus areas identification
- Resource recommendations
- Study tips

## API Usage Limits (Free Tier)

- **Queries per minute**: 60
- **Queries per day**: 1,500
- **Characters per day**: 1,000,000

For production use with higher limits, consider upgrading to a paid plan.

## Troubleshooting

### AI Assistant shows "Offline"
1. Check if API key is set correctly
2. Verify internet connection
3. Check browser console for errors
4. Ensure `google-generativeai` package is installed

### Error generating content
1. Check API quota limits
2. Verify the input text is not too long
3. Try refreshing the page

### Permission errors
Ensure the user is logged in and has proper authentication tokens.

## Security Notes

- Never commit API keys to version control
- Use environment variables in production
- Monitor API usage to avoid exceeding limits
- The API key should be kept secure

## Production Deployment

For production deployment:

1. Set the API key as an environment variable
2. Monitor usage through Google AI Studio dashboard
3. Consider implementing rate limiting
4. Add error logging for debugging
5. Set up alerts for API quota limits

## Cost Information

The Gemini API free tier includes:
- Generative AI models: Free
- Up to 60 requests per minute
- Up to 1,500 requests per day

For higher usage, paid plans are available starting at reasonable rates.

## Support

If you encounter issues:

1. Check the Django logs: `python manage.py runserver --verbosity=2`
2. Verify API key validity in Google AI Studio
3. Check network connectivity
4. Review browser console for JavaScript errors

## Next Steps

Once the AI Assistant is working, you can:

1. Customize the AI prompts for your specific needs
2. Add more AI-powered features
3. Integrate with other educational tools
4. Create custom AI workflows for your institution
