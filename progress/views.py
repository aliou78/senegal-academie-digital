# progress/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, date
from django.contrib.auth import get_user_model

from .models import (
    CourseEnrollment, ModuleProgress, LessonProgress,
    QuizAttempt, StudySession, UserAchievement, LearningStreak
)
from .serializers import (
    CourseEnrollmentSerializer, ModuleProgressSerializer, LessonProgressSerializer,
    QuizAttemptSerializer, StudySessionSerializer, UserAchievementSerializer,
    LearningStreakSerializer, ProgressDashboardSerializer
)
from .services import ProgressService

User = get_user_model()

class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des inscriptions aux cours"""
    
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CourseEnrollment.objects.filter(user=self.request.user).select_related('course')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start_course(self, request, pk=None):
        """Marquer le début d'un cours"""
        enrollment = self.get_object()
        if not enrollment.started_at:
            enrollment.started_at = timezone.now()
            enrollment.status = 'active'
            enrollment.save()
            
            # Créer une session d'étude
            StudySession.objects.create(
                user=request.user,
                course=enrollment.course
            )
        
        return Response({'message': 'Cours démarré avec succès'})
    
    @action(detail=True, methods=['post'])
    def complete_course(self, request, pk=None):
        """Marquer un cours comme terminé"""
        enrollment = self.get_object()
        if enrollment.progress_percentage >= 100:
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
            enrollment.save()
            
            # Générer des achievements
            ProgressService.check_achievements(request.user, course=enrollment.course)
            
            return Response({'message': 'Cours terminé avec succès'})
        else:
            return Response(
                {'error': 'Le cours doit être complété à 100% pour être marqué comme terminé'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProgressViewSet(viewsets.ViewSet):
    """ViewSet pour les statistiques de progression"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Tableau de bord de progression de l'utilisateur"""
        user = request.user
        
        # Statistiques générales
        enrollments = CourseEnrollment.objects.filter(user=user)
        total_enrolled = enrollments.count()
        total_completed = enrollments.filter(status='completed').count()
        
        total_time = enrollments.aggregate(
            total=Sum('total_time_spent')
        )['total'] or 0
        
        avg_completion = enrollments.aggregate(
            avg=Avg('progress_percentage')
        )['avg'] or 0
        
        # Inscriptions récentes (dernières 5)
        recent_enrollments = enrollments.order_by('-enrolled_at')[:5]
        
        # Achievements récents
        recent_achievements = UserAchievement.objects.filter(
            user=user
        ).order_by('-earned_at')[:5]
        
        # Série d'apprentissage
        streak, _ = LearningStreak.objects.get_or_create(user=user)
        
        # Activité de cette semaine
        week_start = timezone.now().date() - timedelta(days=7)
        this_week_sessions = StudySession.objects.filter(
            user=user,
            started_at__date__gte=week_start
        )
        
        this_week_time = this_week_sessions.aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        
        this_week_lessons = this_week_sessions.aggregate(
            total=Sum('lessons_viewed')
        )['total'] or 0
        
        data = {
            'total_courses_enrolled': total_enrolled,
            'total_courses_completed': total_completed,
            'total_time_spent_minutes': total_time,
            'average_completion_rate': round(avg_completion, 2),
            'recent_enrollments': CourseEnrollmentSerializer(recent_enrollments, many=True).data,
            'recent_achievements': UserAchievementSerializer(recent_achievements, many=True).data,
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'this_week_time': this_week_time,
            'this_week_lessons': this_week_lessons,
        }
        
        serializer = ProgressDashboardSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def course_progress(self, request):
        """Progression détaillée d'un cours spécifique"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {'error': 'course_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            enrollment = CourseEnrollment.objects.get(
                user=request.user, 
                course_id=course_id
            )
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Progression des modules
        module_progress = ModuleProgress.objects.filter(
            enrollment=enrollment
        ).select_related('module')
        
        # Progression des leçons
        lesson_progress = LessonProgress.objects.filter(
            enrollment=enrollment
        ).select_related('lesson')
        
        # Tentatives de quiz récentes
        recent_quizzes = QuizAttempt.objects.filter(
            lesson_progress__enrollment=enrollment
        ).order_by('-started_at')[:10]
        
        data = {
            'enrollment': CourseEnrollmentSerializer(enrollment).data,
            'modules': ModuleProgressSerializer(module_progress, many=True).data,
            'lessons': LessonProgressSerializer(lesson_progress, many=True).data,
            'recent_quizzes': QuizAttemptSerializer(recent_quizzes, many=True).data,
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques détaillées de l'utilisateur"""
        user = request.user
        
        # Période (par défaut: 30 derniers jours)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Sessions d'étude
        sessions = StudySession.objects.filter(
            user=user,
            started_at__date__gte=start_date
        )
        
        daily_stats = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            day_sessions = sessions.filter(started_at__date=current_date)
            
            daily_stats.append({
                'date': current_date,
                'sessions': day_sessions.count(),
                'time_minutes': day_sessions.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0,
                'lessons_viewed': day_sessions.aggregate(Sum('lessons_viewed'))['lessons_viewed__sum'] or 0,
            })
        
        # Statistiques par cours
        course_stats = []
        enrollments = CourseEnrollment.objects.filter(user=user).select_related('course')
        
        for enrollment in enrollments:
            course_sessions = sessions.filter(course=enrollment.course)
            course_stats.append({
                'course_id': enrollment.course.id,
                'course_title': enrollment.course.title,
                'progress_percentage': enrollment.progress_percentage,
                'time_spent': enrollment.total_time_spent,
                'sessions_count': course_sessions.count(),
            })
        
        return Response({
            'period_days': days,
            'daily_statistics': daily_stats,
            'course_statistics': course_stats,
            'total_sessions': sessions.count(),
            'total_time_minutes': sessions.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0,
        })

class LessonProgressViewSet(viewsets.ModelViewSet):
    """ViewSet pour la progression des leçons"""
    
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LessonProgress.objects.filter(
            enrollment__user=self.request.user
        ).select_related('lesson', 'enrollment')
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Mettre à jour la progression d'une leçon"""
        lesson_progress = self.get_object()
        
        # Données de progression
        progress_percentage = request.data.get('progress_percentage', 0)
        time_spent = request.data.get('time_spent', 0)
        current_position = request.data.get('current_position', 0)
        
        # Mettre à jour
        lesson_progress.progress_percentage = min(100, max(0, progress_percentage))
        lesson_progress.time_spent += time_spent
        lesson_progress.current_position = current_position
        lesson_progress.last_accessed = timezone.now()
        
        # Marquer comme commencé si pas encore fait
        if not lesson_progress.started_at:
            lesson_progress.started_at = timezone.now()
            lesson_progress.status = 'in_progress'
        
        # Marquer comme terminé si 100%
        if lesson_progress.progress_percentage >= 100 and lesson_progress.status != 'completed':
            lesson_progress.status = 'completed'
            lesson_progress.completed_at = timezone.now()
        
        lesson_progress.save()
        
        # Mettre à jour la progression du module et du cours
        ProgressService.update_module_progress(lesson_progress.enrollment, lesson_progress.lesson.module)
        ProgressService.update_course_progress(lesson_progress.enrollment)
        
        return Response(LessonProgressSerializer(lesson_progress).data)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Marquer une leçon comme terminée"""
        lesson_progress = self.get_object()
        
        lesson_progress.status = 'completed'
        lesson_progress.progress_percentage = 100
        lesson_progress.completed_at = timezone.now()
        
        if not lesson_progress.started_at:
            lesson_progress.started_at = timezone.now()
        
        lesson_progress.save()
        
        # Mettre à jour les progressions parents
        ProgressService.update_module_progress(lesson_progress.enrollment, lesson_progress.lesson.module)
        ProgressService.update_course_progress(lesson_progress.enrollment)
        
        # Vérifier les achievements
        ProgressService.check_lesson_achievements(request.user, lesson_progress.lesson)
        
        return Response({'message': 'Leçon marquée comme terminée'})

class StudySessionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les sessions d'étude"""
    
    serializer_class = StudySessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return StudySession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """Terminer une session d'étude"""
        session = self.get_object()
        
        if not session.ended_at:
            session.ended_at = timezone.now()
            session.duration_minutes = int((session.ended_at - session.started_at).total_seconds() / 60)
            session.save()
            
            # Mettre à jour la série d'apprentissage
            ProgressService.update_learning_streak(request.user)
        
        return Response(StudySessionSerializer(session).data)

class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les achievements (lecture seule)"""
    
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des achievements"""
        achievements = self.get_queryset()
        
        summary = {
            'total_achievements': achievements.count(),
            'total_points': achievements.aggregate(Sum('points'))['points__sum'] or 0,
            'by_type': {},
            'recent': UserAchievementSerializer(achievements.order_by('-earned_at')[:5], many=True).data
        }
        
        # Grouper par type
        for choice in UserAchievement.ACHIEVEMENT_TYPES:
            achievement_type = choice[0]
            type_achievements = achievements.filter(achievement_type=achievement_type)
            summary['by_type'][achievement_type] = {
                'count': type_achievements.count(),
                'points': type_achievements.aggregate(Sum('points'))['points__sum'] or 0
            }
        
        return Response(summary)