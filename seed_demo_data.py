import sys
import os
import django
from django.utils import timezone
from datetime import timedelta

# Set up Django
sys.path.append(r'd:\Projects\FSE_Project\classora-lms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classora.settings')
django.setup()

from accounts.models import Institute, CustomUser
from lms.models import Department, Course, Lecture, Assignment, Quiz, Question, Announcement

def seed_data():
    print("Generating Architectural Demo Institute Data...")
    
    # 1. Institute
    institute, created = Institute.objects.get_or_create(
        institute_code='GTU',
        defaults={
            'name': 'Global Tech University',
            'primary_color': '#1E3A8A',
            'description': 'A leading institution for technology and innovation.',
            'website': 'https://gtu.edu',
            'contact_email': 'contact@gtu.edu',
            'phone': '+1-800-GTU-TECH',
            'academic_year': '2025-2026',
            'semester': 'Fall'
        }
    )
    print(f"Institute: {institute.name}")

    # 2. Departments
    dept_cs, _ = Department.objects.get_or_create(
        institute=institute,
        code='CS',
        defaults={'name': 'Computer Science', 'description': 'Department of Computing and AI'}
    )
    dept_math, _ = Department.objects.get_or_create(
        institute=institute,
        code='MATH',
        defaults={'name': 'Mathematics', 'description': 'Department of Mathematical Sciences'}
    )
    dept_biz, _ = Department.objects.get_or_create(
        institute=institute,
        code='BUS',
        defaults={'name': 'Business Administration', 'description': 'Department of Business'}
    )
    print("Created Departments")

    # 3. Users
    admin, _ = CustomUser.objects.get_or_create(
        email='admin@gtu.edu',
        defaults={
            'full_name': 'Demo Admin',
            'role': CustomUser.Role.ADMIN,
            'institute': institute,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if _: admin.set_password('123456'); admin.save()

    teacher_cs, _ = CustomUser.objects.get_or_create(
        email='t.cs@gtu.edu',
        defaults={'full_name': 'Alan Turing', 'role': CustomUser.Role.TEACHER, 'institute': institute}
    )
    if _: teacher_cs.set_password('123456'); teacher_cs.save()

    teacher_math, _ = CustomUser.objects.get_or_create(
        email='t.math@gtu.edu',
        defaults={'full_name': 'Ada Lovelace', 'role': CustomUser.Role.TEACHER, 'institute': institute}
    )
    if _: teacher_math.set_password('123456'); teacher_math.save()

    teacher_biz, _ = CustomUser.objects.get_or_create(
        email='t.biz@gtu.edu',
        defaults={'full_name': 'Elon Musk', 'role': CustomUser.Role.TEACHER, 'institute': institute}
    )
    if _: teacher_biz.set_password('123456'); teacher_biz.save()

    student1, _ = CustomUser.objects.get_or_create(
        email='s1@gtu.edu',
        defaults={'full_name': 'John Student', 'role': CustomUser.Role.STUDENT, 'institute': institute}
    )
    if _: student1.set_password('123456'); student1.save()

    student2, _ = CustomUser.objects.get_or_create(
        email='s2@gtu.edu',
        defaults={'full_name': 'Jane Scholar', 'role': CustomUser.Role.STUDENT, 'institute': institute}
    )
    if _: student2.set_password('123456'); student2.save()
    
    student3, _ = CustomUser.objects.get_or_create(
        email='s3@gtu.edu',
        defaults={'full_name': 'Bob Learner', 'role': CustomUser.Role.STUDENT, 'institute': institute}
    )
    if _: student3.set_password('123456'); student3.save()
    print("Created Users")

    # 4. Courses
    course_ai, _ = Course.objects.get_or_create(
        institute=institute,
        code='CS401',
        semester='Fall',
        academic_year='2025-2026',
        section='A',
        defaults={
            'name': 'Introduction to Artificial Intelligence',
            'department': dept_cs,
            'description': 'Fundamentals of AI and Machine Learning',
            'credits': 3,
            'is_published': True
        }
    )
    course_ai.teachers.add(teacher_cs)
    course_ai.students.add(student1, student2, student3)

    course_calc, _ = Course.objects.get_or_create(
        institute=institute,
        code='MATH201',
        semester='Fall',
        academic_year='2025-2026',
        section='A',
        defaults={
            'name': 'Advanced Calculus',
            'department': dept_math,
            'description': 'Multivariable calculus and differential equations',
            'credits': 4,
            'is_published': True
        }
    )
    course_calc.teachers.add(teacher_math)
    course_calc.students.add(student1, student2)

    course_mktg, _ = Course.objects.get_or_create(
        institute=institute,
        code='BUS101',
        semester='Fall',
        academic_year='2025-2026',
        section='A',
        defaults={
            'name': 'Marketing Principles',
            'department': dept_biz,
            'description': 'Introduction to modern marketing strategies',
            'credits': 3,
            'is_published': True
        }
    )
    course_mktg.teachers.add(teacher_biz)
    course_mktg.students.add(student2, student3)
    print("Created Courses")

    # 5. Content
    now = timezone.now()
    
    # Lectures
    Lecture.objects.get_or_create(course=course_ai, title='Lecture 1: What is AI?', defaults={'description': 'Overview of AI history and concepts.', 'scheduled_date': now - timedelta(days=5)})
    Lecture.objects.get_or_create(course=course_ai, title='Lecture 2: Neural Networks', defaults={'description': 'Deep dive into perceptrons and MLPs.', 'scheduled_date': now - timedelta(days=2)})
    Lecture.objects.get_or_create(course=course_calc, title='Lecture 1: Limits & Continuity', defaults={'description': 'A review of limits.', 'scheduled_date': now - timedelta(days=4)})
    Lecture.objects.get_or_create(course=course_mktg, title='Lecture 1: The 4 Ps of Marketing', defaults={'description': 'Product, Price, Place, Promotion.', 'scheduled_date': now - timedelta(days=3)})

    # Assignments
    Assignment.objects.get_or_create(course=course_ai, title='Assignment 1: Build a Perceptron', defaults={'description': 'Implement a perceptron in Python.', 'due_date': now + timedelta(days=5)})
    Assignment.objects.get_or_create(course=course_calc, title='Problem Set 1', defaults={'description': 'Solve limits 1-20.', 'due_date': now + timedelta(days=3)})

    # Quizzes
    quiz1, _ = Quiz.objects.get_or_create(course=course_ai, title='Pop Quiz 1: AI Basics', defaults={'instructions': 'Answer carefully.', 'is_published': True})
    if _:
        Question.objects.create(quiz=quiz1, text='Who is considered the father of computer science?', question_type='MCQ', options=['Alan Turing', 'Albert Einstein', 'Isaac Newton', 'Nikola Tesla'], correct_answer='0', points=1)
        Question.objects.create(quiz=quiz1, text='What does AI stand for?', question_type='MCQ', options=['Artificial Intel', 'Automatic Intelligence', 'Artificial Intelligence', 'Alien Intelligence'], correct_answer='2', points=1)

    # Announcements
    Announcement.objects.get_or_create(institute=institute, title='Welcome to Fall 2025!', defaults={'content': 'Welcome back to campus! Let us make this semester great.', 'author': admin, 'target_role': 'ALL'})
    Announcement.objects.get_or_create(institute=institute, course=course_ai, title='AI Project Guidelines', defaults={'content': 'Please review the syllabus for project rules.', 'author': teacher_cs, 'target_role': 'STUDENT'})

    print("Created Content (Lectures, Assignments, Quizzes, Announcements)")
    print("\n--- DEMO DATA CREATED SUCCESSFULLY ---")
    print("Institute Code: GTU")
    print("Admin: admin@gtu.edu | pass: 123456")
    print("Teachers:")
    print("  - t.cs@gtu.edu (Alan Turing)")
    print("  - t.math@gtu.edu (Ada Lovelace)")
    print("  - t.biz@gtu.edu (Elon Musk)")
    print("Students:")
    print("  - s1@gtu.edu (John Student)")
    print("  - s2@gtu.edu (Jane Scholar)")
    print("  - s3@gtu.edu (Bob Learner)")

if __name__ == '__main__':
    seed_data()
