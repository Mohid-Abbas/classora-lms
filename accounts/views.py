from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Institute, PasswordResetToken
from .permissions import IsAdminRole, IsStudentRole, IsTeacherRole
from .serializers import (
    CreateUserSerializer,
    InstituteRegisterSerializer,
    InstituteSerializer,
    LoginSerializer,
    UserSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])  # Public: used to bootstrap a new tenant + admin.
def institute_register(request):
    serializer = InstituteRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    result = serializer.save()
    institute = result["institute"]
    admin_user = result["admin_user"]

    return Response(
        {
            "message": "Institute registered successfully.",
            "institute": {
                "id": institute.id,
                "name": institute.name,
                "institute_code": institute.institute_code,
                "created_at": institute.created_at,
            },
            "admin": {
                "id": admin_user.id,
                "full_name": admin_user.full_name,
                "email": admin_user.email,
                "role": admin_user.role,
                "institute_id": institute.id,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])  # Public: returns JWTs for valid email/password.
def login(request):
    serializer = LoginSerializer(data=request.data, context={"request": request})
    if not serializer.is_valid():
        # Missing fields or invalid credentials.
        message = serializer.errors
        # For credential issues we standardize to 401.
        if isinstance(message, dict) and "non_field_errors" in message:
            return Response({"detail": message["non_field_errors"][0]}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.validated_data["user"]
    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "institute_id": user.institute_id,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])  # Example protected endpoint using JWT auth.
def me(request):
    user = request.user
    return Response(
        {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "institute_id": user.institute_id,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminRole])
def institute_detail(request, pk: int):
    """
    Return details of the admin's own institute.
    """
    institute = get_object_or_404(Institute, pk=pk)

    # Enforce tenant boundary: admin can only view their own institute.
    if request.user.institute_id != institute.id:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = InstituteSerializer(institute)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_list(request):
    """
    List all users that belong to the user's institute.
    Admin and teachers can view all users in their institute.
    """
    institute_id = request.query_params.get("institute")
    if not institute_id:
        return Response(
            {"detail": "The 'institute' query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if str(request.user.institute_id) != str(institute_id):
        return Response(
            {"detail": "You can only view users in your own institute."},
            status=status.HTTP_403_FORBIDDEN,
        )

    search = request.query_params.get("search", "").strip()
    try:
        page = int(request.query_params.get("page", "1"))
    except ValueError:
        page = 1
    try:
        page_size = int(request.query_params.get("page_size", "10"))
    except ValueError:
        page_size = 10

    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)

    users_qs = CustomUser.objects.filter(institute_id=institute_id)
    role = request.query_params.get("role")
    if role:
        users_qs = users_qs.filter(role=role)
        
    if search:
        users_qs = users_qs.filter(
            Q(full_name__icontains=search) | Q(email__icontains=search)
        )

    total = users_qs.count()
    start = (page - 1) * page_size
    end = start + page_size

    users = users_qs.order_by("full_name")[start:end]
    serializer = UserSerializer(users, many=True)

    return Response(
        {
            "results": serializer.data,
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": end < total,
            "has_previous": start > 0,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminRole])
def create_user(request):
    """
    Create a new user in the admin's institute.
    """
    serializer = CreateUserSerializer(data=request.data, context={"request": request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    output = UserSerializer(user)
    return Response(output.data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdminRole])
def delete_user(request, pk: int):
    """
    Delete a user from the admin's institute.
    """
    user_to_delete = get_object_or_404(CustomUser, pk=pk)
    
    # Ensure they only delete within their own institute
    if request.user.institute_id != user_to_delete.institute_id:
        return Response({"detail": "Not found or permission denied."}, status=status.HTTP_404_NOT_FOUND)
        
    # Prevent admin from deleting themselves
    if request.user.id == user_to_delete.id:
        return Response({"detail": "Cannot delete your own admin account."}, status=status.HTTP_400_BAD_REQUEST)
        
    user_to_delete.delete()
    return Response({"detail": "User securely deleted"}, status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTeacherRole])
def teacher_dashboard(request):
    """
    Teacher dashboard data: includes students in institute and courses assigned to this teacher.
    """
    from lms.models import Course
    from lms.serializers import CourseSerializer
    
    user = request.user

    students = CustomUser.objects.filter(
        institute_id=user.institute_id, role=CustomUser.Role.STUDENT
    ).order_by("full_name")
    students_serialized = UserSerializer(students, many=True)

    courses = Course.objects.filter(teachers=user)
    courses_serialized = CourseSerializer(courses, many=True)

    return Response(
        {
            "user": UserSerializer(user).data,
            "students": students_serialized.data,
            "courses": courses_serialized.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudentRole])
def student_dashboard(request):
    """
    Student dashboard data: includes institute info and courses the student is enrolled in.
    """
    from lms.models import Course
    from lms.serializers import CourseSerializer
    
    user = request.user
    institute = user.institute

    institute_data = None
    if institute is not None:
        institute_data = InstituteSerializer(institute).data

    courses = Course.objects.filter(students=user, is_published=True)
    courses_serialized = CourseSerializer(courses, many=True)

    return Response(
        {
            "user": UserSerializer(user).data,
            "institute": institute_data,
            "courses": courses_serialized.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Send password reset email to user.
    Does not reveal whether email exists for security.
    """
    email = request.data.get("email", "").strip().lower()
    
    if not email:
        return Response(
            {"detail": "Email address is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = CustomUser.objects.get(email=email)

        # Only send codes for users that are part of an institute (tenant validation)
        if user.institute is None:
            # Do not reveal user existence; behave as if email sent
            return Response(
                {"detail": "If an account with this email exists, a verification code has been sent."},
                status=status.HTTP_200_OK
            )

        # Generate verification code (6-digit) and persist
        reset_token = PasswordResetToken.generate_verification_code(user)

        # Send email with the numeric code (no link)
        subject = "Your Classora LMS password reset code"
        message = f"""
Hello {user.full_name},

You requested a password reset for your Classora LMS account.

Use the following verification code to reset your password:

{reset_token.verification_code}

This code will expire in 30 minutes.

If you didn't request this password reset, you can safely ignore this email.

Best regards,
Classora LMS Team
"""

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            print(f"Password reset code email sent successfully to {user.email}")
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            print(f"Email settings: Host={settings.EMAIL_HOST}, Port={settings.EMAIL_PORT}, User={settings.EMAIL_HOST_USER}")
            return Response(
                {"detail": "Failed to send reset email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except CustomUser.DoesNotExist:
        # Don't reveal that email doesn't exist
        pass
    
    # Always return success message to prevent user enumeration
    return Response(
        {"detail": "If an account with this email exists, a password reset link has been sent."},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password using verification code sent via email.
    """
    email = request.data.get("email", "").strip().lower()
    code = request.data.get("code", "").strip()
    new_password = request.data.get("new_password", "")

    if not email or not code or not new_password:
        return Response(
            {"detail": "Email, code and new password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {"detail": "Password must be at least 8 characters long."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        reset_token = PasswordResetToken.objects.get(user__email=email, verification_code=code, is_used=False)

        if not reset_token.is_valid():
            return Response({"detail": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)

        # Reset password
        user = reset_token.user
        user.set_password(new_password)
        user.save()

        # Mark code as used
        reset_token.mark_as_used()

        return Response({"detail": "Password reset successfully. You can now login with your new password."}, status=status.HTTP_200_OK)

    except PasswordResetToken.DoesNotExist:
        return Response({"detail": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)
