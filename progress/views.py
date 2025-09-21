from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg
from .models import (
    Badge, UserBadge, Certificate, UserCertificate, LearningPath,
    LearningPathCourse, UserLearningPath, Achievement, StudySession, UserStatistics
)
from .serializers import (
    BadgeSerializer, UserBadgeSerializer, CertificateSerializer, UserCertificateSerializer,
    LearningPathSerializer, LearningPathDetailSerializer, UserLearningPathSerializer,
    AchievementSerializer, StudySessionSerializer, UserStatisticsSerializer,
    LearningPathEnrollmentSerializer, CertificateVerificationSerializer,
    ProgressUpdateSerializer, BadgeAwardSerializer
)
from .services import ProgressService, BadgeService, CertificateService


class BadgeListView(generics.ListAPIView):
    """
    Liste des badges disponibles
    """
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [AllowAny]


class UserBadgeListView(generics.ListAPIView):
    """
    Liste des badges d'un utilisateur
    """
    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserBadge.objects.filter(
            user=self.request.user,
            is_visible=True
        ).select_related('badge')


class CertificateListView(generics.ListAPIView):
    """
    Liste des certificats disponibles
    """
    queryset = Certificate.objects.filter(is_active=True)
    serializer_class = CertificateSerializer
    permission_classes = [AllowAny]


class UserCertificateListView(generics.ListAPIView):
    """
    Liste des certificats d'un utilisateur
    """
    serializer_class = UserCertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserCertificate.objects.filter(
            user=self.request.user
        ).select_related('certificate', 'course', 'issued_by')


