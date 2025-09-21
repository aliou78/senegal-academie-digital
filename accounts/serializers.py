from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, InstructorProfile, EnterpriseProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription des utilisateurs
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 
                 'phone', 'role', 'date_of_birth', 'gender', 'location', 'preferred_language')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion des utilisateurs
    """
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Identifiants invalides.')
            if not user.is_active:
                raise serializers.ValidationError('Ce compte est désactivé.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Username et password requis.')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil utilisateur
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 
                 'date_of_birth', 'gender', 'profile_picture', 'bio', 'location', 
                 'preferred_language', 'is_verified', 'date_joined')
        read_only_fields = ('id', 'username', 'is_verified', 'date_joined')


class UserProfileExtendedSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil étendu
    """
    class Meta:
        model = UserProfile
        fields = ('skills', 'experience', 'education', 'certifications', 
                 'social_links', 'notification_preferences')


class InstructorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil formateur
    """
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = InstructorProfile
        fields = ('id', 'user', 'title', 'company', 'years_of_experience', 
                 'specializations', 'hourly_rate', 'availability', 'is_approved', 'approval_date')
        read_only_fields = ('id', 'is_approved', 'approval_date')


class EnterpriseProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil entreprise
    """
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = EnterpriseProfile
        fields = ('id', 'user', 'company_name', 'company_type', 'industry', 
                 'company_size', 'website', 'description', 'contact_person', 'contact_phone')


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des utilisateurs
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'role', 
                 'profile_picture', 'is_verified', 'date_joined')


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer pour le changement de mot de passe
    """
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value
