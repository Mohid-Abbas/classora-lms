"""
AI Integration Module for Classora LMS
Using Google Gemini API for AI-powered features
"""

import os
import json
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
from .models import Quiz, Question, Course

logger = logging.getLogger(__name__)

# Configure Gemini API
if hasattr(settings, 'GEMINI_API_KEY'):
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    # Fallback to environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)

class AIAssistant:
    """AI Assistant for various LMS tasks"""
    
    def __init__(self):
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.available = True
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            self.available = False
    
    def generate_quiz_questions(self, topic, num_questions=5, difficulty='medium'):
        """Generate quiz questions based on topic"""
        if not self.available:
            return None
            
        prompt = f"""
        Generate {num_questions} multiple-choice quiz questions about {topic}.
        Difficulty level: {difficulty}.
        
        Format as JSON array with each question having:
        - question: The question text
        - options: Array of 4 options
        - correct_answer: Index of correct option (0-3)
        - explanation: Brief explanation of the answer
        
        Example format:
        [
            {{
                "question": "What is Python?",
                "options": ["A programming language", "A snake", "A car", "A country"],
                "correct_answer": 0,
                "explanation": "Python is a high-level programming language."
            }}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Parse the response as JSON
            questions = json.loads(response_text)
            return questions
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error generating quiz questions: {e}")
            
            # Check for quota limit errors
            if "quota" in error_str.lower() or "rate limit" in error_str.lower() or "429" in error_str:
                logger.error("API quota limit reached")
                return {"error": "quota_limit", "message": "API quota limit reached. Please wait a minute and try again."}
            
            logger.error(f"Response text: {response.text if 'response' in locals() else 'No response'}")
            return None
    
    def generate_assignment_feedback(self, assignment_text, rubric=None):
        """Generate feedback for student assignment"""
        if not self.available:
            return None
            
        prompt = f"""
        Provide constructive feedback for the following assignment submission.
        
        Assignment text:
        {assignment_text}
        
        {"Rubric: " + rubric if rubric else ""}
        
        Provide feedback in JSON format:
        {{
            "overall_score": 85,
            "strengths": ["Good explanation", "Clear structure"],
            "improvements": ["Add more examples", "Check grammar"],
            "detailed_feedback": "Comprehensive feedback paragraph...",
            "suggestions": ["Consider adding citations", "Expand on conclusion"]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            feedback = json.loads(response_text)
            return feedback
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            logger.error(f"Response text: {response.text if 'response' in locals() else 'No response'}")
            return None
    
    def generate_study_recommendations(self, student_performance, subjects):
        """Generate personalized study recommendations"""
        if not self.available:
            return None
            
        prompt = f"""
        Based on the following student performance data, generate personalized study recommendations.
        
        Student Performance:
        {student_performance}
        
        Subjects: {subjects}
        
        Provide recommendations in JSON format:
        {{
            "focus_areas": ["Subject1 - Topic1", "Subject2 - Topic2"],
            "study_schedule": "Suggested study schedule...",
            "resources": ["Resource1", "Resource2"],
            "tips": ["Study tip 1", "Study tip 2"],
            "improvement_plan": "Step-by-step improvement plan..."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            recommendations = json.loads(response_text)
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            logger.error(f"Response text: {response.text if 'response' in locals() else 'No response'}")
            return None
    
    def chat_with_ai(self, message, context=""):
        """AI chat assistant for students and teachers"""
        if not self.available:
            return None
            
        system_prompt = """
        You are an AI assistant for Classora LMS, a learning management system.
        You help students with their studies, answer questions about courses,
        provide explanations, and assist teachers with educational tasks.
        Be helpful, educational, and concise.
        """
        
        full_prompt = f"{system_prompt}\n\nContext: {context}\n\nUser: {message}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in AI chat: {e}")
            return None

# Initialize AI Assistant
ai_assistant = AIAssistant()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_quiz_questions(request):
    """Generate quiz questions using AI"""
    try:
        data = request.data
        topic = data.get('topic', '')
        num_questions = data.get('num_questions', 5)
        difficulty = data.get('difficulty', 'medium')
        
        if not topic:
            return Response(
                {'error': 'Topic is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        questions = ai_assistant.generate_quiz_questions(topic, num_questions, difficulty)
        
        # Check if it's a quota limit error
        if isinstance(questions, dict) and questions.get('error') == 'quota_limit':
            return Response(
                {'error': questions.get('message', 'API quota limit reached. Please wait a minute and try again.')}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        if questions:
            return Response({'questions': questions})
        else:
            return Response(
                {'error': 'Failed to generate questions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error in generate_quiz_questions: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_ai_quiz_to_course(request):
    """Save AI-generated quiz questions to a course"""
    try:
        data = request.data
        course_id = data.get('course_id')
        questions = data.get('questions', [])
        quiz_title = data.get('quiz_title', 'AI Generated Quiz')
        quiz_description = data.get('quiz_description', 'Quiz generated by AI Assistant')
        time_limit = data.get('time_limit', 30)
        
        if not course_id:
            return Response(
                {'error': 'Course ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not questions:
            return Response(
                {'error': 'Questions are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the course
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user is a teacher of this course
        if request.user.role == 'TEACHER' and request.user not in course.teachers.all():
            return Response(
                {'error': 'You are not a teacher of this course'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the quiz
        quiz = Quiz.objects.create(
            title=quiz_title,
            description=quiz_description,
            course=course,
            time_limit=time_limit,
            created_by=request.user
        )
        
        # Create questions
        created_questions = []
        for q_data in questions:
            question = Question.objects.create(
                quiz=quiz,
                text=q_data.get('question', ''),
                question_type='MCQ',
                options=q_data.get('options', []),
                correct_answer=q_data.get('correct_answer', 0),
                explanation=q_data.get('explanation', ''),
                marks=1
            )
            created_questions.append({
                'id': question.id,
                'text': question.text,
                'correct_answer': question.correct_answer
            })
        
        return Response({
            'success': True,
            'message': f'Quiz created successfully with {len(created_questions)} questions',
            'quiz_id': quiz.id,
            'quiz_title': quiz.title,
            'course_name': course.name,
            'questions_count': len(created_questions)
        })
        
    except Exception as e:
        logger.error(f"Error in save_ai_quiz_to_course: {e}")
        return Response(
            {'error': 'Failed to save quiz to course'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_assignment_feedback(request):
    """Generate assignment feedback using AI"""
    try:
        data = request.data
        assignment_text = data.get('assignment_text', '')
        rubric = data.get('rubric', '')
        
        if not assignment_text:
            return Response(
                {'error': 'Assignment text is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback = ai_assistant.generate_assignment_feedback(assignment_text, rubric)
        
        if feedback:
            return Response({'feedback': feedback})
        else:
            return Response(
                {'error': 'Failed to generate feedback'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error in generate_assignment_feedback: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_study_recommendations(request):
    """Generate study recommendations using AI"""
    try:
        data = request.data
        student_performance = data.get('student_performance', '')
        subjects = data.get('subjects', '')
        
        if not student_performance or not subjects:
            return Response(
                {'error': 'Student performance and subjects are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recommendations = ai_assistant.generate_study_recommendations(student_performance, subjects)
        
        if recommendations:
            return Response({'recommendations': recommendations})
        else:
            return Response(
                {'error': 'Failed to generate recommendations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error in generate_study_recommendations: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    """AI chat endpoint"""
    try:
        data = request.data
        message = data.get('message', '')
        context = data.get('context', '')
        
        if not message:
            return Response(
                {'error': 'Message is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response = ai_assistant.chat_with_ai(message, context)
        
        if response:
            return Response({'response': response})
        else:
            return Response(
                {'error': 'Failed to get AI response'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error in ai_chat: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def ai_status(request):
    """Check AI service status - Public endpoint"""
    return Response({
        'available': ai_assistant.available,
        'model': 'gemini-2.0-flash' if ai_assistant.available else None
    })
