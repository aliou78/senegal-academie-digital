# progress/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CourseEnrollment, ModuleProgress, LessonProgress,
    QuizAttempt, StudySession, UserAchievement, LearningStreak
)

User = get_user_model()

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_thumbnail = serializers.CharField(source='course.thumbnail', read_only=True)
    estimated_completion_date = serializers.DateTimeField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'course_title', 'course_thumbnail',
            'status', 'enrolled_at', 'started_at', 'completed_at',
            'last_accessed', 'progress_percentage', 'total_time_spent',
            'current_grade', 'certificate_issued', 'certificate_date',
            'estimated_completion_date', 'is_completed'
        ]
        read_only_fields = ['enrolled_at', 'user']

class ModuleProgressSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source='module.title', read_only=True)
    module_order = serializers.IntegerField(source='module.order', read_only=True)
    
    class Meta:
        model = ModuleProgress
        fields = [
            'id', 'module', 'module_title', 'module_order',
            'is_started', 'is_completed', 'started_at', 'completed_at',
            'progress_percentage', 'time_spent', 'score'
        ]

class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_type = serializers.CharField(source='lesson.lesson_type', read_only=True)
    lesson_duration = serializers.IntegerField(source='lesson.estimated_duration', read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'lesson_title', 'lesson_type', 'lesson_duration',
            'status', 'started_at', 'completed_at', 'last_accessed',
            'progress_percentage', 'time_spent', 'current_position',
            'score', 'attempts', 'is_completed'
        ]

class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    quiz_passing_score = serializers.DecimalField(source='quiz.passing_score', max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'quiz_passing_score',
            'attempt_number', 'started_at', 'completed_at',
            'score', 'total_questions', 'correct_answers',
            'time_taken', 'is_passed'
        ]

class StudySessionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = StudySession
        fields = [
            'id', 'course', 'course_title', 'lesson', 'lesson_title',
            'started_at', 'ended_at', 'duration_minutes',
            'lessons_viewed', 'quizzes_attempted', 'active_time_minutes'
        ]

class UserAchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement_type', 'title', 'description',
            'earned_at', 'points', 'course', 'lesson'
        ]

class LearningStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningStreak
        fields = [
            'id', 'start_date', 'end_date', 'current_streak',
            'longest_streak', 'last_activity_date', 'is_active'
        ]

class ProgressDashboardSerializer(serializers.Serializer):
    """Sérialiseur pour le tableau de bord de progression"""
    
    # Statistiques générales
    total_courses_enrolled = serializers.IntegerField()
    total_courses_completed = serializers.IntegerField()
    total_time_spent_minutes = serializers.IntegerField()
    average_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Progression récente
    recent_enrollments = CourseEnrollmentSerializer(many=True)
    recent_achievements = UserAchievementSerializer(many=True)
    
    # Séries
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    
    # Cette semaine
    this_week_time = serializers.IntegerField()
    this_week_lessons = serializers.IntegerField()