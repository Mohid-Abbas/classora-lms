import sys
import os
import django
import random
from django.utils import timezone
from datetime import timedelta

# Set up Django
sys.path.append(r'd:\Projects\FSE_Project\classora-lms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classora.settings')
django.setup()

from accounts.models import Institute, CustomUser
from lms.models import Department, Course, Lecture, Assignment, Quiz, Question, Announcement, AttendanceRecord, AttendanceEntry, QuizAttempt

def seed_data():
    print("Generating Massive Demo Institute Data for FAST NUCES...")

    # Name Lists for Random Generation
    first_names = ['Ali', 'Ayesha', 'Bilal', 'Fatima', 'Hassan', 'Zainab', 'Usman', 'Khadija', 'Omar', 'Maryam', 'Hamza', 'Sana', 'Ibrahim', 'Hira', 'Tariq', 'Sadia', 'Saad', 'Nida', 'Fahad', 'Rabia', 'Kamran', 'Mehwish', 'Imran', 'Nazia', 'Waqas', 'Amina', 'Junaid', 'Sobia', 'Adil', 'Saira', 'Shahzaib', 'Mahnoor', 'Rizwan', 'Kiran', 'Yasir', 'Nadia', 'Farhan', 'Uzma', 'Salman', 'Bushra']
    last_names = ['Khan', 'Ahmed', 'Ali', 'Qureshi', 'Malik', 'Shah', 'Mehmood', 'Hussain', 'Raza', 'Abbas', 'Tariq', 'Sheikh', 'Nawaz', 'Baig', 'Mirza', 'Siddiqui', 'Zafar', 'Aslam', 'Iqbal', 'Chaudhry']

    # 1. Institute
    institute, _ = Institute.objects.get_or_create(
        institute_code='FAST',
        defaults={
            'name': 'FAST NUCES Islamabad',
            'primary_color': '#111827',
            'description': 'Foundation for Advancement of Science and Technology.',
            'website': 'https://isb.nu.edu.pk',
            'contact_email': 'info@isb.nu.edu.pk',
            'phone': '+92-51-111-128-128',
            'academic_year': '2025-2026',
            'semester': 'Spring'
        }
    )
    print(f"Institute: {institute.name}")

    # 2. Departments
    depts = [
        ('CS', 'Computer Science', 'Department of Computer Science'),
        ('SE', 'Software Engineering', 'Department of Software Engineering'),
        ('EE', 'Electrical Engineering', 'Department of Electrical Engineering'),
        ('MS', 'Management Sciences', 'Department of Management Sciences')
    ]
    db_depts = []
    for code, name, desc in depts:
        d, _ = Department.objects.get_or_create(institute=institute, code=code, defaults={'name': name, 'description': desc})
        db_depts.append(d)
    print(f"Created {len(db_depts)} Departments")

    # 3. Users
    # Admin
    admin_email = 'i240074@isb.nu.edu.pk'
    admin, _ = CustomUser.objects.get_or_create(
        email=admin_email,
        defaults={
            'full_name': 'Super Admin',
            'role': CustomUser.Role.ADMIN,
            'institute': institute,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if _: admin.set_password('123456'); admin.save()

    # Teachers (20)
    db_teachers = []
    for i in range(1, 21):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"teacher{i}@isb.nu.edu.pk"
        t, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={'full_name': f"{fn} {ln}", 'role': CustomUser.Role.TEACHER, 'institute': institute}
        )
        if created:
            t.set_password('123456'); t.save()
        db_teachers.append(t)
    print(f"Created {len(db_teachers)} Teachers")

    # Students (100)
    db_students = []
    for i in range(1, 101):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        roll = 2000 + i
        email = f"i24{roll}@isb.nu.edu.pk"
        s, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={'full_name': f"{fn} {ln}", 'role': CustomUser.Role.STUDENT, 'institute': institute}
        )
        if created:
            s.set_password('123456'); s.save()
        db_students.append(s)
    print(f"Created {len(db_students)} Students")

    # 4. Courses (8)
    course_data = [
        ('CS101', 'Programming Fundamentals', db_depts[0]),
        ('CS201', 'Data Structures', db_depts[0]),
        ('SE301', 'Software Requirement Engineering', db_depts[1]),
        ('SE401', 'Software Quality Assurance', db_depts[1]),
        ('EE101', 'Linear Circuit Analysis', db_depts[2]),
        ('EE201', 'Digital Logic Design', db_depts[2]),
        ('MS101', 'Principles of Management', db_depts[3]),
        ('MS201', 'Marketing Management', db_depts[3]),
    ]
    
    db_courses = []
    for idx, (code, name, dept) in enumerate(course_data):
        c, _ = Course.objects.get_or_create(
            institute=institute,
            code=code,
            semester='Spring',
            academic_year='2025-2026',
            section='A',
            defaults={
                'name': name,
                'department': dept,
                'description': f'Core course for {dept.name}',
                'credits': 3,
                'is_published': True
            }
        )
        # Assign 2-3 random teachers to this course
        c.teachers.add(*random.sample(db_teachers, k=random.randint(2, 3)))
        
        # Assign 50-70 random students to this course
        assigned_students = random.sample(db_students, k=random.randint(50, 70))
        c.students.add(*assigned_students)
        db_courses.append(c)
    print(f"Created {len(db_courses)} Courses and Enrolled Students")

    # 5. Announcements (5+)
    announcements = [
        ('Spring 2025 Midterms', 'Midterms will start from next week. Best of luck!'),
        ('Sports Week', 'Annual sports week is scheduled for the end of the month.'),
        ('Seminar on AI', 'A guest speaker from Google will be discussing Generative AI.'),
        ('Fee Submission Deadline', 'Please submit your dues by the 15th to avoid fine.'),
        ('Campus Drive', 'Tech companies are arriving for recruitment. Seniors please update resumes.'),
    ]
    for title, content in announcements:
        Announcement.objects.get_or_create(
            institute=institute, 
            title=title, 
            defaults={'content': content, 'author': admin, 'target_role': 'ALL'}
        )
    print("Created 5 Announcements")

    # 6. Quizzes (3 per course) & Quiz Attempts
    now = timezone.now()
    quiz_questions = [
        {'text': 'What is the primary key in a database?', 'options': ['Unique Identifier', 'Foreign Key', 'Index', 'String'], 'ans': '0'},
        {'text': 'What does CPU stand for?', 'options': ['Central Process Unit', 'Central Processing Unit', 'Computer Personal Unit', 'Central Processor Unit'], 'ans': '1'},
        {'text': 'Which of the following is not an OS?', 'options': ['Windows', 'Linux', 'Oracle', 'DOS'], 'ans': '2'},
    ]
    
    for c in db_courses:
        for q_num in range(1, 4):
            quiz, created = Quiz.objects.get_or_create(
                course=c, 
                title=f'Quiz {q_num}: {c.name} Basics', 
                defaults={
                    'instructions': 'Attempt all questions. Time limit is 15 mins.', 
                    'total_time_minutes': 15,
                    'is_published': True
                }
            )
            
            if created:
                for q_data in quiz_questions:
                    Question.objects.create(
                        quiz=quiz, 
                        text=q_data['text'], 
                        question_type='MCQ', 
                        options=q_data['options'], 
                        correct_answer=q_data['ans'], 
                        points=1
                    )
            
            # 7. Attempt Quizzes for Analytics
            # Get students in course
            course_students = list(c.students.all())
            # Randomly select 60-90% of students to attempt
            attempters = random.sample(course_students, int(len(course_students) * random.uniform(0.6, 0.9)))
            for student in attempters:
                QuizAttempt.objects.get_or_create(
                    quiz=quiz,
                    student=student,
                    defaults={
                        'score': random.randint(0, 3), # Score between 0 and 3
                        'total_marks': 3,
                        'answers': {'1': '0', '2': '1', '3': '2'}, # Dummy answers
                        'time_taken_seconds': random.randint(100, 900)
                    }
                )
    print("Created Quizzes and Quiz Attempts for Analytics")

    # 8. Attendance (10 days)
    for c in db_courses:
        course_students = list(c.students.all())
        for day_offset in range(10):
            record_date = now.date() - timedelta(days=day_offset)
            record, _ = AttendanceRecord.objects.get_or_create(
                course=c,
                date=record_date
            )
            # Add entries for all students
            for student in course_students:
                # 80% present, 20% absent/late
                status_choice = random.choices(
                    ['PRESENT', 'ABSENT', 'LATE'], 
                    weights=[80, 15, 5], 
                    k=1
                )[0]
                AttendanceEntry.objects.get_or_create(
                    record=record,
                    student=student,
                    defaults={'status': status_choice}
                )
    print("Created 10 days of Attendance Records")

    print("\n--- MASSIVE DEMO DATA CREATED SUCCESSFULLY ---")
    print("Institute Code: FAST")
    print(f"Admin Email: {admin_email} | Password: 123456")

if __name__ == '__main__':
    seed_data()
