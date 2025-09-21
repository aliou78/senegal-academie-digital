from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Course, CourseModule, Lesson, Enrollment, LessonProgress,
    CourseReview, Quiz, QuizQuestion, QuizAnswer, QuizAttempt
)

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer pour les catégories
    """
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'icon', 'color', 'is_active', 'course_count', 'created_at')

    def get_course_count(self, obj):
        return obj.courses.filter(status='published').count()


class CourseListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des cours
    """
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    enrolled_students_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('id', 'title', 'slug', 'short_description', 'instructor_name', 'category_name',
                 'level', 'language', 'thumbnail', 'price', 'duration_hours', 'is_featured',
                 'is_certified', 'enrolled_students_count', 'average_rating', 'is_enrolled',
                 'created_at', 'published_at')

    def get_enrolled_students_count(self, obj):
        return obj.get_enrolled_students_count()

    def get_average_rating(self, obj):
        return round(obj.get_average_rating(), 1)

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'student':
            return obj.enrollments.filter(student=request.user, is_active=True).exists()
        return False


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails d'un cours
    """
    instructor = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    modules = serializers.SerializerMethodField()
    enrolled_students_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    enrollment_progress = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('id', 'title', 'slug', 'description', 'short_description', 'instructor',
                 'category', 'level', 'language', 'thumbnail', 'video_intro', 'price',
                 'duration_hours', 'status', 'is_featured', 'is_certified', 'modules',
                 'enrolled_students_count', 'average_rating', 'is_enrolled', 'enrollment_progress',
                 'created_at', 'updated_at', 'published_at')

    def get_instructor(self, obj):
        return {
            'id': obj.instructor.id,
            'name': obj.instructor.get_full_name(),
            'profile_picture': obj.instructor.profile_picture.url if obj.instructor.profile_picture else None,
            'bio': obj.instructor.bio,
        }

    def get_modules(self, obj):
        modules = obj.modules.filter(is_published=True).order_by('order')
        return CourseModuleSerializer(modules, many=True, context=self.context).data

    def get_enrolled_students_count(self, obj):
        return obj.get_enrolled_students_count()

    def get_average_rating(self, obj):
        return round(obj.get_average_rating(), 1)

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'student':
            return obj.enrollments.filter(student=request.user, is_active=True).exists()
        return False

    def get_enrollment_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'student':
            enrollment = obj.enrollments.filter(student=request.user, is_active=True).first()
            if enrollment:
                return {
                    'progress_percentage': enrollment.progress_percentage,
                    'completed_at': enrollment.completed_at,
                }
        return None


class CourseModuleSerializer(serializers.ModelSerializer):
    """
    Serializer pour les modules de cours
    """
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = CourseModule
        fields = ('id', 'title', 'description', 'order', 'lessons')

    def get_lessons(self, obj):
        lessons = obj.lessons.filter(is_published=True).order_by('order')
        return LessonSerializer(lessons, many=True, context=self.context).data


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer pour les leçons
    """
    is_completed = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'description', 'content', 'lesson_type', 'video_url',
                 'video_duration', 'attachment', 'order', 'is_free', 'is_completed', 'progress')

    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = obj.progress.filter(student=request.user).first()
            return progress.is_completed if progress else False
        return False

    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = obj.progress.filter(student=request.user).first()
            if progress:
                return {
                    'time_spent': progress.time_spent,
                    'last_position': progress.last_position,
                    'completed_at': progress.completed_at,
                }
        return None


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les inscriptions
    """
    course = CourseListSerializer(read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'course', 'student_name', 'enrolled_at', 'progress_percentage',
                 'is_active', 'completed_at')

    def create(self, validated_data):
        # Vérifier si l'utilisateur est déjà inscrit
        enrollment, created = Enrollment.objects.get_or_create(
            student=validated_data['student'],
            course=validated_data['course'],
            defaults={'is_active': True}
        )
        if not created and not enrollment.is_active:
            enrollment.is_active = True
            enrollment.save()
        return enrollment


class LessonProgressSerializer(serializers.ModelSerializer):
    """
    Serializer pour la progression des leçons
    """
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    course_title = serializers.CharField(source='lesson.module.course.title', read_only=True)

    class Meta:
        model = LessonProgress
        fields = ('id', 'lesson', 'lesson_title', 'course_title', 'is_completed',
                 'completed_at', 'time_spent', 'last_position')

    def create(self, validated_data):
        progress, created = LessonProgress.objects.get_or_create(
            student=validated_data['student'],
            lesson=validated_data['lesson'],
            defaults=validated_data
        )
        if not created:
            for key, value in validated_data.items():
                if key != 'student' and key != 'lesson':
                    setattr(progress, key, value)
            progress.save()
        return progress


class CourseReviewSerializer(serializers.ModelSerializer):
    """
    Serializer pour les avis de cours
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_avatar = serializers.SerializerMethodField()

    class Meta:
        model = CourseReview
        fields = ('id', 'student', 'student_name', 'student_avatar', 'rating', 'comment',
                 'is_active', 'created_at')

    def get_student_avatar(self, obj):
        if obj.student.profile_picture:
            return obj.student.profile_picture.url
        return None

    def create(self, validated_data):
        review, created = CourseReview.objects.get_or_create(
            student=validated_data['student'],
            course=validated_data['course'],
            defaults=validated_data
        )
        if not created:
            for key, value in validated_data.items():
                if key != 'student' and key != 'course':
                    setattr(review, key, value)
            review.save()
        return review


class QuizAnswerSerializer(serializers.ModelSerializer):
    """
    Serializer pour les réponses de quiz
    """
    class Meta:
        model = QuizAnswer
        fields = ('id', 'answer_text', 'is_correct', 'order')


class QuizQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les questions de quiz
    """
    answers = QuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ('id', 'question_text', 'question_type', 'points', 'order', 'answers')


class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer pour les quiz
    """
    questions = QuizQuestionSerializer(many=True, read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'lesson_title', 'time_limit', 'passing_score',
                 'max_attempts', 'is_published', 'questions', 'created_at')


class QuizAttemptSerializer(serializers.ModelSerializer):
    """
    Serializer pour les tentatives de quiz
    """
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ('id', 'quiz', 'quiz_title', 'score', 'percentage', 'is_passed',
                 'started_at', 'completed_at', 'time_taken')

    def create(self, validated_data):
        # Calculer le score et le pourcentage
        quiz = validated_data['quiz']
        # Ici, vous devriez calculer le score basé sur les réponses
        # Pour l'instant, on utilise des valeurs par défaut
        validated_data['percentage'] = 0  # À calculer
        validated_data['is_passed'] = validated_data['percentage'] >= quiz.passing_score
        return super().create(validated_data)
