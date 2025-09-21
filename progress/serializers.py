from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Badge, UserBadge, Certificate, UserCertificate, LearningPath,
    LearningPathCourse, UserLearningPath, Achievement, StudySession, UserStatistics
)

User = get_user_model()


class BadgeSerializer(serializers.ModelSerializer):
    """
    Serializer pour les badges
    """
    class Meta:
        model = Badge
        fields = ('id', 'name', 'description', 'icon', 'color', 'badge_type', 'criteria', 'is_active', 'created_at')


class UserBadgeSerializer(serializers.ModelSerializer):
    """
    Serializer pour les badges des utilisateurs
    """
    badge = BadgeSerializer(read_only=True)
    badge_name = serializers.CharField(source='badge.name', read_only=True)
    badge_icon = serializers.CharField(source='badge.icon', read_only=True)
    badge_color = serializers.CharField(source='badge.color', read_only=True)

    class Meta:
        model = UserBadge
        fields = ('id', 'badge', 'badge_name', 'badge_icon', 'badge_color', 'earned_at', 'is_visible')


class CertificateSerializer(serializers.ModelSerializer):
    """
    Serializer pour les certificats
    """
    class Meta:
        model = Certificate
        fields = ('id', 'name', 'description', 'certificate_type', 'template', 'background_image', 'requirements', 'is_active', 'created_at')


