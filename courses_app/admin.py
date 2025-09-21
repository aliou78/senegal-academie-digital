from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Course, Module, Lesson, Quiz, Question, Answer, Enrollment, Certificate

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title','instructor','price','is_published','created_at')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title','course','order')
    ordering = ('course','order')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title','module','order')
    ordering = ('module','order')

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text','quiz','marks')
    inlines = [AnswerInline]

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title','module')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student','course','enrolled_at','progress')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('enrollment','issued_at')
