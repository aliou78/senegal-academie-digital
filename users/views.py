from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth import authenticate

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Payload: username, email, first_name, last_name, password, password2, optional profile {role,bio}
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT /api/auth/profile/  (auth required)
    """
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.UpdateAPIView):
    """
    PUT /api/auth/change-password/
    Payload: old_password, new_password
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data.get("old_password")
        new_password = serializer.validated_data.get("new_password")

        if not self.object.check_password(old_password):
            return Response({"old_password": "Ancien mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        self.object.set_password(new_password)
        self.object.save()
        return Response({"detail": "Mot de passe changé avec succès."}, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/users/  (admin only)
    """
    queryset = User.objects.select_related("profile").all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
