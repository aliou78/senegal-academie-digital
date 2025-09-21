from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from .models import (
    Category, Course, CourseModule, Lesson, Enrollment, LessonProgress,
    CourseReview, Quiz, QuizQuestion, QuizAnswer, QuizAttempt
)
from .serializers import (
    CategorySerializer, CourseListSerializer, CourseDetailSerializer,
    CourseModuleSerializer, LessonSerializer, EnrollmentSerializer,
    LessonProgressSerializer, CourseReviewSerializer, QuizSerializer,
    QuizAttemptSerializer
)
from .filters import CourseFilter


class CategoryListView(generics.ListAPIView):
    """
    Liste des catégories
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class CourseListView(generics.ListAPIView):
    """
    Liste des cours avec filtres et recherche
    """
    queryset = Course.objects.filter(status='published').select_related('instructor', 'category')
    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'description', 'short_description', 'instructor__first_name', 'instructor__last_name']
    ordering_fields = ['created_at', 'price', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtre par niveau
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Filtre par langue
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        # Filtre par prix (gratuit)
        free_only = self.request.query_params.get('free_only')
        if free_only == 'true':
            queryset = queryset.filter(price=0)
        
        # Filtre par cours mis en avant
        featured = self.request.query_params.get('featured')
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        return queryset


class CourseDetailView(generics.RetrieveAPIView):
    """
    Détails d'un cours
    """
    queryset = Course.objects.filter(status='published').select_related('instructor', 'category')
    serializer_class = CourseDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class CourseEnrollView(generics.CreateAPIView):
    """
    Inscription à un cours
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        course = get_object_or_404(Course, slug=kwargs['slug'])
        
        # Vérifier que l'utilisateur est un étudiant
        if request.user.role != 'student':
            return Response(
                {'error': 'Seuls les étudiants peuvent s\'inscrire aux cours'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier si déjà inscrit
        if Enrollment.objects.filter(student=request.user, course=course, is_active=True).exists():
            return Response(
                {'error': 'Vous êtes déjà inscrit à ce cours'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course
        )
        
        serializer = self.get_serializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StudentEnrollmentsView(generics.ListAPIView):
    """
    Cours auxquels l'étudiant est inscrit
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'student':
            return Enrollment.objects.filter(
                student=self.request.user,
                is_active=True
            ).select_related('course', 'course__instructor', 'course__category')
        return Enrollment.objects.none()


class InstructorCoursesView(generics.ListAPIView):
    """
    Cours d'un formateur
    """
    serializer_class = CourseListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'instructor':
            return Course.objects.filter(
                instructor=self.request.user
            ).select_related('category')
        return Course.objects.none()


class LessonDetailView(generics.RetrieveAPIView):
    """
    Détails d'une leçon
    """
    queryset = Lesson.objects.filter(is_published=True).select_related('module', 'module__course')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Vérifier l'inscription pour les leçons payantes
        if self.request.user.role == 'student':
            # Les étudiants peuvent voir les leçons gratuites ou celles des cours auxquels ils sont inscrits
            enrolled_courses = Enrollment.objects.filter(
                student=self.request.user,
                is_active=True
            ).values_list('course_id', flat=True)
            
            queryset = queryset.filter(
                Q(is_free=True) | Q(module__course_id__in=enrolled_courses)
            )
        elif self.request.user.role == 'instructor':
            # Les formateurs peuvent voir leurs propres leçons
            queryset = queryset.filter(module__course__instructor=self.request.user)
        elif self.request.user.role == 'admin':
            # Les admins peuvent voir toutes les leçons
            pass
        else:
            # Autres rôles ne peuvent voir que les leçons gratuites
            queryset = queryset.filter(is_free=True)
        
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_lesson_progress(request, lesson_id):
    """
    Mettre à jour la progression d'une leçon
    """
    if request.user.role != 'student':
        return Response(
            {'error': 'Seuls les étudiants peuvent mettre à jour leur progression'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Vérifier l'inscription au cours
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=lesson.module.course,
        is_active=True
    ).first()
    
    if not enrollment:
        return Response(
            {'error': 'Vous n\'êtes pas inscrit à ce cours'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    progress_data = {
        'student': request.user,
        'lesson': lesson,
        'is_completed': request.data.get('is_completed', False),
        'time_spent': request.data.get('time_spent', 0),
        'last_position': request.data.get('last_position', 0),
    }
    
    serializer = LessonProgressSerializer(data=progress_data)
    if serializer.is_valid():
        progress = serializer.save()
        
        # Mettre à jour la progression globale du cours
        total_lessons = lesson.module.course.modules.aggregate(
            total=Count('lessons', filter=Q(lessons__is_published=True))
        )['total'] or 0
        
        completed_lessons = LessonProgress.objects.filter(
            student=request.user,
            lesson__module__course=lesson.module.course,
            is_completed=True
        ).count()
        
        progress_percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
        enrollment.progress_percentage = progress_percentage
        
        # Marquer le cours comme terminé si 100% de progression
        if progress_percentage == 100 and not enrollment.completed_at:
            from django.utils import timezone
            enrollment.completed_at = timezone.now()
        
        enrollment.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseReviewListView(generics.ListCreateAPIView):
    """
    Liste et création d'avis pour un cours
    """
    serializer_class = CourseReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        return CourseReview.objects.filter(
            course=course,
            is_active=True
        ).select_related('student')

    def perform_create(self, serializer):
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        
        # Vérifier que l'utilisateur est un étudiant inscrit
        if self.request.user.role != 'student':
            raise PermissionError('Seuls les étudiants peuvent laisser des avis')
        
        enrollment = Enrollment.objects.filter(
            student=self.request.user,
            course=course,
            is_active=True
        ).first()
        
        if not enrollment:
            raise PermissionError('Vous devez être inscrit au cours pour laisser un avis')
        
        serializer.save(student=self.request.user, course=course)


class QuizDetailView(generics.RetrieveAPIView):
    """
    Détails d'un quiz
    """
    queryset = Quiz.objects.filter(is_published=True).select_related('lesson', 'lesson__module', 'lesson__module__course')
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Vérifier l'accès selon le rôle
        if self.request.user.role == 'student':
            enrolled_courses = Enrollment.objects.filter(
                student=self.request.user,
                is_active=True
            ).values_list('course_id', flat=True)
            
            queryset = queryset.filter(
                lesson__module__course_id__in=enrolled_courses
            )
        elif self.request.user.role == 'instructor':
            queryset = queryset.filter(lesson__module__course__instructor=self.request.user)
        elif self.request.user.role != 'admin':
            queryset = queryset.none()
        
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz_attempt(request, quiz_id):
    """
    Soumettre une tentative de quiz
    """
    if request.user.role != 'student':
        return Response(
            {'error': 'Seuls les étudiants peuvent passer des quiz'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Vérifier l'inscription au cours
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=quiz.lesson.module.course,
        is_active=True
    ).first()
    
    if not enrollment:
        return Response(
            {'error': 'Vous n\'êtes pas inscrit à ce cours'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Vérifier le nombre de tentatives
    attempts_count = QuizAttempt.objects.filter(
        student=request.user,
        quiz=quiz
    ).count()
    
    if attempts_count >= quiz.max_attempts:
        return Response(
            {'error': f'Nombre maximum de tentatives atteint ({quiz.max_attempts})'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculer le score (simplifié - à améliorer selon les réponses)
    answers = request.data.get('answers', [])
    total_questions = quiz.questions.count()
    correct_answers = 0
    
    # Ici, vous devriez calculer le score réel basé sur les réponses
    # Pour l'instant, on utilise une logique simplifiée
    for answer in answers:
        question_id = answer.get('question_id')
        selected_answer_id = answer.get('answer_id')
        
        if question_id and selected_answer_id:
            try:
                question = QuizQuestion.objects.get(id=question_id, quiz=quiz)
                correct_answer = QuizAnswer.objects.filter(
                    question=question,
                    is_correct=True
                ).first()
                
                if correct_answer and str(correct_answer.id) == str(selected_answer_id):
                    correct_answers += 1
            except (QuizQuestion.DoesNotExist, QuizAnswer.DoesNotExist):
                pass
    
    score = correct_answers
    percentage = int((score / total_questions) * 100) if total_questions > 0 else 0
    is_passed = percentage >= quiz.passing_score
    
    attempt_data = {
        'student': request.user,
        'quiz': quiz,
        'score': score,
        'percentage': percentage,
        'is_passed': is_passed,
        'time_taken': request.data.get('time_taken', 0),
    }
    
    serializer = QuizAttemptSerializer(data=attempt_data)
    if serializer.is_valid():
        attempt = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentQuizAttemptsView(generics.ListAPIView):
    """
    Tentatives de quiz d'un étudiant
    """
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'student':
            return QuizAttempt.objects.filter(
                student=self.request.user
            ).select_related('quiz', 'quiz__lesson')
        return QuizAttempt.objects.none()