class UserCertificateSerializer(serializers.ModelSerializer):
    """
    Serializer pour les certificats des utilisateurs
    """
    certificate = CertificateSerializer(read_only=True)
    certificate_name = serializers.CharField(source='certificate.name', read_only=True)
    certificate_type = serializers.CharField(source='certificate.certificate_type', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.get_full_name', read_only=True)

    class Meta:
        model = UserCertificate
        fields = ('id', 'certificate', 'certificate_name', 'certificate_type', 'course', 'course_title',
                 'issued_at', 'issued_by', 'issued_by_name', 'certificate_data', 'pdf_file',
                 'is_verified', 'verification_code')


class LearningPathSerializer(serializers.ModelSerializer):
    """
    Serializer pour les parcours d'apprentissage
    """
    courses_count = serializers.SerializerMethodField()
    enrolled_users_count = serializers.SerializerMethodField()

    class Meta:
        model = LearningPath
        fields = ('id', 'name', 'description', 'slug', 'duration_weeks', 'difficulty_level',
                 'thumbnail', 'is_active', 'courses_count', 'enrolled_users_count', 'created_at')

    def get_courses_count(self, obj):
        return obj.courses.count()

    def get_enrolled_users_count(self, obj):
        return obj.users.filter(is_active=True).count()


class LearningPathCourseSerializer(serializers.ModelSerializer):
    """
    Serializer pour les cours dans un parcours
    """
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_description = serializers.CharField(source='course.short_description', read_only=True)
    course_thumbnail = serializers.SerializerMethodField()
    course_duration = serializers.IntegerField(source='course.duration_hours', read_only=True)
    course_level = serializers.CharField(source='course.level', read_only=True)

    class Meta:
        model = LearningPathCourse
        fields = ('id', 'course', 'course_title', 'course_description', 'course_thumbnail',
                 'course_duration', 'course_level', 'order', 'is_required')

    def get_course_thumbnail(self, obj):
        if obj.course.thumbnail:
            return obj.course.thumbnail.url
        return None


class LearningPathDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour les parcours d'apprentissage
    """
    courses = LearningPathCourseSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = LearningPath
        fields = ('id', 'name', 'description', 'slug', 'duration_weeks', 'difficulty_level',
                 'thumbnail', 'is_active', 'courses', 'is_enrolled', 'user_progress', 'created_at')

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.users.filter(user=request.user, is_active=True).exists()
        return False

    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_path = obj.users.filter(user=request.user, is_active=True).first()
            if user_path:
                return {
                    'progress_percentage': user_path.progress_percentage,
                    'enrolled_at': user_path.enrolled_at,
                    'completed_at': user_path.completed_at,
                }
        return None


class UserLearningPathSerializer(serializers.ModelSerializer):
    """
    Serializer pour les parcours d'apprentissage des utilisateurs
    """
    learning_path = LearningPathSerializer(read_only=True)
    learning_path_name = serializers.CharField(source='learning_path.name', read_only=True)

    class Meta:
        model = UserLearningPath
        fields = ('id', 'learning_path', 'learning_path_name', 'enrolled_at', 'completed_at',
                 'progress_percentage', 'is_active')


class AchievementSerializer(serializers.ModelSerializer):
    """
    Serializer pour les réalisations
    """
    class Meta:
        model = Achievement
        fields = ('id', 'achievement_type', 'title', 'description', 'data', 'earned_at', 'is_visible')


class StudySessionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les sessions d'étude
    """
    course_title = serializers.CharField(source='course.title', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = StudySession
        fields = ('id', 'course', 'course_title', 'lesson', 'lesson_title', 'started_at',
                 'ended_at', 'duration_minutes', 'progress_made')


class UserStatisticsSerializer(serializers.ModelSerializer):
    """
    Serializer pour les statistiques des utilisateurs
    """
    completion_rate = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = UserStatistics
        fields = ('total_courses_enrolled', 'total_courses_completed', 'total_lessons_completed',
                 'total_time_spent_minutes', 'current_streak_days', 'longest_streak_days',
                 'total_certificates_earned', 'total_badges_earned', 'total_quizzes_taken',
                 'total_quizzes_passed', 'average_quiz_score', 'completion_rate', 'success_rate',
                 'last_updated')

    def get_completion_rate(self, obj):
        if obj.total_courses_enrolled > 0:
            return round((obj.total_courses_completed / obj.total_courses_enrolled) * 100, 1)
        return 0

    def get_success_rate(self, obj):
        if obj.total_quizzes_taken > 0:
            return round((obj.total_quizzes_passed / obj.total_quizzes_taken) * 100, 1)
        return 0


class LearningPathEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription à un parcours d'apprentissage
    """
    class Meta:
        model = UserLearningPath
        fields = ('learning_path',)

    def create(self, validated_data):
        user = self.context['request'].user
        learning_path = validated_data['learning_path']
        
        # Vérifier si déjà inscrit
        enrollment, created = UserLearningPath.objects.get_or_create(
            user=user,
            learning_path=learning_path,
            defaults={'is_active': True}
        )
        
        if not created and not enrollment.is_active:
            enrollment.is_active = True
            enrollment.save()
        
        return enrollment


class CertificateVerificationSerializer(serializers.Serializer):
    """
    Serializer pour la vérification de certificat
    """
    verification_code = serializers.CharField(max_length=20)

    def validate_verification_code(self, value):
        try:
            certificate = UserCertificate.objects.get(verification_code=value)
            return value
        except UserCertificate.DoesNotExist:
            raise serializers.ValidationError("Code de vérification invalide")


class ProgressUpdateSerializer(serializers.Serializer):
    """
    Serializer pour mettre à jour la progression
    """
    lesson_id = serializers.IntegerField()
    is_completed = serializers.BooleanField()
    time_spent = serializers.IntegerField(default=0)
    last_position = serializers.IntegerField(default=0)

    def validate_lesson_id(self, value):
        from courses.models import Lesson
        try:
            lesson = Lesson.objects.get(id=value)
            return value
        except Lesson.DoesNotExist:
            raise serializers.ValidationError("Leçon non trouvée")


class BadgeAwardSerializer(serializers.Serializer):
    """
    Serializer pour attribuer un badge
    """
    user_id = serializers.IntegerField()
    badge_id = serializers.IntegerField()

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé")

    def validate_badge_id(self, value):
        try:
            badge = Badge.objects.get(id=value)
            return value
        except Badge.DoesNotExist:
            raise serializers.ValidationError("Badge non trouvé")
