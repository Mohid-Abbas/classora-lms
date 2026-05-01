"""
Tests for new features:
1. Assignment/Quiz edit/delete with cascade
2. Announcements CRUD for all roles
3. Course uniqueness constraints
4. Course sections with teacher assignment
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Institute, CustomUser
from .models import Course, Quiz, Question, QuizAttempt, Assignment, AssignmentSubmission, Announcement, Department


def _post_json(client, url, data):
    """Helper to POST JSON data."""
    return client.post(url, data, format="json")


def _patch_json(client, url, data):
    """Helper to PATCH JSON data."""
    return client.patch(url, data, format="json")


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
