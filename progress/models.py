# progress/models.py - Version corrigée sans dépendances courses_app
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

User = get_user_model()

class CourseEnrollment(models.Model):
    """Inscription d'un utilisateur à un cours"""
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('paused', 'En pause'),
        ('completed', 'Terminé'),
        ('dropped', 'Abandonné'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    course_id = models.PositiveIntegerField(verbose_name="ID du cours")  # Référence simple
    course_title = models.CharField(max_length=200, verbose_name="Titre du cours")  # Dénormalisé
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Statut")
    
    # Dates importantes
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de début")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name="Dernier accès")
    
    # Progression
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Pourcentage de progression"
    )
    
    # Temps passé (en minutes)
    total_time_spent = models.PositiveIntegerField(default=0, verbose_name="Temps total (minutes)")
    
    # Notes et évaluations
    current_grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Note actuelle"
    )
    
    # Certificat
    certificate_issued = models.BooleanField(default=False, verbose_name="Certificat émis")
    certificate_date = models.DateTimeField(null=True, blank=True, verbose_name="Date du certificat")
    
    class Meta:
        unique_together = ['user', 'course_id']
        verbose_name = "Inscription au cours"
        verbose_name_plural = "Inscriptions aux cours"
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.user} - {self.course_title} ({self.progress_percentage}%)"
    
    @property
    def is_completed(self):
        return self.status == 'completed' and self.progress_percentage >= 100
    
    @property
    def estimated_completion_date(self):
        """Estimation de la date de fin basée sur le rythme actuel"""
        if self.progress_percentage > 0 and self.total_time_spent > 0:
            # Calcul simple basé sur le rythme actuel
            days_since_start = (timezone.now() - self.started_at).days if self.started_at else 1
            remaining_percentage = 100 - float(self.progress_percentage)
            if float(self.progress_percentage) > 0:
                estimated_days = (remaining_percentage / float(self.progress_percentage)) * days_since_start
                return timezone.now() + timedelta(days=estimated_days)
        return None

class ModuleProgress(models.Model):
    """Progression dans un module spécifique"""
    
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, verbose_name="Inscription")
    module_id = models.PositiveIntegerField(verbose_name="ID du module")  # Référence simple
    module_title = models.CharField(max_length=200, verbose_name="Titre du module")  # Dénormalisé
    module_order = models.PositiveIntegerField(default=1, verbose_name="Ordre du module")
    
    # État du module
    is_started = models.BooleanField(default=False, verbose_name="Commencé")
    is_completed = models.BooleanField(default=False, verbose_name="Terminé")
    
    # Dates
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de début")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    
    # Progression
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Progression (%)"
    )
    
    # Temps passé (en minutes)
    time_spent = models.PositiveIntegerField(default=0, verbose_name="Temps passé (minutes)")
    
    # Score du module
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score"
    )
    
    class Meta:
        unique_together = ['enrollment', 'module_id']
        verbose_name = "Progression du module"
        verbose_name_plural = "Progressions des modules"
        ordering = ['module_order']  # Corrigé
    
    def __str__(self):
        return f"{self.enrollment.user} - {self.module_title} ({self.progress_percentage}%)"

class LessonProgress(models.Model):
    """Progression dans une leçon spécifique"""
    
    STATUS_CHOICES = [
        ('not_started', 'Non commencé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('skipped', 'Ignoré'),
    ]
    
    LESSON_TYPE_CHOICES = [
        ('video', 'Vidéo'),
        ('text', 'Texte'),
        ('quiz', 'Quiz'),
        ('document', 'Document'),
        ('interactive', 'Interactif'),
    ]
    
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, verbose_name="Inscription")
    lesson_id = models.PositiveIntegerField(verbose_name="ID de la leçon")  # Référence simple
    lesson_title = models.CharField(max_length=200, verbose_name="Titre de la leçon")  # Dénormalisé
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES, default='text', verbose_name="Type de leçon")
    lesson_order = models.PositiveIntegerField(default=1, verbose_name="Ordre de la leçon")
    estimated_duration = models.PositiveIntegerField(default=0, verbose_name="Durée estimée (minutes)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name="Statut")
    
    # Dates
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de début")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    last_accessed = models.DateTimeField(auto_now=True, verbose_name="Dernier accès")
    
    # Progression
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Progression (%)"
    )
    
    # Temps passé (en minutes)
    time_spent = models.PositiveIntegerField(default=0, verbose_name="Temps passé (minutes)")
    
    # Position dans la leçon (pour les vidéos, documents, etc.)
    current_position = models.PositiveIntegerField(default=0, verbose_name="Position actuelle")
    
    # Note de la leçon (si applicable)
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score"
    )
    
    # Nombre de tentatives (pour les quiz)
    attempts = models.PositiveIntegerField(default=0, verbose_name="Nombre de tentatives")
    
    class Meta:
        unique_together = ['enrollment', 'lesson_id']
        verbose_name = "Progression de la leçon"
        verbose_name_plural = "Progressions des leçons"
        ordering = ['lesson_order']  # Corrigé
    
    def __str__(self):
        return f"{self.enrollment.user} - {self.lesson_title} ({self.status})"
    
    @property
    def is_completed(self):
        return self.status == 'completed' and self.progress_percentage >= 100

