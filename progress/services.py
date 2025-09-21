# progress/services.py
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from datetime import date, timedelta
from decimal import Decimal

class ProgressService:
    """Service pour la gestion de la progression"""
    
    @staticmethod
    def update_course_progress(enrollment):
        """Mettre à jour la progression globale d'un cours"""
        from .models import LessonProgress
        
        # Récupérer toutes les leçons du cours
        course_lessons = enrollment.course.lessons.all()
        if not course_lessons.exists():
            return
        
        # Calculer la progression moyenne
        lesson_progresses = LessonProgress.objects.filter(
            enrollment=enrollment,
            lesson__in=course_lessons
        )
        
        if lesson_progresses.exists():
            avg_progress = lesson_progresses.aggregate(
                avg=Avg('progress_percentage')
            )['avg'] or 0
            
            total_time = lesson_progresses.aggregate(
                total=Sum('time_spent')
            )['total'] or 0
            
            # Mettre à jour l'inscription
            enrollment.progress_percentage = round(avg_progress, 2)
            enrollment.total_time_spent = total_time
            enrollment.last_accessed = timezone.now()
            
            # Calculer la note moyenne si applicable
            scores = lesson_progresses.filter(score__isnull=False)
            if scores.exists():
                enrollment.current_grade = scores.aggregate(
                    avg=Avg('score')
                )['avg']
            
            enrollment.save()
    
    @staticmethod
    def update_module_progress(enrollment, module):
        """Mettre à jour la progression d'un module"""
        from .models import ModuleProgress, LessonProgress
        
        # Récupérer ou créer la progression du module
        module_progress, created = ModuleProgress.objects.get_or_create(
            enrollment=enrollment,
            module=module
        )
        
        # Récupérer les leçons du module
        module_lessons = module.lessons.all()
        if not module_lessons.exists():
            return
        
        # Calculer la progression
        lesson_progresses = LessonProgress.objects.filter(
            enrollment=enrollment,
            lesson__in=module_lessons
        )
        
        if lesson_progresses.exists():
            avg_progress = lesson_progresses.aggregate(
                avg=Avg('progress_percentage')
            )['avg'] or 0
            
            total_time = lesson_progresses.aggregate(
                total=Sum('time_spent')
            )['total'] or 0
            
            # Mettre à jour
            module_progress.progress_percentage = round(avg_progress, 2)
            module_progress.time_spent = total_time
            
            # Marquer comme commencé/terminé
            if avg_progress > 0 and not module_progress.is_started:
                module_progress.is_started = True
                module_progress.started_at = timezone.now()
            
            if avg_progress >= 100 and not module_progress.is_completed:
                module_progress.is_completed = True
                module_progress.completed_at = timezone.now()
            
            # Calculer le score moyen
            scores = lesson_progresses.filter(score__isnull=False)
            if scores.exists():
                module_progress.score = scores.aggregate(
                    avg=Avg('score')
                )['avg']
            
            module_progress.save()
    
    @staticmethod
    def create_lesson_progress(enrollment, lesson):
        """Créer la progression d'une leçon si elle n'existe pas"""
        from .models import LessonProgress
        
        lesson_progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
        return lesson_progress
    
    @staticmethod
    def update_learning_streak(user):
        """Mettre à jour la série d'apprentissage"""
        from .models import LearningStreak, StudySession
        
        streak, created = LearningStreak.objects.get_or_create(user=user)
        today = date.today()
        
        # Vérifier si l'utilisateur a étudié aujourd'hui
        has_studied_today = StudySession.objects.filter(
            user=user,
            started_at__date=today
        ).exists()
        
        if has_studied_today:
            # Si première activité ou activité consécutive
            if streak.last_activity_date == today - timedelta(days=1) or created:
                streak.current_streak += 1
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak
            elif streak.last_activity_date != today:
                # Redémarrer la série
                streak.current_streak = 1
            
            streak.last_activity_date = today
            streak.is_active = True
        else:
            # Vérifier si la série est cassée
            if streak.last_activity_date and (today - streak.last_activity_date).days > 1:
                streak.current_streak = 0
                streak.is_active = False
        
        streak.save()
        
        # Vérifier les achievements de série
        ProgressService.check_streak_achievements(user, streak.current_streak)
    
    @staticmethod
    def check_achievements(user, course=None, lesson=None):
        """Vérifier et créer de nouveaux achievements"""
        from .models import UserAchievement, CourseEnrollment
        
        achievements_to_create = []
        
        # Achievement de completion de cours
        if course:
            # Vérifier si c'est le premier cours terminé
            completed_courses = CourseEnrollment.objects.filter(
                user=user, status='completed'
            ).count()
            
            if completed_courses == 1:
                achievements_to_create.append({
                    'achievement_type': 'course_completion',
                    'title': 'Premier cours terminé',
                    'description': 'Félicitations pour avoir terminé votre premier cours !',
                    'points': 100,
                    'course': course
                })
            elif completed_courses == 5:
                achievements_to_create.append({
                    'achievement_type': 'course_completion',
                    'title': 'Apprenant assidu',
                    'description': '5 cours terminés avec succès !',
                    'points': 250,
                    'course': course
                })
        
        # Créer les achievements
        for achievement_data in achievements_to_create:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement_type=achievement_data['achievement_type'],
                title=achievement_data['title'],
                defaults=achievement_data
            )
    
    @staticmethod
    def check_lesson_achievements(user, lesson):
        """Vérifier les achievements liés aux leçons"""
        from .models import UserAchievement, LessonProgress
        
        # Compter les leçons terminées
        completed_lessons = LessonProgress.objects.filter(
            enrollment__user=user,
            status='completed'
        ).count()
        
        achievements_to_create = []
        
        if completed_lessons == 10:
            achievements_to_create.append({
                'achievement_type': 'course_completion',
                'title': 'Explorateur',
                'description': '10 leçons terminées !',
                'points': 50,
                'lesson': lesson
            })
        elif completed_lessons == 50:
            achievements_to_create.append({
                'achievement_type': 'course_completion',
                'title': 'Étudiant dévoué',
                'description': '50 leçons terminées !',
                'points': 200,
                'lesson': lesson
            })
        
        # Créer les achievements
        for achievement_data in achievements_to_create:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement_type=achievement_data['achievement_type'],
                title=achievement_data['title'],
                defaults=achievement_data
            )
    
    @staticmethod
    def check_streak_achievements(user, streak_days):
        """Vérifier les achievements de série"""
        from .models import UserAchievement
        
        achievements_to_create = []
        
        if streak_days == 7:
            achievements_to_create.append({
                'achievement_type': 'streak',
                'title': 'Une semaine de régularité',
                'description': '7 jours consécutifs d\'apprentissage !',
                'points': 75
            })
        elif streak_days == 30:
            achievements_to_create.append({
                'achievement_type': 'streak',
                'title': 'Champion de la régularité',
                'description': '30 jours consécutifs d\'apprentissage !',
                'points': 300
            })
        
        # Créer les achievements
        for achievement_data in achievements_to_create:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement_type=achievement_data['achievement_type'],
                title=achievement_data['title'],
                defaults=achievement_data
            )
    
    @staticmethod
    def generate_progress_report(user, report_type='weekly'):
        """Générer un rapport de progression"""
        from .models import ProgressReport, CourseEnrollment, StudySession
        
        # Définir la période
        end_date = date.today()
        if report_type == 'weekly':
            start_date = end_date - timedelta(days=7)
        elif report_type == 'monthly':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Collecter les statistiques
        enrollments = CourseEnrollment.objects.filter(user=user)
        sessions = StudySession.objects.filter(
            user=user,
            started_at__date__range=[start_date, end_date]
        )
        
        courses_enrolled = enrollments.count()
        courses_completed = enrollments.filter(
            status='completed',
            completed_at__date__range=[start_date, end_date]
        ).count()
        
        from .models import LessonProgress
        lessons_completed = LessonProgress.objects.filter(
            enrollment__user=user,
            status='completed',
            completed_at__date__range=[start_date, end_date]
        ).count()
        
        total_time = sessions.aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        
        average_score = enrollments.filter(
            current_grade__isnull=False
        ).aggregate(
            avg=Avg('current_grade')
        )['avg']
        
        # Données détaillées
        detailed_data = {
            'daily_activity': [],
            'course_progress': [],
            'achievements_earned': []
        }
        
        # Activité quotidienne
        for i in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=i)
            day_sessions = sessions.filter(started_at__date=current_date)
            
            detailed_data['daily_activity'].append({
                'date': current_date.isoformat(),
                'sessions': day_sessions.count(),
                'time_minutes': day_sessions.aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
            })
        
        # Progression des cours
        for enrollment in enrollments:
            detailed_data['course_progress'].append({
                'course_title': enrollment.course.title,
                'progress_percentage': float(enrollment.progress_percentage),
                'time_spent': enrollment.total_time_spent,
                'status': enrollment.status
            })
        
        # Créer le rapport
        report = ProgressReport.objects.create(
            user=user,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            courses_enrolled=courses_enrolled,
            courses_completed=courses_completed,
            lessons_completed=lessons_completed,
            total_time_minutes=total_time,
            average_score=average_score,
            detailed_data=detailed_data
        )
        
        return report