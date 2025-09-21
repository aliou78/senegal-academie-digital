from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Badge, UserBadge, Certificate, UserCertificate, LearningPath,
    LearningPathCourse, UserLearningPath, Achievement, StudySession, UserStatistics
)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_type', 'is_active', 'created_at')
    list_filter = ('badge_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at', 'is_visible')
    list_filter = ('badge__badge_type', 'earned_at', 'is_visible')
    search_fields = ('user__username', 'badge__name')
    readonly_fields = ('earned_at',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('name', 'certificate_type', 'is_active', 'created_at')
    list_filter = ('certificate_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')


@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'certificate', 'course', 'issued_at', 'is_verified')
    list_filter = ('certificate__certificate_type', 'issued_at', 'is_verified')
    search_fields = ('user__username', 'certificate__name', 'verification_code')
    readonly_fields = ('id', 'verification_code', 'issued_at')


class LearningPathCourseInline(admin.TabularInline):
    model = LearningPathCourse
    extra = 0
    fields = ('course', 'order', 'is_required')


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty_level', 'duration_weeks', 'is_active', 'created_at')
    list_filter = ('difficulty_level', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [LearningPathCourseInline]


@admin.register(UserLearningPath)
class UserLearningPathAdmin(admin.ModelAdmin):
    list_display = ('user', 'learning_path', 'progress_percentage', 'enrolled_at', 'is_active')
    list_filter = ('learning_path__difficulty_level', 'enrolled_at', 'is_active')
    search_fields = ('user__username', 'learning_path__name')
    readonly_fields = ('enrolled_at',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement_type', 'title', 'earned_at', 'is_visible')
    list_filter = ('achievement_type', 'earned_at', 'is_visible')
    search_fields = ('user__username', 'title', 'description')
    readonly_fields = ('earned_at',)


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'lesson', 'started_at', 'duration_minutes')
    list_filter = ('started_at', 'course')
    search_fields = ('user__username', 'course__title', 'lesson__title')
    readonly_fields = ('started_at',)


@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_courses_completed', 'total_certificates_earned', 'current_streak_days', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('user__username',)
    readonly_fields = ('last_updated',)
    
    fieldsets = (
        (_('Cours'), {
            'fields': ('total_courses_enrolled', 'total_courses_completed', 'total_lessons_completed')
        }),
        (_('Temps et progression'), {
            'fields': ('total_time_spent_minutes', 'current_streak_days', 'longest_streak_days')
        }),
        (_('Certifications'), {
            'fields': ('total_certificates_earned', 'total_badges_earned')
        }),
        (_('Quiz'), {
            'fields': ('total_quizzes_taken', 'total_quizzes_passed', 'average_quiz_score')
        }),
    )