class QuizAttempt(models.Model):
    """Tentative de quiz"""
    
    lesson_progress = models.ForeignKey(LessonProgress, on_delete=models.CASCADE, verbose_name="Progression leçon")
    quiz_id = models.PositiveIntegerField(verbose_name="ID du quiz")  # Référence simple
    quiz_title = models.CharField(max_length=200, verbose_name="Titre du quiz")  # Dénormalisé
    quiz_passing_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=70,
        verbose_name="Score minimum"
    )
    
    # Informations de la tentative
    attempt_number = models.PositiveIntegerField(verbose_name="Numéro de tentative")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Débuté à")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Terminé à")
    
    # Résultats
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score (%)"
    )
    
    # Questions
    total_questions = models.PositiveIntegerField(verbose_name="Total questions")
    correct_answers = models.PositiveIntegerField(verbose_name="Bonnes réponses")
    
    # Temps passé (en secondes)
    time_taken = models.PositiveIntegerField(verbose_name="Temps pris (secondes)")
    
    # État
    is_passed = models.BooleanField(default=False, verbose_name="Réussi")
    
    class Meta:
        unique_together = ['lesson_progress', 'quiz_id', 'attempt_number']
        verbose_name = "Tentative de quiz"
        verbose_name_plural = "Tentatives de quiz"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.lesson_progress.enrollment.user} - {self.quiz_title} - Tentative {self.attempt_number}"

class StudySession(models.Model):
    """Session d'étude d'un utilisateur"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    course_id = models.PositiveIntegerField(verbose_name="ID du cours")  # Référence simple
    course_title = models.CharField(max_length=200, verbose_name="Titre du cours")  # Dénormalisé
    lesson_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID de la leçon")
    lesson_title = models.CharField(max_length=200, blank=True, verbose_name="Titre de la leçon")
    
    # Informations de la session
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Début")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Fin")
    
    # Durée (calculée automatiquement)
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name="Durée (minutes)")
    
    # Activités pendant la session
    lessons_viewed = models.PositiveIntegerField(default=0, verbose_name="Leçons vues")
    quizzes_attempted = models.PositiveIntegerField(default=0, verbose_name="Quiz tentés")
    
    # Engagement
    active_time_minutes = models.PositiveIntegerField(default=0, verbose_name="Temps actif (minutes)")
    
    class Meta:
        verbose_name = "Session d'étude"
        verbose_name_plural = "Sessions d'étude"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user} - {self.course_title} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"

class UserAchievement(models.Model):
    """Réalisations et badges des utilisateurs"""
    
    ACHIEVEMENT_TYPES = [
        ('course_completion', 'Cours terminé'),
        ('quiz_master', 'Maître du quiz'),
        ('streak', 'Série d\'étude'),
        ('time_spent', 'Temps passé'),
        ('perfect_score', 'Score parfait'),
        ('fast_learner', 'Apprenant rapide'),
        ('consistent', 'Régularité'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES, verbose_name="Type")
    title = models.CharField(max_length=100, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    
    # Métadonnées
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Obtenu le")
    points = models.PositiveIntegerField(default=0, verbose_name="Points")
    
    # Références optionnelles (références simples)
    course_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID du cours")
    lesson_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID de la leçon")
    
    class Meta:
        verbose_name = "Réalisation"
        verbose_name_plural = "Réalisations"
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user} - {self.title}"

class LearningStreak(models.Model):
    """Série d'apprentissage consécutif"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    
    # Informations de la série
    start_date = models.DateField(auto_now_add=True, verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    current_streak = models.PositiveIntegerField(default=0, verbose_name="Série actuelle")
    longest_streak = models.PositiveIntegerField(default=0, verbose_name="Plus longue série")
    
    # Dernière activité
    last_activity_date = models.DateField(auto_now_add=True, verbose_name="Dernière activité")
    
    # État
    is_active = models.BooleanField(default=True, verbose_name="Active")
    
    class Meta:
        verbose_name = "Série d'apprentissage"
        verbose_name_plural = "Séries d'apprentissage"
        ordering = ['-current_streak']
    
    def __str__(self):
        return f"{self.user} - Série: {self.current_streak} jours"

class ProgressReport(models.Model):
    """Rapport de progression généré automatiquement"""
    
    REPORT_TYPES = [
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('course_completion', 'Fin de cours'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="Type de rapport")
    
    # Période couverte
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    
    # Statistiques
    courses_enrolled = models.PositiveIntegerField(default=0, verbose_name="Cours inscrits")
    courses_completed = models.PositiveIntegerField(default=0, verbose_name="Cours terminés")
    lessons_completed = models.PositiveIntegerField(default=0, verbose_name="Leçons terminées")
    total_time_minutes = models.PositiveIntegerField(default=0, verbose_name="Temps total (minutes)")
    average_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Score moyen"
    )
    
    # Données détaillées (JSON)
    detailed_data = models.JSONField(default=dict, verbose_name="Données détaillées")
    
    # Génération
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Généré le")
    
    class Meta:
        verbose_name = "Rapport de progression"
        verbose_name_plural = "Rapports de progression"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.user} - Rapport {self.report_type} ({self.start_date} - {self.end_date})"