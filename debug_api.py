import os
import sys

# Add the project path
sys.path.append('c:\\Users\\surface\\Desktop\\classora-lms\\classora-lms')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classora.settings')

import django
django.setup()

from lms.serializers import CourseSerializer
from lms.models import Course, Department
from accounts.models import CustomUser, Institute

# Test the serializer directly
print("Testing CourseSerializer...")

# Get test data
admin = CustomUser.objects.filter(role='ADMIN').first()
if not admin:
    print("No admin user found!")
    sys.exit(1)

dept = Department.objects.filter(institute=admin.institute).first()
if not dept:
    print("No department found!")
    sys.exit(1)

teacher = CustomUser.objects.filter(role='TEACHER', institute=admin.institute).first()
if not teacher:
    print("No teacher found!")
    sys.exit(1)

# Test data
test_data = {
    "name": "Test Course API",
    "code": "TEST101", 
    "department": dept.id,
    "semester": "Fall",
    "academic_year": "2025-2026",
    "section": "A",
    "description": "Test course description",
    "credits": 3,
    "duration_weeks": 16,
    "max_students": 50,
    "is_published": False,
    "assigned_teachers": [teacher.id] if teacher else []
}

print(f"Test data: {test_data}")

# Test serializer
serializer = CourseSerializer(data=test_data)
if serializer.is_valid():
    print("✓ Serializer is valid!")
    print(f"Validated data: {serializer.validated_data}")
else:
    print("✗ Serializer errors:")
    for field, errors in serializer.errors.items():
        print(f"  {field}: {errors}")

# Check if course already exists
existing = Course.objects.filter(
    institute=admin.institute,
    code="TEST101",
    semester="Fall", 
    academic_year="2025-2026",
    section="A"
).exists()

print(f"Course already exists: {existing}")

print("\nDebug complete!")
