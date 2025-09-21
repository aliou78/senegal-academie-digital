# progress/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import CourseEnrollment, LessonProgress, StudySession
from .services import ProgressService

@receiver(post_save, sender=LessonProgress)
def update_progress_on_lesson_change(sender, instance, created, **kwargs):
    """Mettre à jour la progression quand une leçon change"""
    if not created:  # Seulement pour les mises à jour
        # Mettre à jour la progression du module et du cours
        ProgressService.update_module_progress(instance.enrollment, instance.lesson.module)
        ProgressService.update_course_progress(instance.enrollment)

@receiver(post_save, sender=StudySession)
def update_streak_on_session_end(sender, instance, created, **kwargs):
    """Mettre à jour la série d'apprentissage quand une session se termine"""
    if instance.ended_at and not created:
        ProgressService.update_learning_streak(instance.user)

@receiver(pre_save, sender=CourseEnrollment)
def check_course_completion(sender, instance, **kwargs):
    """Vérifier si le cours est terminé et déclencher des actions"""
    if instance.pk:  # Mise à jour d'un objet existant
        try:
            old_instance = CourseEnrollment.objects.get(pk=instance.pk)
            
            # Si le cours vient d'être terminé
            if (old_instance.status != 'completed' and 
                instance.status == 'completed' and 
                not instance.completed_at):
                
                instance.completed_at = timezone.now()
                
                # Vérifier les achievements
                ProgressService.check_achievements(instance.user, course=instance.course)
                
        except CourseEnrollment.DoesNotExist:
            pass