class UserCertificateDetailView(generics.RetrieveAPIView):
    """
    Détails d'un certificat utilisateur
    """
    serializer_class = UserCertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserCertificate.objects.filter(
            user=self.request.user
        ).select_related('certificate', 'course', 'issued_by')


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_certificate(request):
    """
    Vérifier un certificat par code
    """
    serializer = CertificateVerificationSerializer(data=request.data)
    if serializer.is_valid():
        verification_code = serializer.validated_data['verification_code']
        certificate = get_object_or_404(UserCertificate, verification_code=verification_code)
        
        return Response({
            'certificate': UserCertificateSerializer(certificate).data,
            'is_valid': True
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LearningPathListView(generics.ListAPIView):
    """
    Liste des parcours d'apprentissage
    """
    queryset = LearningPath.objects.filter(is_active=True)
    serializer_class = LearningPathSerializer
    permission_classes = [AllowAny]


class LearningPathDetailView(generics.RetrieveAPIView):
    """
    Détails d'un parcours d'apprentissage
    """
    queryset = LearningPath.objects.filter(is_active=True)
    serializer_class = LearningPathDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class UserLearningPathListView(generics.ListAPIView):
    """
    Parcours d'apprentissage d'un utilisateur
    """
    serializer_class = UserLearningPathSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserLearningPath.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('learning_path')


class LearningPathEnrollmentView(generics.CreateAPIView):
    """
    Inscription à un parcours d'apprentissage
    """
    serializer_class = LearningPathEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if request.user.role != 'student':
            return Response(
                {'error': 'Seuls les étudiants peuvent s\'inscrire aux parcours'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            enrollment = serializer.save()
            return Response(
                UserLearningPathSerializer(enrollment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AchievementListView(generics.ListAPIView):
    """
    Liste des réalisations d'un utilisateur
    """
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Achievement.objects.filter(
            user=self.request.user,
            is_visible=True
        )


class StudySessionListView(generics.ListCreateAPIView):
    """
    Liste et création de sessions d'étude
    """
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudySession.objects.filter(
            user=self.request.user
        ).select_related('course', 'lesson')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_study_session(request, session_id):
    """
    Terminer une session d'étude
    """
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    
    if session.ended_at:
        return Response(
            {'error': 'Cette session est déjà terminée'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session.ended_at = timezone.now()
    duration = (session.ended_at - session.started_at).total_seconds() / 60
    session.duration_minutes = int(duration)
    session.save()
    
    # Mettre à jour les statistiques
    progress_service = ProgressService()
    progress_service.update_user_statistics(request.user)
    
    return Response(StudySessionSerializer(session).data, status=status.HTTP_200_OK)


class UserStatisticsView(generics.RetrieveAPIView):
    """
    Statistiques d'un utilisateur
    """
    serializer_class = UserStatisticsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        stats, created = UserStatistics.objects.get_or_create(user=self.request.user)
        return stats


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request):
    """
    Mettre à jour la progression d'un utilisateur
    """
    if request.user.role != 'student':
        return Response(
            {'error': 'Seuls les étudiants peuvent mettre à jour leur progression'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = ProgressUpdateSerializer(data=request.data)
    if serializer.is_valid():
        progress_service = ProgressService()
        result = progress_service.update_lesson_progress(
            user=request.user,
            lesson_id=serializer.validated_data['lesson_id'],
            is_completed=serializer.validated_data['is_completed'],
            time_spent=serializer.validated_data['time_spent'],
            last_position=serializer.validated_data['last_position']
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def award_badge(request):
    """
    Attribuer un badge à un utilisateur (pour les administrateurs)
    """
    if request.user.role != 'admin':
        return Response(
            {'error': 'Accès non autorisé'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = BadgeAwardSerializer(data=request.data)
    if serializer.is_valid():
        badge_service = BadgeService()
        result = badge_service.award_badge(
            user_id=serializer.validated_data['user_id'],
            badge_id=serializer.validated_data['badge_id']
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_certificate(request, course_id):
    """
    Générer un certificat pour un cours terminé
    """
    if request.user.role != 'student':
        return Response(
            {'error': 'Seuls les étudiants peuvent générer des certificats'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from courses.models import Course, Enrollment
    
    course = get_object_or_404(Course, id=course_id)
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=course,
        is_active=True
    )
    
    # Vérifier que le cours est terminé
    if enrollment.progress_percentage < 100:
        return Response(
            {'error': 'Vous devez terminer le cours pour obtenir un certificat'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier qu'un certificat n'existe pas déjà
    if UserCertificate.objects.filter(user=request.user, course=course).exists():
        return Response(
            {'error': 'Vous avez déjà un certificat pour ce cours'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    certificate_service = CertificateService()
    result = certificate_service.generate_course_certificate(
        user=request.user,
        course=course,
        issued_by=request.user  # Auto-généré
    )
    
    if result['success']:
        return Response(result, status=status.HTTP_201_CREATED)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Statistiques pour le tableau de bord
    """
    if request.user.role == 'student':
        # Statistiques pour les étudiants
        stats = UserStatistics.objects.get(user=request.user)
        
        # Cours en cours
        from courses.models import Enrollment
        active_enrollments = Enrollment.objects.filter(
            student=request.user,
            is_active=True,
            completed_at__isnull=True
        ).count()
        
        # Sessions récentes
        recent_sessions = StudySession.objects.filter(
            user=request.user,
            started_at__gte=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        return Response({
            'user_stats': UserStatisticsSerializer(stats).data,
            'active_enrollments': active_enrollments,
            'recent_sessions': recent_sessions,
        })
    
    elif request.user.role == 'instructor':
        # Statistiques pour les formateurs
        from courses.models import Course, Enrollment
        from payments.models import InstructorCommission
        
        total_courses = Course.objects.filter(instructor=request.user).count()
        total_students = Enrollment.objects.filter(
            course__instructor=request.user,
            is_active=True
        ).values('student').distinct().count()
        
        total_earnings = InstructorCommission.objects.filter(
            instructor=request.user
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return Response({
            'total_courses': total_courses,
            'total_students': total_students,
            'total_earnings': total_earnings,
        })
    
    elif request.user.role == 'admin':
        # Statistiques pour les administrateurs
        from courses.models import Course, Enrollment
        from payments.models import Payment
        
        total_courses = Course.objects.count()
        total_students = User.objects.filter(role='student').count()
        total_instructors = User.objects.filter(role='instructor').count()
        total_revenue = Payment.objects.filter(status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        return Response({
            'total_courses': total_courses,
            'total_students': total_students,
            'total_instructors': total_instructors,
            'total_revenue': total_revenue,
        })
    
    return Response({'error': 'Rôle non reconnu'}, status=status.HTTP_400_BAD_REQUEST)
