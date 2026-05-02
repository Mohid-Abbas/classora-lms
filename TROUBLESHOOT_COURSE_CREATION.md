# Course Creation Troubleshooting Guide

## Error: "Failed to create course. Check your inputs."

### Most Common Causes:

1. **Department ID doesn't exist** - The department ID sent from frontend doesn't exist in database
2. **Teacher ID doesn't exist** - The teacher ID in assigned_teachers doesn't exist or isn't a TEACHER
3. **User not authenticated** - The API request doesn't include proper authentication
4. **Duplicate course** - Course with same code/semester/year/section already exists

### How to Debug:

#### Step 1: Check Browser Console
1. Open browser developer tools (F12)
2. Go to Console tab
3. Try creating a course
4. Look for error messages like:
   ```
   Course creation error: Error: Request failed with status code 400
   Error response: {detail: "Department is invalid for your institute."}
   Error status: 400
   ```

#### Step 2: Check Required Data
Make sure you have:
- At least one department in your institute
- At least one teacher with role='TEACHER' in your institute
- Logged in as ADMIN user

#### Step 3: Verify Data in Database
Run these checks in Django admin or shell:
```python
# Check departments
from lms.models import Department
from accounts.models import CustomUser

# Get current user
user = CustomUser.objects.get(email="your_admin@email.com")

# Check departments in your institute
departments = Department.objects.filter(institute=user.institute)
print(f"Departments: {list(departments.values('id', 'name'))}")

# Check teachers in your institute  
teachers = CustomUser.objects.filter(institute=user.institute, role='TEACHER')
print(f"Teachers: {list(teachers.values('id', 'email', 'full_name'))}")
```

### Fixes Applied:

1. **Enhanced Error Logging** - Frontend now shows detailed error messages
2. **Fixed Serializer Error** - Backend error logging bug fixed
3. **Better Validation** - Step validation properly integrated

### If Still Not Working:

1. **Start the Django server** and watch terminal for error messages
2. **Create test data** first:
   - Create a department
   - Create a teacher user
3. **Check the exact error** in browser console - it will tell you the specific field that's failing

### Expected Flow:
1. Fill all required fields in each step
2. Frontend validates before allowing next step
3. Backend validates again for security
4. Course created with "done": true response
