from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Category, Course, CourseModule, Lesson, Enrollment, LessonProgress,
    CourseReview, Quiz, QuizQuestion, QuizAnswer, QuizAttempt
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'level', 'price', 'status', 'is_featured', 'created_at')
    list_filter = ('status', 'level', 'language', 'is_featured', 'is_certified', 'category', 'created_at')
    search_fields = ('title', 'description', 'instructor__username', 'instructor__email')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ()
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('title', 'slug', 'description', 'short_description', 'instructor', 'category')
        }),
        (_('Métadonnées'), {
            'fields': ('level', 'language', 'thumbnail', 'video_intro')
        }),
        (_('Prix et durée'), {
            'fields': ('price', 'duration_hours')
        }),
        (_('Statut'), {
            'fields': ('status', 'is_featured', 'is_certified', 'published_at')
        }),
    )


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('title', 'lesson_type', 'order', 'is_published', 'is_free')


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_published', 'created_at')
    list_filter = ('is_published', 'course', 'created_at')
    search_fields = ('title', 'course__title')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'lesson_type', 'order', 'is_published', 'is_free', 'created_at')
    list_filter = ('lesson_type', 'is_published', 'is_free', 'module__course', 'created_at')
    search_fields = ('title', 'module__title', 'module__course__title')
    ordering = ('module__course', 'module__order', 'order')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'progress_percentage', 'is_active', 'completed_at')
    list_filter = ('is_active', 'enrolled_at', 'completed_at', 'course')
    search_fields = ('student__username', 'student__email', 'course__title')
    readonly_fields = ('enrolled_at',)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'is_completed', 'time_spent', 'completed_at')
    list_filter = ('is_completed', 'lesson__module__course', 'completed_at')
    search_fields = ('student__username', 'lesson__title')
    readonly_fields = ('completed_at',)


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'is_active', 'created_at')
    list_filter = ('rating', 'is_active', 'created_at', 'course')
    search_fields = ('student__username', 'course__title', 'comment')
    readonly_fields = ('created_at',)


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 0
    fields = ('answer_text', 'is_correct', 'order')


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0
    fields = ('question_text', 'question_type', 'points', 'order')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'time_limit', 'passing_score', 'max_attempts', 'is_published')
    list_filter = ('is_published', 'lesson__module__course', 'created_at')
    search_fields = ('title', 'lesson__title')
    inlines = [QuizQuestionInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz', 'question_type', 'points', 'order')
    list_filter = ('question_type', 'quiz__lesson__module__course')
    search_fields = ('question_text', 'quiz__title')
    inlines = [QuizAnswerInline]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('answer_text', 'question', 'is_correct', 'order')
    list_filter = ('is_correct', 'question__quiz__lesson__module__course')
    search_fields = ('answer_text', 'question__question_text')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'percentage', 'is_passed', 'started_at', 'completed_at')
    list_filter = ('is_passed', 'quiz__lesson__module__course', 'started_at', 'completed_at')
    search_fields = ('student__username', 'quiz__title')
    readonly_fields = ('started_at', 'completed_at')
