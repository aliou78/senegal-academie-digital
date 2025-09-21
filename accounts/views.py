from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from .models import User, UserProfile, InstructorProfile, EnterpriseProfile
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserProfileExtendedSerializer, InstructorProfileSerializer, 
    EnterpriseProfileSerializer, UserListSerializer, PasswordChangeSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Inscription d'un nouvel utilisateur
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        # Créer le profil utilisateur
        UserProfile.objects.create(user=user)
        
        # Créer le profil spécialisé selon le rôle
        if user.role == 'instructor':
            InstructorProfile.objects.create(user=user)
        elif user.role == 'enterprise':
            EnterpriseProfile.objects.create(user=user)
        
        return Response({
            'message': 'Utilisateur créé avec succès',
            'user': UserProfileSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Connexion d'un utilisateur
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Connexion réussie',
            'user': UserProfileSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Déconnexion d'un utilisateur
    """
    try:
        request.user.auth_token.delete()
    except:
        pass
    
    logout(request)
    return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Récupérer ou modifier le profil de l'utilisateur connecté
    """
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def extended_profile(request):
    """
    Récupérer ou modifier le profil étendu de l'utilisateur
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = UserProfileExtendedSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileExtendedSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def instructor_profile(request):
    """
    Récupérer ou modifier le profil formateur
    """
    if request.user.role != 'instructor':
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    profile, created = InstructorProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = InstructorProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = InstructorProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def enterprise_profile(request):
    """
    Récupérer ou modifier le profil entreprise
    """
    if request.user.role != 'enterprise':
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    profile, created = EnterpriseProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = EnterpriseProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = EnterpriseProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Changer le mot de passe de l'utilisateur
    """
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Mot de passe modifié avec succès'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """
    Liste des utilisateurs (pour les administrateurs)
    """
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'is_verified', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']

    def get_queryset(self):
        # Seuls les administrateurs peuvent voir tous les utilisateurs
        if self.request.user.role == 'admin':
            return User.objects.all()
        return User.objects.none()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request, user_id):
    """
    Détails d'un utilisateur spécifique
    """
    user = get_object_or_404(User, id=user_id)
    
    # Vérifier les permissions
    if request.user.role != 'admin' and request.user != user:
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = UserProfileSerializer(user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_user(request, user_id):
    """
    Vérifier un utilisateur (pour les administrateurs)
    """
    if request.user.role != 'admin':
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    user = get_object_or_404(User, id=user_id)
    user.is_verified = True
    user.save()
    
    return Response({'message': 'Utilisateur vérifié avec succès'}, status=status.HTTP_200_OK)
