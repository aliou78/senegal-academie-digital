from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    UserBadge, UserCertificate, UserLearningPath, Achievement, 
    StudySession, UserStatistics, Badge, Certificate
)
from courses.models import Course, Enrollment, LessonProgress, Lesson

User = get_user_model()


class ProgressService:
    """
    Service pour gérer la progression des utilisateurs
    """
    
    def __init__(self):
        self.badge_service = BadgeService()
        self.certificate_service = CertificateService()
    
    def update_lesson_progress(self, user, lesson_id, is_completed, time_spent=0, last_position=0):
        """
        Mettre à jour la progression d'une leçon
        """
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            
            # Vérifier l'inscription au cours
            enrollment = Enrollment.objects.filter(
                student=user,
                course=lesson.module.course,
                is_active=True
            ).first()
            
            if not enrollment:
                return {
                    'success': False,
                    'error': 'Vous n\'êtes pas inscrit à ce cours'
                }
            
            # Mettre à jour ou créer la progression
            progress, created = LessonProgress.objects.get_or_create(
                student=user,
                lesson=lesson,
                defaults={
                    'is_completed': is_completed,
                    'time_spent': time_spent,
                    'last_position': last_position
                }
            )
            
            if not created:
                progress.is_completed = is_completed
                progress.time_spent += time_spent
                progress.last_position = last_position
                
                if is_completed and not progress.completed_at:
                    progress.completed_at = timezone.now()
                
                progress.save()
            
            # Mettre à jour la progression du cours
            self._update_course_progress(user, lesson.module.course)
            
            # Vérifier les badges et réalisations
            self._check_achievements(user, lesson, is_completed)
            
            return {
                'success': True,
                'progress': {
                    'lesson_id': lesson.id,
                    'is_completed': progress.is_completed,
                    'time_spent': progress.time_spent,
                    'completed_at': progress.completed_at
                }
            }
            
        except Lesson.DoesNotExist:
            return {
                'success': False,
                'error': 'Leçon non trouvée'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_course_progress(self, user, course):
        """
        Mettre à jour la progression globale d'un cours
        """
        # Calculer le pourcentage de progression
        total_lessons = Lesson.objects.filter(
            module__course=course,
            is_published=True
        ).count()
        
        completed_lessons = LessonProgress.objects.filter(
            student=user,
            lesson__module__course=course,
            is_completed=True
        ).count()
        
        progress_percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
        
        # Mettre à jour l'inscription
        enrollment = Enrollment.objects.get(student=user, course=course, is_active=True)
        enrollment.progress_percentage = progress_percentage
        
        if progress_percentage == 100 and not enrollment.completed_at:
            enrollment.completed_at = timezone.now()
            
            # Générer automatiquement un certificat si le cours en propose un
            if course.is_certified:
                self.certificate_service.generate_course_certificate(
                    user=user,
                    course=course,
                    issued_by=course.instructor
                )
        
        enrollment.save()
        
        # Mettre à jour les statistiques
        self.update_user_statistics(user)
    
    def _check_achievements(self, user, lesson, is_completed):
        """
        Vérifier et attribuer les réalisations
        """
        if is_completed:
            # Réalisation: Leçon terminée
            Achievement.objects.create(
                user=user,
                achievement_type='lesson_completed',
                title=f'Leçon terminée: {lesson.title}',
                description=f'Vous avez terminé la leçon "{lesson.title}"',
                data={
                    'lesson_id': lesson.id,
                    'course_id': lesson.module.course.id,
                    'course_title': lesson.module.course.title
                }
            )
            
            # Vérifier les badges liés aux leçons
            self.badge_service.check_lesson_badges(user, lesson)
    
    def update_user_statistics(self, user):
        """
        Mettre à jour les statistiques d'un utilisateur
        """
        stats, created = UserStatistics.objects.get_or_create(user=user)
        
        # Statistiques des cours
        stats.total_courses_enrolled = Enrollment.objects.filter(
            student=user,
            is_active=True
        ).count()
        
        stats.total_courses_completed = Enrollment.objects.filter(
            student=user,
            completed_at__isnull=False
        ).count()
        
        stats.total_lessons_completed = LessonProgress.objects.filter(
            student=user,
            is_completed=True
        ).count()
        
        # Temps total passé
        stats.total_time_spent_minutes = LessonProgress.objects.filter(
            student=user
        ).aggregate(total=models.Sum('time_spent'))['total'] or 0
        
        # Statistiques des certificats et badges
        stats.total_certificates_earned = UserCertificate.objects.filter(user=user).count()
        stats.total_badges_earned = UserBadge.objects.filter(user=user).count()
        
        # Statistiques des quiz
        from courses.models import QuizAttempt
        quiz_stats = QuizAttempt.objects.filter(student=user).aggregate(
            total_taken=models.Count('id'),
            total_passed=models.Count('id', filter=models.Q(is_passed=True)),
            avg_score=models.Avg('percentage')
        )
        
        stats.total_quizzes_taken = quiz_stats['total_taken'] or 0
        stats.total_quizzes_passed = quiz_stats['total_passed'] or 0
        stats.average_quiz_score = quiz_stats['avg_score'] or 0
        
        # Calculer la série de connexions
        self._calculate_streak(user, stats)
        
        stats.save()
    
    def _calculate_streak(self, user, stats):
        """
        Calculer la série de connexions
        """
        from datetime import timedelta
        
        # Sessions des 30 derniers jours
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_sessions = StudySession.objects.filter(
            user=user,
            started_at__gte=thirty_days_ago
        ).order_by('-started_at')
        
        if not recent_sessions.exists():
            stats.current_streak_days = 0
            return
        
        # Calculer la série actuelle
        current_streak = 0
        current_date = timezone.now().date()
        
        for session in recent_sessions:
            session_date = session.started_at.date()
            if session_date == current_date or session_date == current_date - timedelta(days=current_streak):
                current_streak += 1
                current_date = session_date - timedelta(days=1)
            else:
                break
        
        stats.current_streak_days = current_streak
        stats.longest_streak_days = max(stats.longest_streak_days, current_streak)


class BadgeService:
    """
    Service pour gérer les badges
    """
    
    def award_badge(self, user_id, badge_id):
        """
        Attribuer un badge à un utilisateur
        """
        try:
            user = User.objects.get(id=user_id)
            badge = Badge.objects.get(id=badge_id)
            
            # Vérifier si l'utilisateur a déjà ce badge
            if UserBadge.objects.filter(user=user, badge=badge).exists():
                return {
                    'success': False,
                    'error': 'L\'utilisateur a déjà ce badge'
                }
            
            # Attribuer le badge
            user_badge = UserBadge.objects.create(user=user, badge=badge)
            
            # Créer une réalisation
            Achievement.objects.create(
                user=user,
                achievement_type='badge_earned',
                title=f'Badge obtenu: {badge.name}',
                description=f'Vous avez obtenu le badge "{badge.name}"',
                data={
                    'badge_id': badge.id,
                    'badge_name': badge.name,
                    'badge_type': badge.badge_type
                }
            )
            
            return {
                'success': True,
                'badge': {
                    'id': user_badge.id,
                    'badge_name': badge.name,
                    'earned_at': user_badge.earned_at
                }
            }
            
        except User.DoesNotExist:
            return {
                'success': False,
                'error': 'Utilisateur non trouvé'
            }
        except Badge.DoesNotExist:
            return {
                'success': False,
                'error': 'Badge non trouvé'
            }
    
    def check_lesson_badges(self, user, lesson):
        """
        Vérifier les badges liés aux leçons
        """
        # Badge: Première leçon terminée
        if LessonProgress.objects.filter(student=user, is_completed=True).count() == 1:
            self._award_badge_by_criteria(user, 'first_lesson_completed')
        
        # Badge: 10 leçons terminées
        if LessonProgress.objects.filter(student=user, is_completed=True).count() == 10:
            self._award_badge_by_criteria(user, 'ten_lessons_completed')
        
        # Badge: 50 leçons terminées
        if LessonProgress.objects.filter(student=user, is_completed=True).count() == 50:
            self._award_badge_by_criteria(user, 'fifty_lessons_completed')
    
    def _award_badge_by_criteria(self, user, criteria):
        """
        Attribuer un badge basé sur des critères
        """
        try:
            badge = Badge.objects.get(criteria__contains={'type': criteria})
            if not UserBadge.objects.filter(user=user, badge=badge).exists():
                UserBadge.objects.create(user=user, badge=badge)
        except Badge.DoesNotExist:
            pass


class CertificateService:
    """
    Service pour gérer les certificats
    """
    
    def generate_course_certificate(self, user, course, issued_by):
        """
        Générer un certificat de cours
        """
        try:
            # Trouver le certificat de completion de cours
            certificate = Certificate.objects.filter(
                certificate_type='course_completion',
                is_active=True
            ).first()
            
            if not certificate:
                return {
                    'success': False,
                    'error': 'Aucun certificat de completion disponible'
                }
            
            # Vérifier qu'un certificat n'existe pas déjà
            if UserCertificate.objects.filter(user=user, course=course).exists():
                return {
                    'success': False,
                    'error': 'Certificat déjà existant'
                }
            
            # Créer le certificat
            user_certificate = UserCertificate.objects.create(
                user=user,
                certificate=certificate,
                course=course,
                issued_by=issued_by,
                certificate_data={
                    'course_title': course.title,
                    'instructor_name': course.instructor.get_full_name(),
                    'completion_date': timezone.now().strftime('%Y-%m-%d'),
                    'student_name': user.get_full_name(),
                }
            )
            
            # Créer une réalisation
            Achievement.objects.create(
                user=user,
                achievement_type='certificate_earned',
                title=f'Certificat obtenu: {course.title}',
                description=f'Vous avez obtenu un certificat pour le cours "{course.title}"',
                data={
                    'certificate_id': user_certificate.id,
                    'course_id': course.id,
                    'course_title': course.title
                }
            )
            
            return {
                'success': True,
                'certificate': {
                    'id': user_certificate.id,
                    'verification_code': user_certificate.verification_code,
                    'issued_at': user_certificate.issued_at
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_pdf_certificate(self, user_certificate):
        """
        Générer le PDF du certificat
        """
        # Ici, vous implémenteriez la génération de PDF
        # en utilisant des bibliothèques comme reportlab ou weasyprint
        # Pour l'instant, on retourne une URL simulée
        return f"/media/certificates/pdfs/{user_certificate.id}.pdf"
