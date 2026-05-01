from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Institute, CustomUser
from .models import Course, Quiz, Question, QuizAttempt, Department


def _post_json(client, url, data):
    """Helper to POST JSON data (needed for nested dicts/lists in answers/options)."""
    return client.post(url, data, format="json")


def _patch_json(client, url, data):
    """Helper to PATCH JSON data."""
    return client.patch(url, data, format="json")


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
