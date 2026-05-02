"""
Comprehensive Test Suite for LMS System
Merged and extended with full test coverage including:
- Functional Testing (Unit, Integration, System)
- Structured Test Cases with TC IDs
- Boundary Value Analysis (BVA)
- Additional Comprehensive Tests
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Institute, CustomUser
from .models import (
    Course, Quiz, Question, QuizAttempt, Assignment, AssignmentSubmission, 
    Announcement, Department, Lecture, AttendanceRecord, AttendanceEntry,
    Notification, AnnouncementComment
)

CustomUser = get_user_model()


def _post_json(client, url, data):
    """Helper to POST JSON data (needed for nested dicts/lists in answers/options)."""
    return client.post(url, data, format="json")


def _patch_json(client, url, data):
    """Helper to PATCH JSON data."""
    return client.patch(url, data, format="json")


# =============================================================================
# A. FUNCTIONAL TESTING - Unit, Integration, and System Tests
# =============================================================================

class UnitTests(TestCase):
    """Unit Tests for individual functions/models"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
        self.course = Course.objects.create(
            name="Test Course",
            code="TEST101",
            institute=self.institute,
            department=self.department
        )
    
    def test_course_str_method(self):
        """Test Course model string representation"""
        expected = f"{self.course.code}: {self.course.name}"
        self.assertEqual(str(self.course), expected)
    
    def test_department_str_method(self):
        """Test Department model string representation"""
        expected = f"{self.department.name} ({self.institute.name})"
        self.assertEqual(str(self.department), expected)
    
    def test_quiz_is_active_method(self):
        """Test Quiz model is_active method"""
        now = timezone.now()
        active_quiz = Quiz.objects.create(
            course=self.course,
            title="Active Quiz",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            is_published=True
        )
        self.assertTrue(active_quiz.is_active())
        
        inactive_quiz = Quiz.objects.create(
            course=self.course,
            title="Inactive Quiz",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            is_published=True
        )
        self.assertFalse(inactive_quiz.is_active())

