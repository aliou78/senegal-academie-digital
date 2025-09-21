# progress/admin.py - Version corrigée
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CourseEnrollment, ModuleProgress, LessonProgress,
    QuizAttempt, StudySession, UserAchievement, LearningStreak, ProgressReport
)

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_title', 'status', 'progress_percentage', 'enrolled_at', 'certificate_issued']
    list_filter = ['status', 'certificate_issued', 'enrolled_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'course_title']
    readonly_fields = ['enrolled_at', 'estimated_completion_date']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('user', 'course_id', 'course_title', 'status', 'enrolled_at')
        }),
        ('Progression', {
            'fields': ('progress_percentage', 'total_time_spent', 'current_grade')
        }),
        ('Dates importantes', {
            'fields': ('started_at', 'completed_at', 'last_accessed')
        }),
        ('Certificat', {
            'fields': ('certificate_issued', 'certificate_date')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'module_title', 'progress_percentage', 'is_completed', 'score']
    list_filter = ['is_started', 'is_completed', 'enrollment__course_title']  # Corrigé
    search_fields = ['enrollment__user__email', 'module_title']
    
    def user_info(self, obj):
        return f"{obj.enrollment.user} - {obj.enrollment.course_title}"
    user_info.short_description = "Utilisateur - Cours"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('enrollment__user')

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'lesson_title', 'status', 'progress_percentage', 'time_spent', 'attempts']
    list_filter = ['status', 'lesson_type', 'enrollment__course_title']  # Corrigé
    search_fields = ['enrollment__user__email', 'lesson_title']
    
    def user_info(self, obj):
        return f"{obj.enrollment.user}"
    user_info.short_description = "Utilisateur"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('enrollment__user')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'quiz_title', 'attempt_number', 'score', 'is_passed', 'started_at']
    list_filter = ['is_passed', 'started_at']
    search_fields = ['lesson_progress__enrollment__user__email', 'quiz_title']
    
    def user_info(self, obj):
        return f"{obj.lesson_progress.enrollment.user}"
    user_info.short_description = "Utilisateur"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lesson_progress__enrollment__user')

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_title', 'started_at', 'duration_minutes', 'lessons_viewed', 'active_time_minutes']
    list_filter = ['started_at', 'course_title']
    search_fields = ['user__email', 'course_title']
    readonly_fields = ['started_at', 'duration_minutes']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'achievement_type', 'points', 'earned_at']
    list_filter = ['achievement_type', 'earned_at']
    search_fields = ['user__email', 'title']
    readonly_fields = ['earned_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(LearningStreak)
class LearningStreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak', 'longest_streak', 'last_activity_date', 'is_active']
    list_filter = ['is_active', 'last_activity_date']
    search_fields = ['user__email']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'report_type', 'start_date', 'end_date', 'courses_completed', 'generated_at']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['user__email']
    readonly_fields = ['generated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')