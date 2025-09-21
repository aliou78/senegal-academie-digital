from rest_framework import permissions

class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Read allowed to anyone. Write only to course instructor or staff/superuser.
    Works for Course instances and for objects with .course attribute (Module).
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        # try to get instructor from object
        instructor = None
        if hasattr(obj, 'instructor'):
            instructor = obj.instructor
        elif hasattr(obj, 'course') and hasattr(obj.course, 'instructor'):
            instructor = obj.course.instructor
        return user and user.is_authenticated and (user.is_staff or user.is_superuser or user == instructor)
    