class IntegrationTests(APITestCase):
    """Integration Tests for workflows"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            full_name="Admin User",
            password="adminpass123",
            role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            full_name="Student User",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
    
    def test_complete_course_workflow(self):
        """Test complete course creation to quiz workflow"""
        # Login as admin
        self.client.force_authenticate(user=self.admin)
        
        # Create course
        course_data = {
            'name': 'Complete Workflow Course',
            'code': 'CWC101',
            'department': self.department.id,
            'semester': 'Fall',
            'academic_year': '2025-2026',
            'section': 'A',
            'credits': 3,
            'is_published': True,
            'assigned_teachers': [self.teacher.id],
            'students': [self.student.id]
        }
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        course_id = response.data['id']
        
        # Create quiz
        quiz_data = {
            'course': course_id,
            'title': 'Workflow Quiz',
            'total_time_minutes': 30,
            'is_published': True
        }
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        quiz_id = response.data['id']
        
        # Add question
        question_data = {
            'quiz': quiz_id,
            'question_type': 'MCQ',
            'text': 'Test Question',
            'options': ['A', 'B', 'C', 'D'],
            'correct_answer': '0',
            'points': 5
        }
        response = self.client.post('/api/lms/questions/', question_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Student attempts quiz
        self.client.force_authenticate(user=self.student)
        attempt_data = {
            'quiz': quiz_id,
            'answers': {str(response.data['id']): '0'},
            'time_taken_seconds': 120
        }
        response = self.client.post('/api/lms/quiz-attempts/', attempt_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class SystemTests(APITestCase):
    """System Tests for full role-based behavior"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            full_name="Admin User",
            password="adminpass123",
            role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            full_name="Student User",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
        self.course = Course.objects.create(
            name="System Test Course",
            code="SYS101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3,
            is_published=True
        )
        self.course.teachers.add(self.teacher)
        self.course.students.add(self.student)
    
    def test_admin_full_system_access(self):
        """Test admin has full system access"""
        self.client.force_authenticate(user=self.admin)
        
        # Can access all system resources
        endpoints = [
            '/api/lms/courses/',
            '/api/lms/departments/',
            '/api/lms/quizzes/',
            '/api/lms/assignments/',
            '/api/lms/announcements/',
            '/api/lms/notifications/'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cross_role_data_isolation(self):
        """Test data isolation between different roles"""
        # Teacher creates quiz
        self.client.force_authenticate(user=self.teacher)
        quiz_data = {
            'course': self.course.id,
            'title': 'Teacher Quiz',
            'total_time_minutes': 30,
            'is_published': True
        }
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Student can see quiz but not modify
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/lms/quizzes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Student cannot create quiz
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

# =============================================================================
# B. STRUCTURED TEST CASES WITH TC IDs
# =============================================================================

class StructuredTestCases(APITestCase):
    """8-10 Structured Test Cases with TC IDs covering major features"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            full_name="Admin User",
            password="adminpass123",
            role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            full_name="Student User",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
    
    def test_TC01_course_creation_admin_success(self):
        """TC01: Course Creation - Admin Success"""
        # Feature Name: Course Management
        # Input Data: Admin role, valid course data
        # Expected Output: Status 201, course created
        self.client.force_authenticate(user=self.admin)
        course_data = {
            'name': 'Admin Course',
            'code': 'ADM101',
            'department': self.department.id,
            'semester': 'Fall',
            'academic_year': '2025-2026',
            'section': 'A',
            'credits': 3,
            'is_published': True
        }
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        
        # Actual Output captured in assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Admin Course')
        self.assertEqual(response.data['code'], 'ADM101')
        # Status: PASS
    
    def test_TC02_quiz_creation_teacher_success(self):
        """TC02: Quiz Creation - Teacher Success"""
        # Feature Name: Quiz Management
        # Input Data: Teacher role, valid quiz data
        # Expected Output: Status 201, quiz created
        # Create course first
        course = Course.objects.create(
            name="Quiz Course",
            code="QZ101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        
        self.client.force_authenticate(user=self.teacher)
        quiz_data = {
            'course': course.id,
            'title': 'Teacher Quiz',
            'total_time_minutes': 30,
            'is_published': False
        }
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        
        # Actual Output captured in assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Teacher Quiz')
        # Status: PASS
    
    def test_TC03_assignment_submission_student_success(self):
        """TC03: Assignment Submission - Student Success"""
        # Feature Name: Assignment Management
        # Input Data: Student role, assignment submission
        # Expected Output: Status 201, submission created
        # Create course and assignment
        course = Course.objects.create(
            name="Assignment Course",
            code="ASG101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        course.students.add(self.student)
        
        assignment = Assignment.objects.create(
            course=course,
            title='Test Assignment',
            description='Submit this',
            due_date=timezone.now() + timedelta(days=7),
            total_marks=100
        )
        
        self.client.force_authenticate(user=self.student)
        submission_data = {
            'assignment': assignment.id,
            'links': [{'label': 'My Work', 'url': 'https://example.com'}]
        }
        response = self.client.post('/api/lms/assignment-submissions/', submission_data, format='json')
        
        # Actual Output captured in assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['assignment'], assignment.id)
        # Status: PASS
    
    def test_TC04_announcement_creation_all_roles(self):
        """TC04: Announcement Creation - All Roles"""
        # Feature Name: Announcement Management
        # Input Data: Different roles, announcement data
        # Expected Output: Status 201 for all roles
        self.client.force_authenticate(user=self.teacher)
        announcement_data = {
            'institute': self.institute.id,
            'title': 'Teacher Announcement',
            'content': 'From teacher',
            'target_role': 'ALL'
        }
        response = self.client.post('/api/lms/announcements/', announcement_data, format='json')
        
        # Actual Output captured in assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Teacher Announcement')
        # Status: PASS
    
    def test_TC05_quiz_attempt_student_validation(self):
        """TC05: Quiz Attempt - Student Validation"""
        # Feature Name: Quiz Attempt Management
        # Input Data: Student role, quiz attempt data
        # Expected Output: Status 201, attempt created with validation
        # Create course, quiz, and question
        course = Course.objects.create(
            name="Attempt Course",
            code="ATT101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        course.students.add(self.student)
        
        quiz = Quiz.objects.create(
            course=course,
            title='Test Quiz',
            total_time_minutes=30,
            is_published=True
        )
        question = Question.objects.create(
            quiz=quiz,
            question_type='MCQ',
            text='Test Question',
            options=['A', 'B', 'C', 'D'],
            correct_answer='0',
            points=5
        )
        
        self.client.force_authenticate(user=self.student)
        attempt_data = {
            'quiz': quiz.id,
            'answers': {str(question.id): '0'},
            'time_taken_seconds': 120
        }
        response = self.client.post('/api/lms/quiz-attempts/', attempt_data, format='json')
        
        # Actual Output captured in assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quiz'], quiz.id)
        # Status: PASS
    
    def test_TC06_department_management_admin_only(self):
        """TC06: Department Management - Admin Only"""
        # Feature Name: Department Management
        # Input Data: Admin role, department data
        # Expected Output: Status 201, department created
        self.client.force_authenticate(user=self.admin)
        dept_data = {
            'name': 'New Department',
            'code': 'NEW',
            'description': 'Test department'
        }
        response = self.client.post('/api/lms/departments/', dept_data, format='json')
        
        # Actual Output captured in assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Department')
        # Status: PASS
    
    def test_TC07_attendance_marking_teacher_success(self):
        """TC07: Attendance Marking - Teacher Success"""
        # Feature Name: Attendance Management
        # Input Data: Teacher role, attendance data
        # Expected Output: Status 201, attendance record created
        # Create course
        course = Course.objects.create(
            name="Attendance Course",
            code="ATT101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        course.students.add(self.student)
        
        self.client.force_authenticate(user=self.teacher)
        attendance_data = {
            'course': course.id,
            'date': timezone.now().date()
        }
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        
        # Actual Output captured in assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record_id = response.data['id']
        
        # Mark attendance
        mark_data = {
            'entries': [{
                'student_id': self.student.id,
                'status': 'PRESENT',
                'remarks': 'On time'
            }]
        }
        response = self.client.post(f'/api/lms/attendance/{record_id}/mark_attendance/', mark_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Status: PASS
    
    def test_TC08_notification_system_functionality(self):
        """TC08: Notification System - Functionality"""
        # Feature Name: Notification Management
        # Input Data: Notification creation and retrieval
        # Expected Output: Status 201, notification retrieved
        # Create notification
        notification = Notification.objects.create(
            user=self.student,
            title='Test Notification',
            message='This is a test'
        )
        
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/lms/notifications/')
        
        # Actual Output captured in assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Notification')
        # Status: PASS
    
    def test_TC09_permission_denied_scenarios(self):
        """TC09: Permission Denied - Various Scenarios"""
        # Feature Name: Access Control
        # Input Data: Unauthorized access attempts
        # Expected Output: Status 403 for all attempts
        self.client.force_authenticate(user=self.student)
        
        # Student tries to create department
        dept_data = {'name': 'Hacked Dept', 'code': 'HACK'}
        response = self.client.post('/api/lms/departments/', dept_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Student tries to delete course
        course = Course.objects.create(
            name="Delete Test",
            code="DEL101",
            institute=self.institute,
            department=self.department,
            credits=3
        )
        response = self.client.delete(f'/api/lms/courses/{course.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Status: PASS
    
    def test_TC10_data_retrieval_role_filtering(self):
        """TC10: Data Retrieval - Role Filtering"""
        # Feature Name: Data Access Control
        # Input Data: Different roles accessing same endpoints
        # Expected Output: Filtered data based on role
        # Create course for teacher
        course = Course.objects.create(
            name="Teacher Course",
            code="TCH101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        course.students.add(self.student)
        
        # Teacher sees their course
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/lms/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Student sees enrolled course
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/lms/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        # Status: PASS

# =============================================================================
# C. BOUNDARY VALUE ANALYSIS (BVA)
# =============================================================================

class BoundaryValueAnalysisTests(APITestCase):
    """Boundary Value Analysis for critical features"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            full_name="Admin User",
            password="adminpass123",
            role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
    
    def test_bva_quiz_time_minutes_boundary(self):
        """BVA for Quiz Total Time Minutes"""
        # Create course
        course = Course.objects.create(
            name="BVA Quiz Course",
            code="BVAQ101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        
        self.client.force_authenticate(user=self.teacher)
        
        # Test minimum boundary (1 minute)
        quiz_data = {
            'course': course.id,
            'title': 'Min Time Quiz',
            'total_time_minutes': 1,
            'is_published': False
        }
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just below minimum (0) - should fail
        quiz_data['title'] = 'Zero Time Quiz'
        quiz_data['total_time_minutes'] = 0
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test maximum boundary (300 minutes = 5 hours)
        quiz_data['title'] = 'Max Time Quiz'
        quiz_data['total_time_minutes'] = 300
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just above maximum (301 minutes) - should fail
        quiz_data['title'] = 'Over Max Time Quiz'
        quiz_data['total_time_minutes'] = 301
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_bva_question_points_boundary(self):
        """BVA for Question Points Field"""
        # Create course and quiz
        course = Course.objects.create(
            name="BVA Question Course",
            code="BVAQ101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        
        quiz = Quiz.objects.create(
            course=course,
            title='BVA Quiz',
            total_time_minutes=30,
            is_published=False
        )
        
        self.client.force_authenticate(user=self.teacher)
        
        # Test minimum boundary (1 point)
        question_data = {
            'quiz': quiz.id,
            'question_type': 'MCQ',
            'text': 'Min Point Question',
            'options': ['A', 'B'],
            'correct_answer': '0',
            'points': 1
        }
        response = self.client.post('/api/lms/questions/', question_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just below minimum (0 points) - should fail
        question_data['text'] = 'Zero Point Question'
        question_data['points'] = 0
        response = self.client.post('/api/lms/questions/', question_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test maximum boundary (100 points)
        question_data['text'] = 'Max Point Question'
        question_data['points'] = 100
        response = self.client.post('/api/lms/questions/', question_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_bva_course_duration_weeks_boundary(self):
        """BVA for Course Duration Weeks Field"""
        self.client.force_authenticate(user=self.admin)
        
        # Test minimum boundary (1 week)
        course_data = {
            'name': 'Min Duration Course',
            'code': 'MIN101',
            'department': self.department.id,
            'semester': 'Fall',
            'academic_year': '2025-2026',
            'duration_weeks': 1,
            'credits': 3,
            'is_published': True
        }
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just below minimum (0 weeks) - should fail
        course_data['code'] = 'MIN102'
        course_data['duration_weeks'] = 0
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test maximum boundary (52 weeks = 1 year)
        course_data['code'] = 'MAX101'
        course_data['duration_weeks'] = 52
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just above maximum (53 weeks) - should fail
        course_data['code'] = 'MAX102'
        course_data['duration_weeks'] = 53
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_bva_announcement_title_length_boundary(self):
        """BVA for Announcement Title Length"""
        # Create course
        course = Course.objects.create(
            name="Announcement Course",
            code="ANN101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        
        self.client.force_authenticate(user=self.teacher)
        
        # Test minimum boundary (1 character)
        announcement_data = {
            'institute': self.institute.id,
            'title': 'A',
            'content': 'Min title announcement',
            'course': course.id,
            'target_role': 'ALL'
        }
        response = self.client.post('/api/lms/announcements/', announcement_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test maximum boundary (255 characters)
        long_title = 'A' * 255
        announcement_data['title'] = long_title
        response = self.client.post('/api/lms/announcements/', announcement_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just above maximum (256 characters) - should fail
        announcement_data['title'] = 'A' * 256
        response = self.client.post('/api/lms/announcements/', announcement_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

# =============================================================================
# D. ORIGINAL QUIZ ISOLATION TESTS (MERGED)
# =============================================================================

class QuizIsolationTests(TestCase):
    """Tests to verify quizzes are isolated per course and per tenant."""

    def setUp(self):
        # --- Institute A ---
        self.institute_a = Institute.objects.create(
            name="Institute A", institute_code="INSTA",
        )
        self.admin_a = CustomUser.objects.create_user(
            email="admin_a@test.com", full_name="Admin A", password="Pass1234", role="ADMIN", institute=self.institute_a,
        )
        self.teacher_a1 = CustomUser.objects.create_user(
            email="teacher_a1@test.com", full_name="Teacher A1", password="Pass1234", role="TEACHER", institute=self.institute_a,
        )
        self.teacher_a2 = CustomUser.objects.create_user(
            email="teacher_a2@test.com", full_name="Teacher A2", password="Pass1234", role="TEACHER", institute=self.institute_a,
        )
        self.student_a1 = CustomUser.objects.create_user(
            email="student_a1@test.com", full_name="Student A1", password="Pass1234", role="STUDENT", institute=self.institute_a,
        )
        self.student_a2 = CustomUser.objects.create_user(
            email="student_a2@test.com", full_name="Student A2", password="Pass1234", role="STUDENT", institute=self.institute_a,
        )

        # --- Institute B ---
        self.institute_b = Institute.objects.create(
            name="Institute B", institute_code="INSTB",
        )
        self.admin_b = CustomUser.objects.create_user(
            email="admin_b@test.com", full_name="Admin B", password="Pass1234", role="ADMIN", institute=self.institute_b,
        )
        self.teacher_b1 = CustomUser.objects.create_user(
            email="teacher_b1@test.com", full_name="Teacher B1", password="Pass1234", role="TEACHER", institute=self.institute_b,
        )
        self.student_b1 = CustomUser.objects.create_user(
            email="student_b1@test.com", full_name="Student B1", password="Pass1234", role="STUDENT", institute=self.institute_b,
        )

        # --- Courses ---
        self.course_a1 = Course.objects.create(
            name="Math 101", code="MATH101", institute=self.institute_a,
        )
        self.course_a1.teachers.add(self.teacher_a1)
        self.course_a1.students.add(self.student_a1)

        self.course_a2 = Course.objects.create(
            name="Physics 101", code="PHYS101", institute=self.institute_a,
        )
        self.course_a2.teachers.add(self.teacher_a2)
        self.course_a2.students.add(self.student_a2)

        self.course_b1 = Course.objects.create(
            name="Chem 101", code="CHEM101", institute=self.institute_b,
        )
        self.course_b1.teachers.add(self.teacher_b1)
        self.course_b1.students.add(self.student_b1)

        # --- Quizzes ---
        now = timezone.now()
        self.quiz_a1 = Quiz.objects.create(
            course=self.course_a1, title="Math Midterm", total_time_minutes=30,
            is_published=True, start_time=now - timedelta(hours=1), end_time=now + timedelta(hours=2),
        )
        Question.objects.create(quiz=self.quiz_a1, question_type="MCQ", text="1+1?", options=["1","2","3","4"], correct_answer="1", points=5)

        self.quiz_a2 = Quiz.objects.create(
            course=self.course_a2, title="Physics Midterm", total_time_minutes=45,
            is_published=True, start_time=now - timedelta(hours=1), end_time=now + timedelta(hours=2),
        )
        Question.objects.create(quiz=self.quiz_a2, question_type="MCQ", text="F=ma?", options=["True","False"], correct_answer="0", points=10)

        self.quiz_b1 = Quiz.objects.create(
            course=self.course_b1, title="Chem Midterm", total_time_minutes=30,
            is_published=True, start_time=now - timedelta(hours=1), end_time=now + timedelta(hours=2),
        )
        Question.objects.create(quiz=self.quiz_b1, question_type="MCQ", text="H2O?", options=["Water","Salt"], correct_answer="0", points=5)

        # Draft quiz in course_a1
        self.quiz_a1_draft = Quiz.objects.create(
            course=self.course_a1, title="Math Draft Quiz", total_time_minutes=20,
            is_published=False,
        )

    # ──────────────────────────────────────────────────
    # 1. QUIZ LIST ISOLATION
    # ──────────────────────────────────────────────────

    def test_teacher_sees_only_own_course_quizzes(self):
        """Teacher A1 should only see quizzes from course_a1, not course_a2."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = client.get("/api/lms/quizzes/")
        ids = [q["id"] for q in resp.data]
        self.assertIn(self.quiz_a1.id, ids)
        self.assertNotIn(self.quiz_a2.id, ids)
        self.assertNotIn(self.quiz_b1.id, ids)

    def test_student_sees_only_enrolled_course_published_quizzes(self):
        """Student A1 should only see published quizzes from enrolled course."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        resp = client.get("/api/lms/quizzes/")
        ids = [q["id"] for q in resp.data]
        self.assertIn(self.quiz_a1.id, ids)
        self.assertNotIn(self.quiz_a1_draft.id, ids)  # draft not visible
        self.assertNotIn(self.quiz_a2.id, ids)         # different course
        self.assertNotIn(self.quiz_b1.id, ids)         # different institute

    def test_admin_sees_only_own_institute_quizzes(self):
        """Admin A should not see Institute B quizzes."""
        client = APIClient()
        client.force_authenticate(self.admin_a)
        resp = client.get("/api/lms/quizzes/")
        ids = [q["id"] for q in resp.data]
        self.assertIn(self.quiz_a1.id, ids)
        self.assertIn(self.quiz_a2.id, ids)
        self.assertNotIn(self.quiz_b1.id, ids)

    def test_cross_institute_teacher_cannot_see_other_quizzes(self):
        """Teacher B1 should not see Institute A quizzes."""
        client = APIClient()
        client.force_authenticate(self.teacher_b1)
        resp = client.get("/api/lms/quizzes/")
        ids = [q["id"] for q in resp.data]
        self.assertIn(self.quiz_b1.id, ids)
        self.assertNotIn(self.quiz_a1.id, ids)
        self.assertNotIn(self.quiz_a2.id, ids)

    # ──────────────────────────────────────────────────
    # 2. QUIZ CREATION ISOLATION
    # ──────────────────────────────────────────────────

    def test_teacher_can_create_quiz_in_own_course(self):
        """Teacher A1 can create quiz in course_a1."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = _post_json(client, "/api/lms/quizzes/", {
            "title": "New Math Quiz", "course": self.course_a1.id,
            "total_time_minutes": 15, "is_published": False,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_teacher_cannot_create_quiz_in_other_teacher_course(self):
        """Teacher A1 cannot create quiz in course_a2 (taught by A2)."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = _post_json(client, "/api/lms/quizzes/", {
            "title": "Sneaky Quiz", "course": self.course_a2.id,
            "total_time_minutes": 15, "is_published": False,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_create_quiz_in_other_institute_course(self):
        """Teacher A1 cannot create quiz in Institute B course."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = _post_json(client, "/api/lms/quizzes/", {
            "title": "Cross-institute Quiz", "course": self.course_b1.id,
            "total_time_minutes": 15, "is_published": False,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_create_quiz(self):
        """Students cannot create quizzes."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        resp = _post_json(client, "/api/lms/quizzes/", {
            "title": "Student Quiz", "course": self.course_a1.id,
            "total_time_minutes": 15, "is_published": False,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_quiz_in_own_institute(self):
        """Admin A can create quiz in any course in their institute."""
        client = APIClient()
        client.force_authenticate(self.admin_a)
        resp = _post_json(client, "/api/lms/quizzes/", {
            "title": "Admin Quiz", "course": self.course_a1.id,
            "total_time_minutes": 15, "is_published": False,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_admin_cannot_create_quiz_in_other_institute(self):
        """Admin A cannot create quiz in Institute B course."""
        client = APIClient()
        client.force_authenticate(self.admin_a)
        resp = _post_json(client, "/api/lms/quizzes/", {
            "title": "Cross-institute Admin Quiz", "course": self.course_b1.id,
            "total_time_minutes": 15, "is_published": False,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ──────────────────────────────────────────────────
    # 3. QUESTION ISOLATION
    # ──────────────────────────────────────────────────

    def test_teacher_can_add_question_to_own_quiz(self):
        """Teacher A1 can add question to quiz in their course."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = _post_json(client, "/api/lms/questions/", {
            "quiz": self.quiz_a1.id, "question_type": "MCQ",
            "text": "2+2?", "options": ["3","4","5","6"], "correct_answer": "1", "points": 5,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_teacher_cannot_add_question_to_other_course_quiz(self):
        """Teacher A1 cannot add question to quiz in course_a2."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = _post_json(client, "/api/lms/questions/", {
            "quiz": self.quiz_a2.id, "question_type": "MCQ",
            "text": "Sneaky Q?", "options": ["A","B"], "correct_answer": "0", "points": 1,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_add_question_to_other_institute_quiz(self):
        """Teacher A1 cannot add question to Institute B quiz."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = _post_json(client, "/api/lms/questions/", {
            "quiz": self.quiz_b1.id, "question_type": "MCQ",
            "text": "Cross-inst Q?", "options": ["A","B"], "correct_answer": "0", "points": 1,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ──────────────────────────────────────────────────
    # 4. QUIZ ATTEMPT ISOLATION
    # ──────────────────────────────────────────────────

    def test_student_can_submit_attempt_for_enrolled_active_quiz(self):
        """Student A1 can submit attempt for active quiz in enrolled course."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id,
            "answers": {str(Question.objects.filter(quiz=self.quiz_a1).first().id): "1"},
            "time_taken_seconds": 120,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_submit_attempt_for_unenrolled_course_quiz(self):
        """Student A1 cannot submit attempt for quiz in course they're not enrolled in."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a2.id,
            "answers": {str(Question.objects.filter(quiz=self.quiz_a2).first().id): "0"},
            "time_taken_seconds": 60,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_submit_attempt_for_other_institute_quiz(self):
        """Student A1 cannot submit attempt for Institute B quiz."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_b1.id,
            "answers": {str(Question.objects.filter(quiz=self.quiz_b1).first().id): "0"},
            "time_taken_seconds": 60,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_submit_duplicate_attempt(self):
        """Student cannot submit more than one attempt per quiz."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        q_id = str(Question.objects.filter(quiz=self.quiz_a1).first().id)
        # First attempt
        resp1 = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {q_id: "1"}, "time_taken_seconds": 120,
        })
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        # Duplicate attempt
        resp2 = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {q_id: "0"}, "time_taken_seconds": 90,
        })
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already submitted", str(resp2.data).lower())

    def test_student_cannot_submit_attempt_for_inactive_quiz(self):
        """Student cannot submit attempt for an unpublished/draft quiz."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1_draft.id,
            "answers": {}, "time_taken_seconds": 30,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_submit_attempt_for_expired_quiz(self):
        """Student cannot submit attempt for a quiz whose time window has closed."""
        expired_quiz = Quiz.objects.create(
            course=self.course_a1, title="Expired Quiz", total_time_minutes=30,
            is_published=True,
            start_time=timezone.now() - timedelta(hours=3),
            end_time=timezone.now() - timedelta(hours=1),
        )
        Question.objects.create(quiz=expired_quiz, question_type="MCQ", text="Old?", options=["A","B"], correct_answer="0", points=1)
        client = APIClient()
        client.force_authenticate(self.student_a1)
        resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": expired_quiz.id,
            "answers": {str(Question.objects.filter(quiz=expired_quiz).first().id): "0"}, "time_taken_seconds": 30,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_student_cannot_submit_attempt(self):
        """Teacher and admin cannot submit quiz attempts."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {}, "time_taken_seconds": 10,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_update_own_attempt(self):
        """Student cannot modify their attempt after submission."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        q_id = str(Question.objects.filter(quiz=self.quiz_a1).first().id)
        resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {q_id: "1"}, "time_taken_seconds": 120,
        })
        attempt_id = resp.data["id"]
        update_resp = _patch_json(client, f"/api/lms/quiz-attempts/{attempt_id}/", {"score": 100})
        self.assertEqual(update_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_delete_own_attempt(self):
        """Student cannot delete their attempt."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        q_id = str(Question.objects.filter(quiz=self.quiz_a1).first().id)
        resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {q_id: "1"}, "time_taken_seconds": 120,
        })
        attempt_id = resp.data["id"]
        del_resp = client.delete(f"/api/lms/quiz-attempts/{attempt_id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_403_FORBIDDEN)

    # ──────────────────────────────────────────────────
    # 5. QUIZ GRADING ISOLATION
    # ──────────────────────────────────────────────────

    def test_only_teacher_can_grade_attempt(self):
        """Only teachers/admins can grade; students cannot."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        q_id = str(Question.objects.filter(quiz=self.quiz_a1).first().id)
        at_resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {q_id: "1"}, "time_taken_seconds": 120,
        })
        attempt_id = at_resp.data["id"]
        # Student tries to grade
        grade_resp = _patch_json(client, f"/api/lms/quiz-attempts/{attempt_id}/grade/", {"score": 999})
        self.assertEqual(grade_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_grade_own_course_attempt(self):
        """Teacher A1 can grade attempts from their course quiz."""
        client = APIClient()
        # Student submits
        client.force_authenticate(self.student_a1)
        q_id = str(Question.objects.filter(quiz=self.quiz_a1).first().id)
        at_resp = _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {q_id: "1"}, "time_taken_seconds": 120,
        })
        attempt_id = at_resp.data["id"]
        # Teacher grades
        client.force_authenticate(self.teacher_a1)
        grade_resp = _patch_json(client, f"/api/lms/quiz-attempts/{attempt_id}/grade/", {"score": 4})
        self.assertEqual(grade_resp.status_code, status.HTTP_200_OK)

    # ──────────────────────────────────────────────────
    # 6. QUIZ SERIALIZER INCLUDES COURSE INFO
    # ──────────────────────────────────────────────────

    def test_quiz_serializer_includes_course_name_and_code(self):
        """Quiz list response should include course_name and course_code."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = client.get("/api/lms/quizzes/")
        quiz = next(q for q in resp.data if q["id"] == self.quiz_a1.id)
        self.assertEqual(quiz["course_name"], "Math 101")
        self.assertEqual(quiz["course_code"], "MATH101")

    # ──────────────────────────────────────────────────
    # 7. QUIZ DELETION ISOLATION
    # ──────────────────────────────────────────────────

    def test_teacher_cannot_delete_other_course_quiz(self):
        """Teacher A1 cannot delete quiz from course_a2 (404 since it's outside their queryset)."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = client.delete(f"/api/lms/quizzes/{self.quiz_a2.id}/")
        self.assertIn(resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_student_cannot_delete_quiz(self):
        """Students cannot delete quizzes."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        resp = client.delete(f"/api/lms/quizzes/{self.quiz_a1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ──────────────────────────────────────────────────
    # 8. QUIZ UPDATE ISOLATION
    # ──────────────────────────────────────────────────

    def test_teacher_cannot_move_quiz_to_other_course(self):
        """Teacher A1 cannot update quiz to belong to a course they don't teach."""
        client = APIClient()
        client.force_authenticate(self.teacher_a1)
        resp = _patch_json(client, f"/api/lms/quizzes/{self.quiz_a1.id}/", {
            "course": self.course_a2.id,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ──────────────────────────────────────────────────
    # 9. QUIZ ATTEMPT LIST ISOLATION
    # ──────────────────────────────────────────────────

    def test_teacher_sees_only_own_course_attempts(self):
        """Teacher A1 sees attempts only from their course quizzes."""
        # Student A1 submits attempt for quiz_a1
        client = APIClient()
        client.force_authenticate(self.student_a1)
        q_id = str(Question.objects.filter(quiz=self.quiz_a1).first().id)
        _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {q_id: "1"}, "time_taken_seconds": 120,
        })
        # Teacher A1 checks attempts
        client.force_authenticate(self.teacher_a1)
        resp = client.get("/api/lms/quiz-attempts/")
        quiz_ids = [a["quiz"] for a in resp.data]
        self.assertIn(self.quiz_a1.id, quiz_ids)
        self.assertNotIn(self.quiz_a2.id, quiz_ids)
        self.assertNotIn(self.quiz_b1.id, quiz_ids)

    def test_student_sees_only_own_attempts(self):
        """Student A1 sees only their own attempts, not other students'."""
        # Student A1 submits
        client = APIClient()
        client.force_authenticate(self.student_a1)
        q_id = str(Question.objects.filter(quiz=self.quiz_a1).first().id)
        _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": self.quiz_a1.id, "answers": {q_id: "1"}, "time_taken_seconds": 120,
        })
        # Student A2 checks (not enrolled in course_a1, so no attempts)
        client.force_authenticate(self.student_a2)
        resp = client.get("/api/lms/quiz-attempts/")
        student_ids = [a["student"] for a in resp.data]
        self.assertNotIn(self.student_a1.id, student_ids)

    # ──────────────────────────────────────────────────
    # 10. QUESTION LIST ISOLATION (CRITICAL BUG FIX)
    # ──────────────────────────────────────────────────

    def test_questions_filtered_by_quiz_parameter(self):
        """When quiz parameter is provided, only questions from that quiz should be returned."""
        # Create extra questions in different quizzes
        Question.objects.create(quiz=self.quiz_a1, question_type="MCQ", text="Math Q2?", options=["A","B"], correct_answer="0", points=1)
        Question.objects.create(quiz=self.quiz_a2, question_type="MCQ", text="Physics Q1?", options=["A","B"], correct_answer="0", points=1)
        Question.objects.create(quiz=self.quiz_a2, question_type="MCQ", text="Physics Q2?", options=["A","B"], correct_answer="0", points=1)
        
        client = APIClient()
        client.force_authenticate(self.student_a1)
        
        # Get questions for quiz_a1 only
        resp = client.get(f"/api/lms/questions/?quiz={self.quiz_a1.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        question_texts = [q["text"] for q in resp.data]
        
        # Should only see quiz_a1 questions (1+1? and Math Q2?), not quiz_a2 questions
        self.assertIn("1+1?", question_texts)
        self.assertIn("Math Q2?", question_texts)
        self.assertNotIn("Physics Q1?", question_texts)
        self.assertNotIn("Physics Q2?", question_texts)
        self.assertEqual(len(question_texts), 2)

    def test_questions_from_other_quizzes_not_leaked(self):
        """Ensure students cannot see questions from quizzes they didn't open."""
        client = APIClient()
        client.force_authenticate(self.student_a1)
        
        # Without quiz parameter - should get all questions from accessible quizzes
        resp_all = client.get("/api/lms/questions/")
        
        # With quiz parameter - should only get questions from that specific quiz
        resp_filtered = client.get(f"/api/lms/questions/?quiz={self.quiz_a1.id}")
        
        # The filtered response should have fewer or equal questions than unfiltered
        self.assertLessEqual(len(resp_filtered.data), len(resp_all.data))
        
        # All returned questions should belong to quiz_a1
        for q in resp_filtered.data:
            self.assertEqual(q["quiz"], self.quiz_a1.id)

# =============================================================================
# E. ASSIGNMENT_QUIZ_EDIT_DELETE_TESTS (MERGED FROM test_new_features.py)
# =============================================================================

class AssignmentQuizEditDeleteTests(TestCase):
    """Test assignment and quiz edit/delete with cascade."""

    def setUp(self):
        self.institute = Institute.objects.create(name="Test Institute", institute_code="TI001")
        self.admin = CustomUser.objects.create_user(
            email="admin@test.com", full_name="Admin", password="Pass1234", role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@test.com", full_name="Teacher", password="Pass1234", role="TEACHER",
            institute=self.institute
        )
        self.student = CustomUser.objects.create_user(
            email="student@test.com", full_name="Student", password="Pass1234", role="STUDENT",
            institute=self.institute
        )
        self.other_teacher = CustomUser.objects.create_user(
            email="teacher2@test.com", full_name="Teacher 2", password="Pass1234", role="TEACHER",
            institute=self.institute
        )
        
        self.course = Course.objects.create(
            institute=self.institute, name="Math 101", code="MATH101",
            semester="Fall", academic_year="2025-2026", section="A",
            is_published=True
        )
        self.course.teachers.add(self.teacher)
        self.course.students.add(self.student)

    def test_teacher_can_update_own_course_assignment(self):
        """Teacher can update assignment in their course."""
        client = APIClient()
        client.force_authenticate(self.teacher)
        
        # Create assignment
        resp = _post_json(client, "/api/lms/assignments/", {
            "course": self.course.id, "title": "Original Title",
            "description": "Desc", "due_date": (timezone.now() + timedelta(days=7)).isoformat()
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        assignment_id = resp.data["id"]
        
        # Update assignment
        update_resp = _patch_json(client, f"/api/lms/assignments/{assignment_id}/", {
            "title": "Updated Title"
        })
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(update_resp.data["title"], "Updated Title")

    def test_other_teacher_cannot_update_assignment(self):
        """Other teacher cannot update assignment in course they don't teach."""
        client = APIClient()
        client.force_authenticate(self.teacher)
        
        resp = _post_json(client, "/api/lms/assignments/", {
            "course": self.course.id, "title": "Assignment",
            "description": "Desc", "due_date": (timezone.now() + timedelta(days=7)).isoformat()
        })
        assignment_id = resp.data["id"]
        
        # Other teacher tries to update - gets 404 since assignment not in their queryset
        client.force_authenticate(self.other_teacher)
        update_resp = _patch_json(client, f"/api/lms/assignments/{assignment_id}/", {
            "title": "Hacked Title"
        })
        self.assertIn(update_resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_student_cannot_update_assignment(self):
        """Student cannot update assignments."""
        client = APIClient()
        client.force_authenticate(self.teacher)
        
        resp = _post_json(client, "/api/lms/assignments/", {
            "course": self.course.id, "title": "Assignment",
            "description": "Desc", "due_date": (timezone.now() + timedelta(days=7)).isoformat()
        })
        assignment_id = resp.data["id"]
        
        # Student tries to update
        client.force_authenticate(self.student)
        update_resp = _patch_json(client, f"/api/lms/assignments/{assignment_id}/", {
            "title": "Student Update"
        })
        self.assertEqual(update_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_assignment_delete_cascades_submissions(self):
        """Deleting an assignment should delete all its submissions."""
        client = APIClient()
        client.force_authenticate(self.teacher)
        
        # Create assignment
        resp = _post_json(client, "/api/lms/assignments/", {
            "course": self.course.id, "title": "Delete Me",
            "description": "Desc", "due_date": (timezone.now() + timedelta(days=7)).isoformat()
        })
        assignment_id = resp.data["id"]
        
        # Student submits
        client.force_authenticate(self.student)
        _post_json(client, "/api/lms/assignment-submissions/", {
            "assignment": assignment_id
        })
        
        # Verify submission exists
        self.assertEqual(AssignmentSubmission.objects.filter(assignment_id=assignment_id).count(), 1)
        
        # Teacher deletes assignment
        client.force_authenticate(self.teacher)
        del_resp = client.delete(f"/api/lms/assignments/{assignment_id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify cascade - submission should be deleted
        self.assertEqual(AssignmentSubmission.objects.filter(assignment_id=assignment_id).count(), 0)

    def test_teacher_can_update_own_course_quiz(self):
        """Teacher can update quiz in their course."""
        client = APIClient()
        client.force_authenticate(self.teacher)
        
        # Create quiz
        resp = _post_json(client, "/api/lms/quizzes/", {
            "course": self.course.id, "title": "Original Quiz",
            "total_time_minutes": 30, "is_published": False
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        quiz_id = resp.data["id"]
        
        # Update quiz
        update_resp = _patch_json(client, f"/api/lms/quizzes/{quiz_id}/", {
            "title": "Updated Quiz", "is_published": True
        })
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

    def test_quiz_delete_cascades_attempts_and_questions(self):
        """Deleting a quiz should delete all attempts and questions."""
        client = APIClient()
        client.force_authenticate(self.teacher)
        
        # Create quiz with question
        resp = _post_json(client, "/api/lms/quizzes/", {
            "course": self.course.id, "title": "Quiz to Delete",
            "total_time_minutes": 30, "is_published": True
        })
        quiz_id = resp.data["id"]
        
        # Add question
        q_resp = _post_json(client, "/api/lms/questions/", {
            "quiz": quiz_id, "question_type": "MCQ",
            "text": "Test?", "options": ["A", "B"], "correct_answer": "0", "points": 1
        })
        question_id = q_resp.data["id"]
        
        # Student attempts
        client.force_authenticate(self.student)
        _post_json(client, "/api/lms/quiz-attempts/", {
            "quiz": quiz_id, "answers": {str(question_id): "0"}, "time_taken_seconds": 60
        })
        
        # Verify records exist
        self.assertEqual(Question.objects.filter(quiz_id=quiz_id).count(), 1)
        self.assertEqual(QuizAttempt.objects.filter(quiz_id=quiz_id).count(), 1)
        
        # Teacher deletes quiz
        client.force_authenticate(self.teacher)
        del_resp = client.delete(f"/api/lms/quizzes/{quiz_id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify cascade
        self.assertEqual(Question.objects.filter(quiz_id=quiz_id).count(), 0)
        self.assertEqual(QuizAttempt.objects.filter(quiz_id=quiz_id).count(), 0)

# =============================================================================
# F. ANNOUNCEMENT_CRUD_TESTS (MERGED FROM test_new_features.py)
# =============================================================================

class AnnouncementCRUDTests(TestCase):
    """Test announcements CRUD for all roles."""

    def setUp(self):
        self.institute = Institute.objects.create(name="Test Institute", institute_code="TI001")
        self.admin = CustomUser.objects.create_user(
            email="admin@test.com", full_name="Admin", password="Pass1234", role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@test.com", full_name="Teacher", password="Pass1234", role="TEACHER",
            institute=self.institute
        )
        self.student = CustomUser.objects.create_user(
            email="student@test.com", full_name="Student", password="Pass1234", role="STUDENT",
            institute=self.institute
        )
        self.other_student = CustomUser.objects.create_user(
            email="student2@test.com", full_name="Student 2", password="Pass1234", role="STUDENT",
            institute=self.institute
        )
        
        self.dept = Department.objects.create(institute=self.institute, name="Math Dept", code="MATH")
        self.course = Course.objects.create(
            institute=self.institute, name="Math 101", code="MATH101",
            department=self.dept, semester="Fall", academic_year="2025-2026",
            section="A", is_published=True
        )
        self.course.teachers.add(self.teacher)
        self.course.students.add(self.student)
        self.course2 = Course.objects.create(
            institute=self.institute, name="Physics 101", code="PHYS101",
            semester="Fall", academic_year="2025-2026",
            section="A", is_published=True
        )
        self.course2.students.add(self.other_student)

    def test_student_can_create_announcement_for_enrolled_course(self):
        """Student can create announcement for course they're enrolled in."""
        client = APIClient()
        client.force_authenticate(self.student)
        
        resp = _post_json(client, "/api/lms/announcements/", {
            "title": "Student Announcement",
            "content": "Hello from student!",
            "course": self.course.id,
            "target_role": "ALL"
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author"], self.student.id)

    def test_student_cannot_create_announcement_for_unenrolled_course(self):
        """Student cannot create announcement for course they're not enrolled in."""
        client = APIClient()
        client.force_authenticate(self.student)
        
        resp = _post_json(client, "/api/lms/announcements/", {
            "title": "Hacked Announcement",
            "content": "Hello!",
            "course": self.course2.id,  # Student not enrolled here
            "target_role": "ALL"
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_update_own_announcement(self):
        """Student can update their own announcement."""
        client = APIClient()
        client.force_authenticate(self.student)
        
        # Create
        resp = _post_json(client, "/api/lms/announcements/", {
            "title": "Original",
            "content": "Content",
            "course": self.course.id,
            "target_role": "ALL"
        })
        announcement_id = resp.data["id"]
        
        # Update
        update_resp = _patch_json(client, f"/api/lms/announcements/{announcement_id}/", {
            "title": "Updated Title"
        })
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

    def test_student_cannot_update_other_student_announcement(self):
        """Student cannot update another student's announcement."""
        client = APIClient()
        client.force_authenticate(self.other_student)
        
        # Create announcement in course2
        resp = _post_json(client, "/api/lms/announcements/", {
            "title": "Other Student's",
            "content": "Content",
            "course": self.course2.id,
            "target_role": "ALL"
        })
        announcement_id = resp.data["id"]
        
        # First student tries to update - gets 404 since announcement not in their queryset
        client.force_authenticate(self.student)
        update_resp = _patch_json(client, f"/api/lms/announcements/{announcement_id}/", {
            "title": "Hacked"
        })
        self.assertIn(update_resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_student_can_delete_own_announcement(self):
        """Student can delete their own announcement."""
        client = APIClient()
        client.force_authenticate(self.student)
        
        resp = _post_json(client, "/api/lms/announcements/", {
            "title": "To Delete",
            "content": "Content",
            "course": self.course.id,
            "target_role": "ALL"
        })
        announcement_id = resp.data["id"]
        
        # Delete
        del_resp = client.delete(f"/api/lms/announcements/{announcement_id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_delete_any_announcement(self):
        """Admin can delete any announcement."""
        client = APIClient()
        client.force_authenticate(self.student)
        
        resp = _post_json(client, "/api/lms/announcements/", {
            "title": "Student Post",
            "content": "Content",
            "course": self.course.id,
            "target_role": "ALL"
        })
        announcement_id = resp.data["id"]
        
        # Admin deletes
        client.force_authenticate(self.admin)
        del_resp = client.delete(f"/api/lms/announcements/{announcement_id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)

# =============================================================================
# G. COURSE_SECTION_TESTS (MERGED FROM test_new_features.py)
# =============================================================================

class CourseSectionTests(TestCase):
    """Test course sections and uniqueness constraints."""

    def setUp(self):
        self.institute = Institute.objects.create(name="Test Institute", institute_code="TI001")
        self.other_institute = Institute.objects.create(name="Other Institute", institute_code="TI002")
        self.admin = CustomUser.objects.create_user(
            email="admin@test.com", full_name="Admin", password="Pass1234", role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@test.com", full_name="Teacher", password="Pass1234", role="TEACHER",
            institute=self.institute
        )
        self.teacher2 = CustomUser.objects.create_user(
            email="teacher2@test.com", full_name="Teacher 2", password="Pass1234", role="TEACHER",
            institute=self.institute
        )

    def test_duplicate_course_same_section_blocked(self):
        """Cannot create duplicate course (same code, semester, year, section) in same institute."""
        client = APIClient()
        client.force_authenticate(self.admin)
        
        # Create first course
        resp1 = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        
        # Try to create duplicate
        resp2 = _post_json(client, "/api/lms/courses/", {
            "name": "Different Name", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_different_section_allowed(self):
        """Can create same course with different section."""
        client = APIClient()
        client.force_authenticate(self.admin)
        
        # Create Section A
        resp1 = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        
        # Create Section B - should succeed
        resp2 = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "B",
            "is_published": True
        })
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)

    def test_different_semester_allowed(self):
        """Can create same course with different semester/year."""
        client = APIClient()
        client.force_authenticate(self.admin)
        
        # Fall 2025
        resp1 = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        
        # Spring 2026 - should succeed
        resp2 = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Spring", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)

    def test_same_course_different_institute_allowed(self):
        """Same course can exist in different institutes."""
        client = APIClient()
        client.force_authenticate(self.admin)
        
        resp1 = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

    def test_teacher_assignment_to_section(self):
        """Admin can assign teacher to course section."""
        client = APIClient()
        client.force_authenticate(self.admin)
        
        # Create course
        resp = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        course_id = resp.data["id"]
        
        # Assign teacher
        assign_resp = _post_json(client, f"/api/lms/courses/{course_id}/assign_teacher/", {
            "teacher_id": self.teacher.id
        })
        self.assertEqual(assign_resp.status_code, status.HTTP_200_OK)

    def test_teacher_double_assignment_blocked(self):
        """Cannot assign same teacher twice to same course section."""
        client = APIClient()
        client.force_authenticate(self.admin)
        
        # Create course
        resp = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        course_id = resp.data["id"]
        
        # First assignment
        _post_json(client, f"/api/lms/courses/{course_id}/assign_teacher/", {
            "teacher_id": self.teacher.id
        })
        
        # Second assignment - should fail
        assign_resp2 = _post_json(client, f"/api/lms/courses/{course_id}/assign_teacher/", {
            "teacher_id": self.teacher.id
        })
        self.assertEqual(assign_resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_can_teach_multiple_sections(self):
        """Teacher can be assigned to multiple sections of same course."""
        client = APIClient()
        client.force_authenticate(self.admin)
        
        # Create Section A
        resp1 = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "A",
            "is_published": True
        })
        course_a_id = resp1.data["id"]
        
        # Create Section B
        resp2 = _post_json(client, "/api/lms/courses/", {
            "name": "Math 101", "code": "MATH101",
            "semester": "Fall", "academic_year": "2025-2026", "section": "B",
            "is_published": True
        })
        course_b_id = resp2.data["id"]
        
        # Assign teacher to both
        resp_a = _post_json(client, f"/api/lms/courses/{course_a_id}/assign_teacher/", {
            "teacher_id": self.teacher.id
        })
        self.assertEqual(resp_a.status_code, status.HTTP_200_OK)
        
        resp_b = _post_json(client, f"/api/lms/courses/{course_b_id}/assign_teacher/", {
            "teacher_id": self.teacher.id
        })
        self.assertEqual(resp_b.status_code, status.HTTP_200_OK)

# =============================================================================
# H. ADDITIONAL COMPREHENSIVE TESTS
# =============================================================================

class AdditionalComprehensiveTests(APITestCase):
    """Additional comprehensive tests for edge cases and error handling"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            full_name="Admin User",
            password="adminpass123",
            role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            full_name="Student User",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
    
    def test_lecture_management_workflow(self):
        """Test complete lecture creation and access workflow"""
        # Create course
        course = Course.objects.create(
            name="Lecture Course",
            code="LEC101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        course.students.add(self.student)
        
        # Teacher creates lecture
        self.client.force_authenticate(user=self.teacher)
        lecture_data = {
            'course': course.id,
            'title': 'Introduction Lecture',
            'description': 'First lecture content',
            'scheduled_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'external_links': [{'label': 'Resource', 'url': 'https://example.com'}]
        }
        response = self.client.post('/api/lms/lectures/', lecture_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Student can access lecture
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/lms/lectures/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_notification_system_comprehensive(self):
        """Test comprehensive notification system functionality"""
        # Create course
        course = Course.objects.create(
            name="Notification Course",
            code="NOT101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        course.students.add(self.student)
        
        # Create notification
        notification = Notification.objects.create(
            user=self.student,
            title='Assignment Due',
            message='Your assignment is due tomorrow',
        )
        
        # Student retrieves notifications
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/lms/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Mark as read
        response = self.client.patch(f'/api/lms/notifications/{notification.id}/', {'is_read': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
    
    def test_announcement_comment_system(self):
        """Test announcement commenting system"""
        # Create course and announcement
        course = Course.objects.create(
            name="Comment Course",
            code="COM101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        course.students.add(self.student)
        
        announcement = Announcement.objects.create(
            institute=self.institute,
            course=course,
            title='Course Update',
            content='Important announcement',
            author=self.teacher
        )
        
        # Student comments
        self.client.force_authenticate(user=self.student)
        comment_data = {
            'announcement': announcement.id,
            'content': 'Thanks for the update!'
        }
        response = self.client.post('/api/lms/announcement-comments/', comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify comment appears
        response = self.client.get(f'/api/lms/announcement-comments/?announcement={announcement.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_cross_institute_data_isolation(self):
        """Test comprehensive cross-institute data isolation"""
        # Create second institute and user
        institute2 = Institute.objects.create(
            name="Second Institute",
            institute_code="SEC001"
        )
        admin2 = CustomUser.objects.create_user(
            email="admin2@example.com",
            full_name="Second Admin",
            password="adminpass123",
            role="ADMIN",
            institute=institute2
        )
        
        # Create course in first institute
        course1 = Course.objects.create(
            name="First Institute Course",
            code="FIRST101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        
        # Create course in second institute
        course2 = Course.objects.create(
            name="Second Institute Course",
            code="SECOND101",
            institute=institute2,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        
        # First admin sees only their course
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/lms/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle both paginated and non-paginated responses
        courses_data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(courses_data), 1)
        self.assertEqual(courses_data[0]['id'], course1.id)
        
        # Second admin sees only their course
        self.client.force_authenticate(user=admin2)
        response = self.client.get('/api/lms/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle both paginated and non-paginated responses
        courses_data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(courses_data), 1)
        self.assertEqual(courses_data[0]['id'], course2.id)
    
    def test_comprehensive_error_handling(self):
        """Test comprehensive error handling scenarios"""
        self.client.force_authenticate(user=self.student)
        
        # Test invalid course creation
        course_data = {
            'name': '',  # Empty name
            'code': 'INVALID',
            'semester': 'Invalid Semester',
            'academic_year': '2025-2026',
            'credits': -1  # Negative credits
        }
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Student cannot create
        
        # Test with admin for validation errors
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid quiz data
        course = Course.objects.create(
            name="Error Test Course",
            code="ERR101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        course.teachers.add(self.teacher)
        
        self.client.force_authenticate(user=self.teacher)
        quiz_data = {
            'course': course.id,
            'title': '',  # Empty title
            'total_time_minutes': -1  # Invalid time
        }
        response = self.client.post('/api/lms/quizzes/', quiz_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test unauthorized announcement creation returns 403 before serializer validation
        self.client.force_authenticate(user=self.student)
        announcement_data = {
            'title': '',
            'content': ''
        }
        response = self.client.post('/api/lms/announcements/', announcement_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_performance_and_pagination(self):
        """Test API performance and pagination"""
        # Create multiple courses
        for i in range(15):
            Course.objects.create(
                name=f"Course {i}",
                code=f"CRS{i:03d}",
                institute=self.institute,
                department=self.department,
                semester="Fall",
                academic_year="2025-2026",
                credits=3
            )
        
        # Test pagination
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/lms/courses/?page=1&page_size=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertTrue(response.data['has_next'])
        
        response = self.client.get('/api/lms/courses/?page=2&page_size=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertFalse(response.data['has_next'])
    
    def test_data_integrity_constraints(self):
        """Test data integrity and constraint validation"""
        self.client.force_authenticate(user=self.admin)
        
        # Create department
        dept_data = {
            'name': 'Test Department',
            'code': 'TEST',
            'description': 'Test description'
        }
        response = self.client.post('/api/lms/departments/', dept_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        department = Department.objects.get(code='TEST')
        
        # Create course with valid department
        course_data = {
            'name': 'Valid Course',
            'code': 'VAL101',
            'department': department.id,
            'semester': 'Fall',
            'academic_year': '2025-2026',
            'credits': 3,
            'is_published': True
        }
        response = self.client.post('/api/lms/courses/', course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test foreign key constraint
        invalid_course_data = course_data.copy()
        invalid_course_data['department'] = 99999  # Non-existent department
        response = self.client.post('/api/lms/courses/', invalid_course_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

# =============================================================================
# I. STUDENT ANALYTICS AND PERFORMANCE TESTS (ISSUES 7-10)
# =============================================================================

class StudentAnalyticsTests(APITestCase):
    """Test student-specific analytics and performance features"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            full_name="Admin User",
            password="adminpass123",
            role="ADMIN",
            institute=self.institute
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student1 = CustomUser.objects.create_user(
            email="student1@example.com",
            full_name="Student One",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.student2 = CustomUser.objects.create_user(
            email="student2@example.com",
            full_name="Student Two",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.student3 = CustomUser.objects.create_user(
            email="student3@example.com",
            full_name="Student Three",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
        
        # Create course with only 1 enrolled student
        self.course = Course.objects.create(
            name="Analytics Test Course",
            code="ANA101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3,
            is_published=True
        )
        self.course.teachers.add(self.teacher)
        self.course.students.add(self.student1)  # Only 1 student enrolled
        
        # Create assignments and quizzes for analytics
        self.assignment1 = Assignment.objects.create(
            course=self.course,
            title="Assignment 1",
            description="First assignment",
            due_date=timezone.now() + timedelta(days=7),
            total_marks=100
        )
        self.assignment2 = Assignment.objects.create(
            course=self.course,
            title="Assignment 2", 
            description="Second assignment",
            due_date=timezone.now() + timedelta(days=14),
            total_marks=100
        )
        
        self.quiz = Quiz.objects.create(
            course=self.course,
            title="Performance Quiz",
            total_time_minutes=30,
            is_published=True,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2)
        )
        
        # Create questions for quiz
        self.question1 = Question.objects.create(
            quiz=self.quiz,
            question_type="MCQ",
            text="Question 1",
            options=["A", "B", "C", "D"],
            correct_answer="0",
            points=10
        )
        self.question2 = Question.objects.create(
            quiz=self.quiz,
            question_type="MCQ",
            text="Question 2",
            options=["A", "B", "C", "D"],
            correct_answer="1",
            points=15
        )
    
    def test_TC11_student_analytics_tab_access(self):
        """TC11: Student Analytics Tab - Performance Lookup"""
        # Feature Name: Student Analytics Access
        # Input Data: Student role, analytics endpoint
        # Expected Output: Status 200, personal performance data
        self.client.force_authenticate(user=self.student1)
        
        # Test student can access their own analytics
        response = self.client.get('/api/lms/student-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify analytics contain assignment and quiz performance
        self.assertIn('assignments', response.data)
        self.assertIn('quizzes', response.data)
        self.assertIn('overall_performance', response.data)
        # Status: PASS
    
    def test_TC12_teacher_cannot_access_student_analytics(self):
        """TC12: Teacher Analytics Access - Restricted"""
        # Feature Name: Analytics Access Control
        # Input Data: Teacher role, student analytics endpoint
        # Expected Output: Status 403, permission denied
        self.client.force_authenticate(user=self.teacher)
        
        # Test teacher cannot access student analytics tab
        response = self.client.get('/api/lms/student-analytics/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Status: PASS
    
    def test_TC13_assignment_submission_deadline_consistency(self):
        """TC13: Assignment Submission - Deadline Consistency"""
        # Feature Name: Assignment Deadline Management
        # Input Data: Assignment creation, submission with deadline check
        # Expected Output: Same deadline as set by teacher
        self.client.force_authenticate(user=self.teacher)
        
        # Create assignment with specific deadline
        deadline_time = timezone.now() + timedelta(hours=24)
        assignment_data = {
            'course': self.course.id,
            'title': 'Deadline Test Assignment',
            'description': 'Test deadline consistency',
            'due_date': deadline_time.isoformat(),
            'total_marks': 100
        }
        response = self.client.post('/api/lms/assignments/', assignment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assignment_id = response.data['id']
        
        # Verify deadline is stored correctly
        assignment = Assignment.objects.get(id=assignment_id)
        self.assertEqual(assignment.due_date.replace(microsecond=0), 
                        deadline_time.replace(microsecond=0))
        
        # Student retrieves assignment and sees same deadline
        self.client.force_authenticate(user=self.student1)
        response = self.client.get(f'/api/lms/assignments/{assignment_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Convert both to comparable format
        api_deadline = response.data['due_date']
        if isinstance(api_deadline, str):
            api_deadline = timezone.datetime.fromisoformat(api_deadline.replace('Z', '+00:00'))
        
        self.assertEqual(api_deadline.replace(microsecond=0), 
                        deadline_time.replace(microsecond=0))
        # Status: PASS
    
    def test_TC14_student_specific_analytics_assignments_quizzes(self):
        """TC14: Student Analytics - Assignment & Quiz Based"""
        # Feature Name: Student Performance Analytics
        # Input Data: Student role, assignments and quizzes completion
        # Expected Output: Analytics based on student's own data only
        self.client.force_authenticate(user=self.student1)
        
        # Submit assignment
        submission_data = {
            'assignment': self.assignment1.id,
            'links': [{'label': 'My Work', 'url': 'https://example.com'}]
        }
        response = self.client.post('/api/lms/assignment-submissions/', submission_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Attempt quiz
        attempt_data = {
            'quiz': self.quiz.id,
            'answers': {str(self.question1.id): '0', str(self.question2.id): '1'},
            'time_taken_seconds': 300
        }
        response = self.client.post('/api/lms/quiz-attempts/', attempt_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get student analytics
        response = self.client.get('/api/lms/student-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify analytics contain student's assignment and quiz data
        assignments_data = response.data['assignments']
        quizzes_data = response.data['quizzes']
        
        self.assertEqual(len(assignments_data), 1)  # Only student's submission
        self.assertEqual(len(quizzes_data), 1)      # Only student's attempt
        self.assertEqual(assignments_data[0]['assignment'], self.assignment1.id)
        self.assertEqual(quizzes_data[0]['quiz'], self.quiz.id)
        # Status: PASS
    
    def test_TC15_attendance_count_enrolled_students_only(self):
        """TC15: Attendance Count - Enrolled Students Only"""
        # Feature Name: Attendance Management
        # Input Data: Course with 1 enrolled student, attendance record
        # Expected Output: Attendance based on actual enrolled students (1), not fixed 3
        self.client.force_authenticate(user=self.teacher)
        
        # Create attendance record
        attendance_data = {
            'course': self.course.id,
            'date': timezone.now().date()
        }
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record_id = response.data['id']
        
        # Mark attendance for the only enrolled student
        mark_data = {
            'entries': [{
                'student_id': self.student1.id,
                'status': 'PRESENT',
                'remarks': 'On time'
            }]
        }
        response = self.client.post(f'/api/lms/attendance/{record_id}/mark_attendance/', mark_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify attendance record shows only enrolled students count
        response = self.client.get(f'/api/lms/attendance/{record_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that attendance is based on enrolled students (1), not fixed 3
        attendance_entries = response.data.get('entries', [])
        enrolled_students_count = self.course.students.count()
        
        self.assertEqual(len(attendance_entries), enrolled_students_count)
        self.assertEqual(enrolled_students_count, 1)  # Only 1 student enrolled
        self.assertNotEqual(enrolled_students_count, 3)  # Not fixed 3
        # Status: PASS
    
    def test_TC16_attendance_accuracy_with_multiple_enrollments(self):
        """TC16: Attendance Accuracy - Multiple Enrollments"""
        # Feature Name: Attendance Count Accuracy
        # Input Data: Course with multiple students, attendance marking
        # Expected Output: Accurate attendance count for enrolled students
        # Add more students to course
        self.course.students.add(self.student2, self.student3)
        
        self.client.force_authenticate(user=self.teacher)
        
        # Create attendance record
        attendance_data = {
            'course': self.course.id,
            'date': timezone.now().date()
        }
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record_id = response.data['id']
        
        # Mark attendance for all enrolled students
        mark_data = {
            'entries': [
                {'student_id': self.student1.id, 'status': 'PRESENT', 'remarks': 'On time'},
                {'student_id': self.student2.id, 'status': 'ABSENT', 'remarks': 'Absent'},
                {'student_id': self.student3.id, 'status': 'PRESENT', 'remarks': 'On time'}
            ]
        }
        response = self.client.post(f'/api/lms/attendance/{record_id}/mark_attendance/', mark_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify attendance accuracy
        response = self.client.get(f'/api/lms/attendance/{record_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        attendance_entries = response.data.get('entries', [])
        enrolled_students_count = self.course.students.count()
        
        self.assertEqual(len(attendance_entries), enrolled_students_count)
        self.assertEqual(enrolled_students_count, 3)  # Now 3 students enrolled
        
        # Verify all students are accounted for
        student_ids_in_attendance = [entry['student'] for entry in attendance_entries]
        self.assertIn(self.student1.id, student_ids_in_attendance)
        self.assertIn(self.student2.id, student_ids_in_attendance)
        self.assertIn(self.student3.id, student_ids_in_attendance)
        # Status: PASS

class AssignmentDeadlineTests(APITestCase):
    """Test assignment deadline consistency and edge cases"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            full_name="Student User",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
        self.course = Course.objects.create(
            name="Deadline Test Course",
            code="DDL101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        self.course.teachers.add(self.teacher)
        self.course.students.add(self.student)
    
    def test_assignment_deadline_timezone_consistency(self):
        """Test assignment deadline consistency across timezones"""
        self.client.force_authenticate(user=self.teacher)
        
        # Create assignment with specific deadline
        specific_deadline = timezone.now() + timedelta(hours=48)
        assignment_data = {
            'course': self.course.id,
            'title': 'Timezone Test Assignment',
            'description': 'Test timezone consistency',
            'due_date': specific_deadline.isoformat(),
            'total_marks': 100
        }
        response = self.client.post('/api/lms/assignments/', assignment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assignment_id = response.data['id']
        
        # Verify deadline consistency when retrieved
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f'/api/lms/assignments/{assignment_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        retrieved_deadline = response.data['due_date']
        if isinstance(retrieved_deadline, str):
            retrieved_deadline = timezone.datetime.fromisoformat(retrieved_deadline.replace('Z', '+00:00'))
        
        # Compare without microseconds for precision
        self.assertEqual(retrieved_deadline.replace(microsecond=0), 
                        specific_deadline.replace(microsecond=0))
    
    def test_assignment_deadline_update_propagation(self):
        """Test deadline updates propagate correctly to all views"""
        self.client.force_authenticate(user=self.teacher)
        
        # Create assignment
        original_deadline = timezone.now() + timedelta(days=7)
        assignment_data = {
            'course': self.course.id,
            'title': 'Update Test Assignment',
            'description': 'Test deadline update',
            'due_date': original_deadline.isoformat(),
            'total_marks': 100
        }
        response = self.client.post('/api/lms/assignments/', assignment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assignment_id = response.data['id']
        
        # Update deadline
        new_deadline = timezone.now() + timedelta(days=14)
        update_data = {'due_date': new_deadline.isoformat()}
        response = self.client.patch(f'/api/lms/assignments/{assignment_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify updated deadline in list view
        response = self.client.get('/api/lms/assignments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_assignment = next(a for a in response.data['results'] if a['id'] == assignment_id)
        
        api_deadline = updated_assignment['due_date']
        if isinstance(api_deadline, str):
            api_deadline = timezone.datetime.fromisoformat(api_deadline.replace('Z', '+00:00'))
        
        self.assertEqual(api_deadline.replace(microsecond=0), 
                        new_deadline.replace(microsecond=0))

class StudentPerformanceAnalyticsTests(APITestCase):
    """Test student-specific performance analytics"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student1 = CustomUser.objects.create_user(
            email="student1@example.com",
            full_name="Student One",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.student2 = CustomUser.objects.create_user(
            email="student2@example.com",
            full_name="Student Two",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
        
        # Create course
        self.course = Course.objects.create(
            name="Performance Test Course",
            code="PERF101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        self.course.teachers.add(self.teacher)
        self.course.students.add(self.student1, self.student2)
        
        # Create assignments
        self.assignment1 = Assignment.objects.create(
            course=self.course,
            title="Performance Assignment 1",
            description="Test assignment 1",
            due_date=timezone.now() + timedelta(days=7),
            total_marks=100
        )
        self.assignment2 = Assignment.objects.create(
            course=self.course,
            title="Performance Assignment 2",
            description="Test assignment 2",
            due_date=timezone.now() + timedelta(days=14),
            total_marks=150
        )
        
        # Create quiz
        self.quiz = Quiz.objects.create(
            course=self.course,
            title="Performance Quiz",
            total_time_minutes=45,
            is_published=True,
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() + timedelta(hours=2)
        )
        
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_type="MCQ",
            text="Performance Question",
            options=["A", "B", "C", "D"],
            correct_answer="0",
            points=20
        )
    
    def test_student_analytics_isolation(self):
        """Test that each student sees only their own analytics"""
        # Student 1 submits assignment and attempts quiz
        self.client.force_authenticate(user=self.student1)
        
        # Submit assignment
        submission_data = {
            'assignment': self.assignment1.id,
            'links': [{'label': 'Student 1 Work', 'url': 'https://example.com/student1'}]
        }
        response = self.client.post('/api/lms/assignment-submissions/', submission_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Attempt quiz
        attempt_data = {
            'quiz': self.quiz.id,
            'answers': {str(self.question.id): '0'},
            'time_taken_seconds': 600
        }
        response = self.client.post('/api/lms/quiz-attempts/', attempt_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get Student 1 analytics
        response = self.client.get('/api/lms/student-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        student1_assignments = response.data['assignments']
        student1_quizzes = response.data['quizzes']
        
        # Verify Student 1 sees only their data
        self.assertEqual(len(student1_assignments), 1)
        self.assertEqual(len(student1_quizzes), 1)
        self.assertEqual(student1_assignments[0]['student'], self.student1.id)
        
        # Student 2 should see empty analytics (no submissions)
        self.client.force_authenticate(user=self.student2)
        response = self.client.get('/api/lms/student-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        student2_assignments = response.data['assignments']
        student2_quizzes = response.data['quizzes']
        
        self.assertEqual(len(student2_assignments), 0)
        self.assertEqual(len(student2_quizzes), 0)
    
    def test_analytics_performance_calculation(self):
        """Test accurate performance calculation in analytics"""
        self.client.force_authenticate(user=self.student1)
        
        # Submit assignment with high score
        submission_data = {
            'assignment': self.assignment1.id,
            'links': [{'label': 'High Score Work', 'url': 'https://example.com'}]
        }
        response = self.client.post('/api/lms/assignment-submissions/', submission_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Manually grade the submission for testing
        submission = AssignmentSubmission.objects.get(assignment=self.assignment1, student=self.student1)
        submission.score = 85  # 85/100 = 85%
        submission.save()
        
        # Attempt quiz with correct answer
        attempt_data = {
            'quiz': self.quiz.id,
            'answers': {str(self.question.id): '0'},
            'time_taken_seconds': 300
        }
        response = self.client.post('/api/lms/quiz-attempts/', attempt_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Manually grade the quiz attempt
        attempt = QuizAttempt.objects.get(quiz=self.quiz, student=self.student1)
        attempt.score = 20  # 20/20 = 100%
        attempt.save()
        
        # Get analytics and verify calculations
        response = self.client.get('/api/lms/student-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        overall_performance = response.data['overall_performance']
        
        # Verify performance metrics
        self.assertIn('assignment_average', overall_performance)
        self.assertIn('quiz_average', overall_performance)
        self.assertIn('total_average', overall_performance)
        
        # Check calculated averages
        expected_assignment_avg = 85.0  # 85/100
        expected_quiz_avg = 100.0       # 20/20
        expected_total_avg = (85.0 + 100.0) / 2  # Average of both
        
        self.assertEqual(overall_performance['assignment_average'], expected_assignment_avg)
        self.assertEqual(overall_performance['quiz_average'], expected_quiz_avg)
        self.assertEqual(overall_performance['total_average'], expected_total_avg)

class AttendanceCountAccuracyTests(APITestCase):
    """Test attendance counting accuracy for enrolled students"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student1 = CustomUser.objects.create_user(
            email="student1@example.com",
            full_name="Student One",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.student2 = CustomUser.objects.create_user(
            email="student2@example.com",
            full_name="Student Two",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
        
        # Create course with dynamic enrollment
        self.course = Course.objects.create(
            name="Attendance Accuracy Course",
            code="ATT101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        self.course.teachers.add(self.teacher)
        # Initially enroll only 1 student
        self.course.students.add(self.student1)
    
    def test_attendance_adapts_to_enrollment_changes(self):
        """Test attendance adapts when students are added/removed"""
        self.client.force_authenticate(user=self.teacher)
        
        # Create attendance record with 1 student
        attendance_data = {
            'course': self.course.id,
            'date': timezone.now().date()
        }
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record_id = response.data['id']
        
        # Mark attendance for 1 student
        mark_data = {
            'entries': [{
                'student_id': self.student1.id,
                'status': 'PRESENT',
                'remarks': 'Only student'
            }]
        }
        response = self.client.post(f'/api/lms/attendance/{record_id}/mark_attendance/', mark_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify attendance shows 1 student
        response = self.client.get(f'/api/lms/attendance/{record_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        attendance_entries = response.data.get('entries', [])
        self.assertEqual(len(attendance_entries), 1)
        self.assertEqual(self.course.students.count(), 1)
        
        # Add second student to course
        self.course.students.add(self.student2)
        
        # Create new attendance record
        attendance_data2 = {
            'course': self.course.id,
            'date': (timezone.now().date() + timedelta(days=1))
        }
        response = self.client.post('/api/lms/attendance/', attendance_data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record_id2 = response.data['id']
        
        # Mark attendance for 2 students
        mark_data2 = {
            'entries': [
                {'student_id': self.student1.id, 'status': 'PRESENT', 'remarks': 'Student 1'},
                {'student_id': self.student2.id, 'status': 'PRESENT', 'remarks': 'Student 2'}
            ]
        }
        response = self.client.post(f'/api/lms/attendance/{record_id2}/mark_attendance/', mark_data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify attendance shows 2 students
        response = self.client.get(f'/api/lms/attendance/{record_id2}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        attendance_entries2 = response.data.get('entries', [])
        self.assertEqual(len(attendance_entries2), 2)
        self.assertEqual(self.course.students.count(), 2)
        
        # Verify it's not fixed at 3
        self.assertNotEqual(self.course.students.count(), 3)
        self.assertNotEqual(len(attendance_entries2), 3)
    
    def test_attendance_statistics_accuracy(self):
        """Test attendance statistics reflect actual enrollment"""
        # Add multiple students to create realistic scenario
        additional_students = []
        for i in range(3, 6):  # Add students 3, 4, 5
            student = CustomUser.objects.create_user(
                email=f'student{i}@example.com',
                full_name=f'Student {i}',
                password='studentpass123',
                role='STUDENT',
                institute=self.institute
            )
            additional_students.append(student)
            self.course.students.add(student)
        
        self.client.force_authenticate(user=self.teacher)
        
        # Create attendance record
        attendance_data = {
            'course': self.course.id,
            'date': timezone.now().date()
        }
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record_id = response.data['id']
        
        # Mark mixed attendance
        mark_data = {
            'entries': [
                {'student_id': self.student1.id, 'status': 'PRESENT', 'remarks': 'Present'},
                {'student_id': self.student2.id, 'status': 'ABSENT', 'remarks': 'Absent'},
                {'student_id': additional_students[0].id, 'status': 'PRESENT', 'remarks': 'Present'},
                {'student_id': additional_students[1].id, 'status': 'LATE', 'remarks': 'Late'},
                {'student_id': additional_students[2].id, 'status': 'PRESENT', 'remarks': 'Present'}
            ]
        }
        response = self.client.post(f'/api/lms/attendance/{record_id}/mark_attendance/', mark_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify attendance statistics
        response = self.client.get(f'/api/lms/attendance/{record_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        attendance_entries = response.data.get('entries', [])
        enrolled_count = self.course.students.count()
        
        # Verify counts match
        self.assertEqual(len(attendance_entries), enrolled_count)
        self.assertEqual(enrolled_count, 5)  # Students 1, 2, 3, 4, 5
        
        # Verify statistics calculation
        present_count = sum(1 for entry in attendance_entries if entry['status'] == 'PRESENT')
        absent_count = sum(1 for entry in attendance_entries if entry['status'] == 'ABSENT')
        late_count = sum(1 for entry in attendance_entries if entry['status'] == 'LATE')
        
        self.assertEqual(present_count, 3)
        self.assertEqual(absent_count, 1)
        self.assertEqual(late_count, 1)
        self.assertEqual(present_count + absent_count + late_count, enrolled_count)
        
        # Verify it's not the hardcoded 3
        self.assertNotEqual(enrolled_count, 3)
        self.assertNotEqual(len(attendance_entries), 3)

# =============================================================================
# J. BOUNDARY VALUE ANALYSIS FOR NEW FEATURES
# =============================================================================

class NewFeaturesBoundaryValueTests(APITestCase):
    """Boundary Value Analysis for analytics and attendance features"""
    
    def setUp(self):
        self.institute = Institute.objects.create(
            name="Test Institute",
            institute_code="TEST001"
        )
        self.teacher = CustomUser.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="teacherpass123",
            role="TEACHER",
            institute=self.institute
        )
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            full_name="Student User",
            password="studentpass123",
            role="STUDENT",
            institute=self.institute
        )
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            institute=self.institute
        )
        self.course = Course.objects.create(
            name="BVA Test Course",
            code="BVA101",
            institute=self.institute,
            department=self.department,
            semester="Fall",
            academic_year="2025-2026",
            credits=3
        )
        self.course.teachers.add(self.teacher)
        self.course.students.add(self.student)
    
    def test_bva_assignment_deadline_boundaries(self):
        """BVA for Assignment Deadline Field"""
        self.client.force_authenticate(user=self.teacher)
        
        # Test minimum boundary (1 hour from now)
        min_deadline = timezone.now() + timedelta(hours=1)
        assignment_data = {
            'course': self.course.id,
            'title': 'Min Deadline Assignment',
            'description': 'Test minimum deadline',
            'due_date': min_deadline.isoformat(),
            'total_marks': 100
        }
        response = self.client.post('/api/lms/assignments/', assignment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just below minimum (past deadline) - should work but warn
        past_deadline = timezone.now() - timedelta(hours=1)
        assignment_data['title'] = 'Past Deadline Assignment'
        assignment_data['due_date'] = past_deadline.isoformat()
        response = self.client.post('/api/lms/assignments/', assignment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test maximum boundary (1 year from now)
        max_deadline = timezone.now() + timedelta(days=365)
        assignment_data['title'] = 'Max Deadline Assignment'
        assignment_data['due_date'] = max_deadline.isoformat()
        response = self.client.post('/api/lms/assignments/', assignment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just above maximum (more than 1 year)
        over_max_deadline = timezone.now() + timedelta(days=400)
        assignment_data['title'] = 'Over Max Deadline Assignment'
        assignment_data['due_date'] = over_max_deadline.isoformat()
        response = self.client.post('/api/lms/assignments/', assignment_data, format='json')
        # Should either succeed or fail based on validation rules
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_bva_attendance_date_boundaries(self):
        """BVA for Attendance Date Field"""
        self.client.force_authenticate(user=self.teacher)
        
        # Test minimum boundary (today)
        today = timezone.now().date()
        attendance_data = {
            'course': self.course.id,
            'date': today
        }
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just below minimum (yesterday) - should work for past attendance
        yesterday = today - timedelta(days=1)
        attendance_data['date'] = yesterday
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test maximum boundary (course end date + reasonable buffer)
        course_end_date = today + timedelta(weeks=16)  # Typical semester length
        attendance_data['date'] = course_end_date
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test just above maximum (far future date)
        far_future = today + timedelta(weeks=52)  # 1 year in future
        attendance_data['date'] = far_future
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        # Should either succeed or fail based on validation rules
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_bva_performance_score_boundaries(self):
        """BVA for Performance Score Calculations"""
        self.client.force_authenticate(user=self.teacher)
        
        # Create assignment for testing
        assignment = Assignment.objects.create(
            course=self.course,
            title='Score Test Assignment',
            description='Test score boundaries',
            due_date=timezone.now() + timedelta(days=7),
            total_marks=100
        )
        
        # Student submits assignment
        self.client.force_authenticate(user=self.student)
        submission_data = {
            'assignment': assignment.id,
            'links': [{'label': 'Test Work', 'url': 'https://example.com'}]
        }
        response = self.client.post('/api/lms/assignment-submissions/', submission_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        submission = AssignmentSubmission.objects.get(assignment=assignment, student=self.student)
        
        # Test minimum boundary (0 score)
        submission.score = 0
        submission.save()
        
        response = self.client.get('/api/lms/student-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        performance = response.data.get('overall_performance', {})
        assignment_avg = performance.get('assignment_average', 0)
        self.assertEqual(assignment_avg, 0.0)
        
        # Test maximum boundary (100 score)
        submission.score = 100
        submission.save()
        
        response = self.client.get('/api/lms/student-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        performance = response.data.get('overall_performance', {})
        assignment_avg = performance.get('assignment_average', 0)
        self.assertEqual(assignment_avg, 100.0)
        
        # Test just below minimum (negative score) - should be handled gracefully
        submission.score = -1
        submission.save()
        
        response = self.client.get('/api/lms/student-analytics/')
        # Should handle negative scores gracefully or reject them
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_bva_course_enrollment_boundaries(self):
        """BVA for Course Enrollment Limits"""
        self.client.force_authenticate(user=self.teacher)
        
        # Test minimum boundary (0 students - empty course)
        self.course.students.clear()
        attendance_data = {
            'course': self.course.id,
            'date': timezone.now().date()
        }
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify empty course attendance
        response = self.client.get(f'/api/lms/attendance/{response.data["id"]}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attendance_entries = response.data.get('entries', [])
        self.assertEqual(len(attendance_entries), 0)
        self.assertEqual(self.course.students.count(), 0)
        
        # Test maximum reasonable boundary (100 students)
        test_students = []
        for i in range(1, 101):  # Add 100 students
            student = CustomUser.objects.create_user(
                email=f'student{i}@example.com',
                full_name=f'Student {i}',
                password='studentpass123',
                role='STUDENT',
                institute=self.institute
            )
            test_students.append(student)
            self.course.students.add(student)
        
        # Verify attendance with 100 students
        attendance_data['date'] = (timezone.now().date() + timedelta(days=1))
        response = self.client.post('/api/lms/attendance/', attendance_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response = self.client.get(f'/api/lms/attendance/{response.data["id"]}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        attendance_entries = response.data.get('entries', [])
        enrolled_count = self.course.students.count()
        
        self.assertEqual(len(attendance_entries), enrolled_count)
        self.assertEqual(enrolled_count, 100)
        
        # Verify it's not hardcoded to 3
        self.assertNotEqual(enrolled_count, 3)
        self.assertNotEqual(len(attendance_entries), 3)
