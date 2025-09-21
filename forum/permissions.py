from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Autorise modification/suppression uniquement à l'auteur ou au staff.
    Lecture autorisée à tous (si IsAuthenticatedOrReadOnly).
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # If object has 'author' field
        author = getattr(obj, "author", None)
        creator = getattr(obj, "created_by", None)
        # staff can do anything
        if request.user and request.user.is_staff:
            return True

        if author:
            return author == request.user
        if creator:
            return creator == request.user
        return False
