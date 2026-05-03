#!/usr/bin/env python
"""
Django ORM script to populate test data
Run: python populate_data.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classora.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from accounts.models import CustomUser, Institute
from lms.models import Department, Course
from django.db import transaction

# Institute ID (Classora Academy)
INSTITUTE_ID = 1

# Passwords (plain text - will be hashed by Django)
TEACHER_PASSWORD = 'teacher123'
STUDENT_PASSWORD = 'student123'

def create_departments():
    """Create 5 departments"""
    departments_data = [
        ('Computer Science', 'CS', 'Department of Computer Science and Engineering'),
        ('Mathematics', 'MATH', 'Department of Mathematics and Statistics'),
        ('Physics', 'PHYS', 'Department of Physics and Astronomy'),
        ('English Literature', 'ENG', 'Department of English and Literature'),
        ('Business Administration', 'BUS', 'Department of Business and Management'),
    ]
    
    depts = []
    for name, code, desc in departments_data:
        try:
            dept = Department.objects.get(code=code, institute_id=INSTITUTE_ID)
            print(f"Department already exists: {name}")
        except Department.DoesNotExist:
            dept = Department.objects.create(
                name=name,
                code=code,
                description=desc,
                institute_id=INSTITUTE_ID
            )
            print(f"Created department: {name}")
        depts.append(dept)
    
    return depts

def create_teachers():
    """Create 8 teachers"""
    teachers_data = [
        ('Dr. Ahmed Hassan', 'ahmed.hassan@classora.edu'),
        ('Prof. Sarah Johnson', 'sarah.johnson@classora.edu'),
        ('Dr. Muhammad Ali', 'muhammad.ali@classora.edu'),
        ('Prof. Emily Chen', 'emily.chen@classora.edu'),
        ('Dr. James Wilson', 'james.wilson@classora.edu'),
        ('Prof. Fatima Zahra', 'fatima.zahra@classora.edu'),
        ('Dr. Robert Brown', 'robert.brown@classora.edu'),
        ('Prof. Ayesha Khan', 'ayesha.khan@classora.edu'),
    ]
    
    teachers = []
    for full_name, email in teachers_data:
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'role': 'TEACHER',
                'is_active': True,
                'is_staff': False,
                'institute_id': INSTITUTE_ID
            }
        )
        if created:
            user.set_password(TEACHER_PASSWORD)
            user.save()
            print(f"Created teacher: {full_name} ({email})")
        else:
            print(f"Teacher already exists: {full_name}")
        teachers.append(user)
    
    return teachers

def create_students():
    """Create 15 students"""
    students_data = [
        ('Ali Khan', 'ali.khan@student.classora.edu'),
        ('Sana Ahmed', 'sana.ahmed@student.classora.edu'),
        ('Bilal Hassan', 'bilal.hassan@student.classora.edu'),
        ('Maria Iqbal', 'maria.iqbal@student.classora.edu'),
        ('Usman Ghani', 'usman.ghani@student.classora.edu'),
        ('Hira Sheikh', 'hira.sheikh@student.classora.edu'),
        ('Tariq Mehmood', 'tariq.mehmood@student.classora.edu'),
        ('Nida Fatima', 'nida.fatima@student.classora.edu'),
        ('Kamran Shah', 'kamran.shah@student.classora.edu'),
        ('Zainab Ali', 'zainab.ali@student.classora.edu'),
        ('Farhan Saeed', 'farhan.saeed@student.classora.edu'),
        ('Amina Begum', 'amina.begum@student.classora.edu'),
        ('Rashid Khan', 'rashid.khan@student.classora.edu'),
        ('Sofia Noor', 'sofia.noor@student.classora.edu'),
        ('Imran Javed', 'imran.javed@student.classora.edu'),
    ]
    
    students = []
    for full_name, email in students_data:
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'role': 'STUDENT',
                'is_active': True,
                'is_staff': False,
                'institute_id': INSTITUTE_ID
            }
        )
        if created:
            user.set_password(STUDENT_PASSWORD)
            user.save()
            print(f"Created student: {full_name} ({email})")
        else:
            print(f"Student already exists: {full_name}")
        students.append(user)
    
    return students

def create_courses(departments):
    """Create 12 courses"""
    courses_data = [
        # Computer Science
        ('Introduction to Programming', 'CS101', departments[0], 'Fall 2026', 'Basic programming concepts using Python', 'code', 3, 'A'),
        ('Data Structures', 'CS201', departments[0], 'Fall 2026', 'Advanced data structures and algorithms', 'storage', 3, 'A'),
        ('Web Development', 'CS301', departments[0], 'Fall 2026', 'Full-stack web development', 'web', 3, 'B'),
        ('Database Systems', 'CS202', departments[0], 'Spring 2026', 'Database design and SQL', 'storage', 3, 'A'),
        # Mathematics
        ('Calculus I', 'MATH101', departments[1], 'Fall 2026', 'Limits, derivatives, integrals', 'functions', 4, 'A'),
        ('Linear Algebra', 'MATH201', departments[1], 'Fall 2026', 'Matrices and vectors', 'grid_on', 3, 'A'),
        # Physics
        ('Physics I', 'PHYS101', departments[2], 'Fall 2026', 'Mechanics and thermodynamics', 'science', 4, 'A'),
        ('Physics II', 'PHYS102', departments[2], 'Spring 2026', 'Electricity and magnetism', 'bolt', 4, 'A'),
        # English
        ('English Composition', 'ENG101', departments[3], 'Fall 2026', 'Academic writing', 'edit', 3, 'A'),
        ('Creative Writing', 'ENG201', departments[3], 'Spring 2026', 'Fiction and poetry', 'create', 3, 'A'),
        # Business
        ('Principles of Management', 'BUS101', departments[4], 'Fall 2026', 'Business management', 'business', 3, 'A'),
        ('Marketing Fundamentals', 'BUS201', departments[4], 'Fall 2026', 'Marketing strategies', 'trending_up', 3, 'A'),
    ]
    
    courses = []
    for name, code, dept, semester, desc, icon, credits, section in courses_data:
        try:
            course = Course.objects.get(code=code, institute_id=INSTITUTE_ID)
            print(f"Course already exists: {name}")
        except Course.DoesNotExist:
            course = Course.objects.create(
                name=name,
                code=code,
                department=dept,
                semester=semester,
                description=desc,
                icon=icon,
                credits=credits,
                duration_weeks=16,
                max_students=50,
                is_published=True,
                institute_id=INSTITUTE_ID,
                academic_year='2026-2027',
                section=section
            )
            print(f"Created course: {name} ({code})")
        courses.append(course)
    
    return courses

def assign_teachers_to_courses(teachers, courses):
    """Assign teachers to courses"""
    # CS courses -> Teachers 0, 1
    # Math courses -> Teachers 2, 3
    # Physics courses -> Teachers 4, 5
    # English courses -> Teachers 6, 7
    # Business courses -> Teachers 0, 1
    
    assignments = [
        (0, [0, 1, 2, 3]),     # CS courses -> Teachers 0, 1
        (1, [4, 5]),           # Math courses -> Teachers 2, 3
        (2, [6, 7]),           # Physics courses -> Teachers 4, 5
        (3, [8, 9]),           # English courses -> Teachers 6, 7
        (4, [10, 11]),         # Business courses -> Teachers 0, 1
    ]
    
    for teacher_idx, course_indices in assignments:
        teacher = teachers[teacher_idx]
        for course_idx in course_indices:
            if course_idx < len(courses):
                course = courses[course_idx]
                course.teachers.add(teacher)
                print(f"Assigned {teacher.full_name} to {course.name}")

def enroll_students_in_courses(students, courses):
    """Enroll students in courses"""
    # Distribute students across courses
    enrollments = [
        (0, [0, 1, 2, 3, 4, 5, 6, 7]),      # CS101 -> Students 0-7
        (1, [0, 1, 2, 3, 4, 5]),             # CS201 -> Students 0-5
        (2, [2, 3, 4, 5, 6, 7, 8, 9]),      # CS301 -> Students 2-9
        (4, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]), # MATH101 -> Students 0-9
        (6, [4, 5, 6, 7, 8, 9, 10, 11]),    # PHYS101 -> Students 4-11
        (8, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]), # ENG101 -> Students 0-11
        (10, [8, 9, 10, 11, 12, 13, 14]),   # BUS101 -> Students 8-14
    ]
    
    for course_idx, student_indices in enrollments:
        if course_idx < len(courses):
            course = courses[course_idx]
            for student_idx in student_indices:
                if student_idx < len(students):
                    student = students[student_idx]
                    course.students.add(student)
                    print(f"Enrolled {student.full_name} in {course.name}")

def main():
    print("=" * 50)
    print("Populating Classora LMS with Test Data")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # 1. Create Departments
            print("\n1. Creating Departments...")
            departments = create_departments()
            
            # 2. Create Teachers
            print("\n2. Creating Teachers...")
            teachers = create_teachers()
            
            # 3. Create Students
            print("\n3. Creating Students...")
            students = create_students()
            
            # 4. Create Courses
            print("\n4. Creating Courses...")
            courses = create_courses(departments)
            
            # 5. Assign Teachers
            print("\n5. Assigning Teachers to Courses...")
            assign_teachers_to_courses(teachers, courses)
            
            # 6. Enroll Students
            print("\n6. Enrolling Students in Courses...")
            enroll_students_in_courses(students, courses)
            
            print("\n" + "=" * 50)
            print("✅ Test data population completed!")
            print("=" * 50)
            
            # Summary
            print(f"\n📊 Summary:")
            print(f"  - Departments: {len(departments)}")
            print(f"  - Teachers: {len(teachers)}")
            print(f"  - Students: {len(students)}")
            print(f"  - Courses: {len(courses)}")
            
            print(f"\n🔑 Login Credentials:")
            print(f"  - Teachers: email = firstname.lastname@classora.edu, password = {TEACHER_PASSWORD}")
            print(f"  - Students: email = firstname.lastname@student.classora.edu, password = {STUDENT_PASSWORD}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
