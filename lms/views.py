from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    Course, Lecture, Assignment, Quiz, Question,
    AttendanceRecord, AttendanceEntry, Announcement, Department,
    AssignmentSubmission, Notification, QuizAttempt, AnnouncementComment
)
from .serializers import (
    CourseSerializer, LectureSerializer, AssignmentSerializer, QuizSerializer,
    QuestionSerializer, AttendanceRecordSerializer, AttendanceEntrySerializer,
    AnnouncementSerializer, DepartmentSerializer, AssignmentSubmissionSerializer,
    NotificationSerializer, QuizAttemptSerializer, AnnouncementCommentSerializer
)

class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Department.objects.filter(institute=user.institute)

    def perform_create(self, serializer):
        serializer.save(institute=self.request.user.institute)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != "ADMIN":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only an admin can perform this action.")
        return super().destroy(request, *args, **kwargs)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'role'):
            return self.queryset.none()
            
        if user.role == "ADMIN":
            return self.queryset.filter(institute=user.institute)
        elif user.role == "TEACHER":
            return self.queryset.filter(teachers=user)
        elif user.role == "STUDENT":
            return self.queryset.filter(students=user, is_published=True)
        return self.queryset.none()

    def _check_duplicate_course(self, data, exclude_instance=None):
        """Check if a course with same code, semester, academic_year, section already exists in the institute."""
        from rest_framework.exceptions import ValidationError
        
        institute = self.request.user.institute
        code = data.get('code')
        semester = data.get('semester')
        academic_year = data.get('academic_year')
        section = data.get('section') or 'A'  # Default to 'A' if not provided
        
        if not all([code, semester, academic_year]):
            return  # Let serializer handle required field validation
        
        qs = Course.objects.filter(
            institute=institute,
            code=code,
            semester=semester,
            academic_year=academic_year,
            section=section
        )
        
        if exclude_instance:
            qs = qs.exclude(id=exclude_instance.id)
        
        if qs.exists():
            raise ValidationError({
                "non_field_errors": [
                    f"A course with code '{code}', semester '{semester}', year '{academic_year}', section '{section}' already exists in your institute."
                ]
            })

    def perform_create(self, serializer):
        self._check_duplicate_course(serializer.validated_data)
        serializer.save(institute=self.request.user.institute)

    def perform_update(self, serializer):
        self._check_duplicate_course(serializer.validated_data, exclude_instance=serializer.instance)
        serializer.save()

    @action(detail=True, methods=['post'], url_path='remove_user')
    def remove_user(self, request, pk=None):
        if request.user.role != "ADMIN":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only an admin can remove users from an enrollment.")
        
        course = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        from accounts.models import CustomUser
        try:
            target_user = CustomUser.objects.get(id=user_id, institute=request.user.institute)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if target_user.role == "TEACHER":
            course.teachers.remove(target_user)
        elif target_user.role == "STUDENT":
            course.students.remove(target_user)
        else:
            return Response({"detail": "Cannot remove admin."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "User securely removed from course"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='assign_teacher')
    def assign_teacher(self, request, pk=None):
        """Assign a teacher to this course. Teachers can be assigned to different sections but not twice to the same section."""
        from rest_framework.exceptions import PermissionDenied, ValidationError
        from accounts.models import CustomUser
        
        if request.user.role != "ADMIN":
            raise PermissionDenied("Only admins can assign teachers to courses.")
        
        course = self.get_object()
        teacher_id = request.data.get('teacher_id')
        if not teacher_id:
            return Response({"detail": "teacher_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            teacher = CustomUser.objects.get(id=teacher_id, institute=request.user.institute, role="TEACHER")
        except CustomUser.DoesNotExist:
            return Response({"detail": "Teacher not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if teacher is already assigned to this specific course section
        if course.teachers.filter(id=teacher.id).exists():
            return Response({
                "detail": f"Teacher {teacher.full_name} is already assigned to this course section."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if teacher is already teaching another section of the same course in same semester/year
        existing_sections = Course.objects.filter(
            institute=request.user.institute,
            code=course.code,
            semester=course.semester,
            academic_year=course.academic_year,
            teachers=teacher
        ).exclude(id=course.id)
        
        if existing_sections.exists():
            section_list = [c.section for c in existing_sections]
            return Response({
                "detail": f"Teacher {teacher.full_name} is already assigned to section(s) {', '.join(section_list)} of this course. They can teach multiple sections but are already assigned.",
                "existing_sections": section_list
            }, status=status.HTTP_200_OK)  # Allow but inform
        
        course.teachers.add(teacher)
        
        # Notify the teacher
        Notification.objects.create(
            user=teacher,
            title="Course Assignment",
            message=f"You have been assigned to teach {course.name} (Section {course.section}) for {course.semester} {course.academic_year}."
        )
        
        return Response({
            "detail": f"Teacher {teacher.full_name} assigned to {course.name} (Section {course.section})."
        }, status=status.HTTP_200_OK)

class LectureViewSet(viewsets.ModelViewSet):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return self.queryset.filter(course__institute=user.institute)
        elif user.role == "TEACHER":
            return self.queryset.filter(course__teachers=user)
        elif user.role == "STUDENT":
            return self.queryset.filter(course__students=user)
        return self.queryset.none()

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return self.queryset.filter(course__institute=user.institute)
        elif user.role == "TEACHER":
            return self.queryset.filter(course__teachers=user)
        elif user.role == "STUDENT":
            return self.queryset.filter(course__students=user)
        return self.queryset.none()

    def _validate_course_ownership(self, course_id):
        from rest_framework.exceptions import PermissionDenied, ValidationError
        user = self.request.user
        if not course_id:
            return
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise ValidationError({"course": "Course not found."})
        if user.role == "ADMIN":
            if course.institute != user.institute:
                raise PermissionDenied("You can only create assignments for courses in your institute.")
        elif user.role == "TEACHER":
            if user not in course.teachers.all():
                raise PermissionDenied("You can only create assignments for courses you teach.")
        else:
            raise PermissionDenied("Students cannot create assignments.")

    def _check_assignment_ownership(self, instance):
        from rest_framework.exceptions import PermissionDenied
        user = self.request.user
        if user.role == "STUDENT":
            raise PermissionDenied("Students cannot modify assignments.")
        if user.role == "TEACHER" and user not in instance.course.teachers.all():
            raise PermissionDenied("You can only modify assignments for your own courses.")

    def perform_create(self, serializer):
        course_id = serializer.validated_data.get('course')
        if course_id:
            course_id = course_id.id if hasattr(course_id, 'id') else course_id
        self._validate_course_ownership(course_id)
        assignment = serializer.save()
        # notify students
        students = assignment.course.students.all()
        notifications = []
        for student in students:
            notifications.append(Notification(
                user=student,
                title="New Assignment",
                message=f"A new assignment '{assignment.title}' has been uploaded for {assignment.course.name}."
            ))
        Notification.objects.bulk_create(notifications)

    def perform_update(self, serializer):
        instance = serializer.instance
        self._check_assignment_ownership(instance)
        course_id = serializer.validated_data.get('course', instance.course_id)
        if course_id:
            course_id = course_id.id if hasattr(course_id, 'id') else course_id
            if course_id != instance.course_id:
                self._validate_course_ownership(course_id)
        assignment = serializer.save()
        # notify students of update
        students = assignment.course.students.all()
        notifications = []
        for student in students:
            notifications.append(Notification(
                user=student,
                title="Assignment Updated",
                message=f"Assignment '{assignment.title}' has been updated."
            ))
        Notification.objects.bulk_create(notifications)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._check_assignment_ownership(instance)
        # Cascade: Delete all related submissions before deleting assignment
        submission_count = instance.submissions.count()
        instance.submissions.all().delete()
        # Notify students
        students = instance.course.students.all()
        notifications = [
            Notification(
                user=student,
                title="Assignment Deleted",
                message=f"Assignment '{instance.title}' has been deleted by your instructor."
            )
            for student in students
        ]
        Notification.objects.bulk_create(notifications)
        return super().destroy(request, *args, **kwargs)

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return self.queryset.filter(course__institute=user.institute)
        elif user.role == "TEACHER":
            return self.queryset.filter(course__teachers=user)
        elif user.role == "STUDENT":
            return self.queryset.filter(course__students=user, is_published=True)
        return self.queryset.none()

    def _validate_course_ownership(self, course_id):
        from rest_framework.exceptions import PermissionDenied, ValidationError
        user = self.request.user
        if not course_id:
            return
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise ValidationError({"course": "Course not found."})
        if user.role == "ADMIN":
            if course.institute != user.institute:
                raise PermissionDenied("You can only create quizzes for courses in your institute.")
        elif user.role == "TEACHER":
            if user not in course.teachers.all():
                raise PermissionDenied("You can only create quizzes for courses you teach.")
        else:
            raise PermissionDenied("Students cannot create quizzes.")

    def perform_create(self, serializer):
        course_id = serializer.validated_data.get('course')
        if course_id:
            course_id = course_id.id if hasattr(course_id, 'id') else course_id
        self._validate_course_ownership(course_id)
        quiz = serializer.save()
        if quiz.is_published:
            self._notify_students(quiz, "New Quiz Available", f"Quiz '{quiz.title}' is now available for {quiz.course.name}.")

    def _check_quiz_ownership(self, instance):
        from rest_framework.exceptions import PermissionDenied
        user = self.request.user
        if user.role == "STUDENT":
            raise PermissionDenied("Students cannot modify quizzes.")
        if user.role == "TEACHER" and user not in instance.course.teachers.all():
            raise PermissionDenied("You can only modify quizzes for your own courses.")

    def perform_update(self, serializer):
        instance = serializer.instance
        self._check_quiz_ownership(instance)
        course_id = serializer.validated_data.get('course', instance.course_id)
        if course_id:
            course_id = course_id.id if hasattr(course_id, 'id') else course_id
            if course_id != instance.course_id:
                self._validate_course_ownership(course_id)
        old_published = instance.is_published
        quiz = serializer.save()
        if quiz.is_published and not old_published:
            self._notify_students(quiz, "New Quiz Available", f"Quiz '{quiz.title}' is now available for {quiz.course.name}.")
        elif quiz.is_published:
            self._notify_students(quiz, "Quiz Updated", f"Quiz '{quiz.title}' has been updated.")

    def _notify_students(self, quiz, title, message):
        students = quiz.course.students.all()
        Notification.objects.bulk_create([
            Notification(
                user=s,
                title=title,
                message=message
            ) for s in students
        ])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._check_quiz_ownership(instance)
        # Cascade: Delete all related attempts and questions before deleting quiz
        instance.attempts.all().delete()
        instance.questions.all().delete()
        # Notify students
        students = instance.course.students.all()
        Notification.objects.bulk_create([
            Notification(
                user=s,
                title="Quiz Deleted",
                message=f"Quiz '{instance.title}' has been deleted by your instructor."
            ) for s in students
        ])
        return super().destroy(request, *args, **kwargs)

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        quiz_id = self.request.query_params.get('quiz')
        
        if user.role == "ADMIN":
            qs = self.queryset.filter(quiz__course__institute=user.institute)
        elif user.role == "TEACHER":
            qs = self.queryset.filter(quiz__course__teachers=user)
        elif user.role == "STUDENT":
            qs = self.queryset.filter(quiz__course__students=user, quiz__is_published=True)
        else:
            return self.queryset.none()
        
        # Filter by quiz if provided (critical for quiz isolation)
        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)
        
        return qs

    def _validate_quiz_ownership(self, quiz_id):
        from rest_framework.exceptions import PermissionDenied, ValidationError
        user = self.request.user
        if not quiz_id:
            return
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            raise ValidationError({"quiz": "Quiz not found."})
        if user.role == "ADMIN":
            if quiz.course.institute != user.institute:
                raise PermissionDenied("You can only add questions to quizzes in your institute.")
        elif user.role == "TEACHER":
            if user not in quiz.course.teachers.all():
                raise PermissionDenied("You can only add questions to quizzes in courses you teach.")
        else:
            raise PermissionDenied("Students cannot create questions.")

    def perform_create(self, serializer):
        quiz_id = serializer.validated_data.get('quiz')
        if quiz_id:
            quiz_id = quiz_id.id if hasattr(quiz_id, 'id') else quiz_id
        self._validate_quiz_ownership(quiz_id)
        serializer.save()

    def perform_update(self, serializer):
        quiz_id = serializer.validated_data.get('quiz', serializer.instance.quiz_id)
        if quiz_id:
            quiz_id = quiz_id.id if hasattr(quiz_id, 'id') else quiz_id
        self._validate_quiz_ownership(quiz_id)
        serializer.save()

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return self.queryset.filter(course__institute=user.institute)
        elif user.role == "TEACHER":
            return self.queryset.filter(course__teachers=user)
        elif user.role == "STUDENT":
            return self.queryset.filter(course__students=user)
        return self.queryset.none()

    @action(detail=True, methods=['post'])
    def mark_attendance(self, request, pk=None):
        record = self.get_object()
        entries_data = request.data.get('entries', [])
        for entry in entries_data:
            # Accept both 'student' and 'student_id' for compatibility
            student_id = entry.get('student') or entry.get('student_id')
            status_val = entry.get('status')
            remarks = entry.get('remarks', '')
            AttendanceEntry.objects.update_or_create(
                record=record,
                student_id=student_id,
                defaults={'status': status_val, 'remarks': remarks}
            )
        return Response({'status': 'attendance marked'})

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all().order_by('-created_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return self.queryset.none()
        from django.db.models import Q
        from accounts.models import CustomUser
        
        # Base filter: in the same institute
        qs = self.queryset.filter(institute=user.institute)
        
        if user.role == "ADMIN":
            return qs
            
        elif user.role == "TEACHER":
            # Teacher sees: ALL, TEACHER, or their specific course, or targeted to them
            q_target = Q(target_role__in=['ALL', 'TEACHER']) | Q(target_user=user)
            # Course target: null (meaning institute/department wide) OR their specific taught course
            q_course = Q(course__isnull=True) | Q(course__teachers=user)
            # Department target: null OR their course's department
            q_dept = Q(department__isnull=True)
            return qs.filter(q_target, q_course, q_dept).distinct()

        elif user.role == "STUDENT":
            # Student sees: ALL, STUDENT, their enrolled courses, their department, or targeted to them
            q_target = Q(target_role__in=['ALL', 'STUDENT']) | Q(target_user=user)
            q_course = Q(course__isnull=True) | Q(course__students=user)
            
            # Additional logic for department: students are linked via enrolled_courses
            q_dept = Q(department__isnull=True) | Q(department__courses__students=user)
            
            return qs.filter(q_target, q_course, q_dept).distinct()
            
        return self.queryset.none()

    def _validate_student_announcement(self, data):
        """Students can only create announcements for courses they're enrolled in."""
        from rest_framework.exceptions import PermissionDenied, ValidationError
        user = self.request.user
        if user.role != "STUDENT":
            return
        
        course = data.get('course')
        department = data.get('department')
        
        # Student must target a specific course they're enrolled in
        if course:
            course_id = course.id if hasattr(course, 'id') else course
            try:
                course_obj = Course.objects.get(id=course_id)
                if user not in course_obj.students.all():
                    raise PermissionDenied("You can only create announcements for courses you're enrolled in.")
            except Course.DoesNotExist:
                raise ValidationError({"course": "Course not found."})
        elif department:
            # Check if student is in any course in this department
            dept_id = department.id if hasattr(department, 'id') else department
            if not Course.objects.filter(department_id=dept_id, students=user).exists():
                raise PermissionDenied("You can only create announcements for departments where you're enrolled.")
        else:
            raise PermissionDenied("Students must specify a course or department for announcements.")

    def perform_create(self, serializer):
        user = self.request.user
        
        # Validate student announcements
        self._validate_student_announcement(serializer.validated_data)
            
        announcement = serializer.save(author=user, institute=user.institute)
        
        # Dispatch notification to targets
        targets = []
        from django.db.models import Q
        from accounts.models import CustomUser
        
        if announcement.target_user:
            targets.append(announcement.target_user)
        else:
            base_users = CustomUser.objects.filter(institute=user.institute)
            if announcement.target_role != 'ALL':
                base_users = base_users.filter(role=announcement.target_role)
                
            if announcement.course:
                if announcement.target_role == 'STUDENT':
                    base_users = base_users.filter(enrolled_courses=announcement.course)
                elif announcement.target_role == 'TEACHER':
                    base_users = base_users.filter(courses_taught=announcement.course)
                else:
                    base_users = base_users.filter(Q(enrolled_courses=announcement.course) | Q(courses_taught=announcement.course))
                    
            elif announcement.department:
                if announcement.target_role == 'STUDENT':
                    base_users = base_users.filter(enrolled_courses__department=announcement.department)
                elif announcement.target_role == 'TEACHER':
                    base_users = base_users.filter(courses_taught__department=announcement.department)
                else:
                    base_users = base_users.filter(Q(enrolled_courses__department=announcement.department) | Q(courses_taught__department=announcement.department))
            
            targets = list(set(base_users))

        if targets:
            Notification.objects.bulk_create([
                Notification(
                    user=target,
                    title="New Announcement",
                    message=f"New announcement from {user.full_name}: {announcement.title}"
                ) for target in targets if target != user
            ])
            
    def perform_update(self, serializer):
        from rest_framework.exceptions import PermissionDenied, ValidationError
        instance = serializer.instance
        user = self.request.user
        
        # Check ownership (admin can edit any, others can only edit their own)
        if user.role != "ADMIN" and instance.author != user:
            raise PermissionDenied("You can only edit your own announcements.")
        
        # Students must maintain course enrollment validation
        if user.role == "STUDENT":
            course = serializer.validated_data.get('course', instance.course)
            department = serializer.validated_data.get('department', instance.department)
            
            if course:
                course_id = course.id if hasattr(course, 'id') else course
                try:
                    course_obj = Course.objects.get(id=course_id)
                    if user not in course_obj.students.all():
                        raise PermissionDenied("You can only update announcements for courses you're enrolled in.")
                except Course.DoesNotExist:
                    raise ValidationError({"course": "Course not found."})
            elif department:
                dept_id = department.id if hasattr(department, 'id') else department
                if not Course.objects.filter(department_id=dept_id, students=user).exists():
                    raise PermissionDenied("You can only update announcements for departments where you're enrolled.")
            else:
                raise PermissionDenied("Students must specify a course or department for announcements.")
        
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        # Check ownership (admin can delete any, others can only delete their own)
        if user.role != "ADMIN" and instance.author != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own announcements.")
        
        # Additional check for students - can only delete their own announcements
        if user.role == "STUDENT" and instance.author != user:
            raise PermissionDenied("Students can only delete their own announcements.")
            
        return super().destroy(request, *args, **kwargs)


class AnnouncementCommentViewSet(viewsets.ModelViewSet):
    queryset = AnnouncementComment.objects.all()
    serializer_class = AnnouncementCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        announcement_id = self.request.query_params.get('announcement')
        
        # Admin can see all comments in their institute
        if user.role == "ADMIN":
            base_qs = self.queryset.filter(announcement__institute=user.institute)
            if announcement_id:
                return base_qs.filter(announcement_id=announcement_id)
            return base_qs
        
        # For non-admins, filter by announcement visibility
        from django.db.models import Q
        from .models import Announcement
        
        # Get announcements this user can see
        visible_announcements = Announcement.objects.filter(institute=user.institute)
        if user.role == "TEACHER":
            visible_announcements = visible_announcements.filter(
                Q(target_role__in=['ALL', 'TEACHER']) | 
                Q(course__teachers=user) |
                Q(target_user=user)
            )
        elif user.role == "STUDENT":
            visible_announcements = visible_announcements.filter(
                Q(target_role__in=['ALL', 'STUDENT']) | 
                Q(course__students=user) |
                Q(target_user=user)
            )
        
        base_qs = self.queryset.filter(announcement__in=visible_announcements)
        if announcement_id:
            return base_qs.filter(announcement_id=announcement_id)
        return base_qs

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        
        # Notify the announcement author if someone else comments
        if comment.announcement.author != self.request.user:
            Notification.objects.create(
                user=comment.announcement.author,
                title="New Comment on Announcement",
                message=f"{self.request.user.full_name} commented on your announcement: '{comment.announcement.title}'"
            )

    def _check_ownership(self, instance):
        """Check if user can modify this comment."""
        from rest_framework.exceptions import PermissionDenied
        user = self.request.user
        if user.role != "ADMIN" and instance.user_id != user.id:
            raise PermissionDenied("You can only modify your own comments.")

    def perform_update(self, serializer):
        self._check_ownership(serializer.instance)
        comment = serializer.save()
        
        # Notify announcement author about edit if someone else edited
        if comment.announcement.author_id != self.request.user.id:
            Notification.objects.create(
                user=comment.announcement.author,
                title="Comment Edited",
                message=f"{self.request.user.full_name} edited their comment on your announcement: '{comment.announcement.title}'"
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._check_ownership(instance)
        return super().destroy(request, *args, **kwargs)

class AssignmentSubmissionViewSet(viewsets.ModelViewSet):
    queryset = AssignmentSubmission.objects.all()
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return self.queryset.filter(assignment__course__institute=user.institute)
        elif user.role == "TEACHER":
            return self.queryset.filter(assignment__course__teachers=user)
        elif user.role == "STUDENT":
            return self.queryset.filter(student=user)
        return self.queryset.none()

    def perform_create(self, serializer):
        assignment = serializer.validated_data.get('assignment')
        from django.utils import timezone
        
        status_val = "ON_TIME"
        if timezone.now() > assignment.due_date:
            status_val = "LATE"
            
        serializer.save(student=self.request.user, status=status_val)

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all marked read'})

class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "TEACHER":
            return self.queryset.filter(quiz__course__teachers=user)
        elif user.role == "STUDENT":
            return self.queryset.filter(student=user)
        elif user.role == "ADMIN":
            return self.queryset.filter(quiz__course__institute=user.institute)
        return self.queryset.none()

    def perform_create(self, serializer):
        from django.utils import timezone
        from rest_framework.exceptions import ValidationError, PermissionDenied
        quiz = serializer.validated_data.get('quiz')
        answers = serializer.validated_data.get('answers', {})
        time_taken = serializer.validated_data.get('time_taken_seconds')
        user = self.request.user

        # Only students can submit attempts
        if user.role != "STUDENT":
            raise PermissionDenied("Only students can submit quiz attempts.")

        # Student must be enrolled in the quiz's course
        if not quiz.course.students.filter(id=user.id).exists():
            raise PermissionDenied("You are not enrolled in this course.")

        # Quiz must be active/published
        if not quiz.is_active():
            raise ValidationError({"quiz": "This quiz is not currently available for submission."})

        # Prevent duplicate attempts
        if QuizAttempt.objects.filter(quiz=quiz, student=user).exists():
            raise ValidationError({"quiz": "You have already submitted an attempt for this quiz."})

        questions = quiz.questions.all()
        total_marks = sum(q.points for q in questions)
        score = 0

        for q in questions:
            student_answer = answers.get(str(q.id))
            if q.question_type == "MCQ":
                if student_answer is not None and str(student_answer) == str(q.correct_answer):
                    score += q.points
            # SHORT_ANSWER: teacher marks manually

        attempt = serializer.save(
            student=user,
            score=score,
            total_marks=total_marks,
            time_taken_seconds=time_taken
        )

        # Notify student of their score
        percentage = round((score / total_marks) * 100, 1) if total_marks > 0 else 0
        Notification.objects.create(
            user=user,
            title="Quiz Submitted",
            message=f"You scored {score}/{total_marks} ({percentage}%) on '{quiz.title}'.",
        )

    def perform_update(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        if self.request.user.role == "STUDENT":
            raise PermissionDenied("Students cannot modify quiz attempts after submission.")
        serializer.save()

    def perform_destroy(self, instance):
        from rest_framework.exceptions import PermissionDenied
        if self.request.user.role == "STUDENT":
            raise PermissionDenied("Students cannot delete quiz attempts.")
        if self.request.user.role == "TEACHER" and self.request.user not in instance.quiz.course.teachers.all():
            raise PermissionDenied("You can only delete attempts for quizzes in your courses.")
        instance.delete()

    @action(detail=True, methods=['patch'])
    def grade(self, request, pk=None):
        """Teacher manually grades a short-answer attempt."""
        from rest_framework.exceptions import PermissionDenied
        if request.user.role not in ("TEACHER", "ADMIN"):
            raise PermissionDenied("Only teachers can grade quiz attempts.")
        attempt = self.get_object()
        score = request.data.get('score')
        if score is not None:
            attempt.score = float(score)
            attempt.save()
            Notification.objects.create(
                user=attempt.student,
                title="Quiz Graded",
                message=f"Your quiz '{attempt.quiz.title}' has been graded. Score: {score}/{attempt.total_marks}.",
            )
        return Response(QuizAttemptSerializer(attempt).data)

