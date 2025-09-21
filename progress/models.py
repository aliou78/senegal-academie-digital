from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class Badge(models.Model):
    """
    Badges pour récompenser les apprenants
    """
    BADGE_TYPE_CHOICES = [
        ('completion', 'Completion'),
        ('achievement', 'Achievement'),
        ('milestone', 'Milestone'),
        ('special', 'Special'),
    ]

    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    description = models.TextField(verbose_name=_('Description'))
    icon = models.CharField(max_length=50, verbose_name=_('Icône'))
    color = models.CharField(max_length=7, default='#007bff', verbose_name=_('Couleur'))
    badge_type = models.CharField(
        max_length=20,
        choices=BADGE_TYPE_CHOICES,
        default='achievement',
        verbose_name=_('Type de badge')
    )
    
    # Critères d'obtention
    criteria = models.JSONField(
        default=dict,
        verbose_name=_('Critères d\'obtention')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Badge')
        verbose_name_plural = _('Badges')

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """
    Badges obtenus par les utilisateurs
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name=_('Utilisateur')
    )
    
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_('Badge')
    )
    
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'obtention'))
    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'))

    class Meta:
        verbose_name = _('Badge utilisateur')
        verbose_name_plural = _('Badges utilisateurs')
        unique_together = ['user', 'badge']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.badge.name}"


class Certificate(models.Model):
    """
    Certificats de cours
    """
    CERTIFICATE_TYPE_CHOICES = [
        ('course_completion', 'Completion de cours'),
        ('skill_verification', 'Vérification de compétence'),
        ('professional', 'Certificat professionnel'),
        ('participation', 'Certificat de participation'),
    ]

    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    description = models.TextField(verbose_name=_('Description'))
    certificate_type = models.CharField(
        max_length=30,
        choices=CERTIFICATE_TYPE_CHOICES,
        default='course_completion',
        verbose_name=_('Type de certificat')
    )
    
    # Template du certificat
    template = models.TextField(verbose_name=_('Template HTML'))
    background_image = models.ImageField(
        upload_to='certificates/backgrounds/',
        blank=True,
        null=True,
        verbose_name=_('Image de fond')
    )
    
    # Critères d'obtention
    requirements = models.JSONField(
        default=dict,
        verbose_name=_('Exigences')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Certificat')
        verbose_name_plural = _('Certificats')

    def __str__(self):
        return self.name


class UserCertificate(models.Model):
    """
    Certificats obtenus par les utilisateurs
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name=_('Utilisateur')
    )
    
    certificate = models.ForeignKey(
        Certificate,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_('Certificat')
    )
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='certificates_issued',
        blank=True,
        null=True,
        verbose_name=_('Cours')
    )
    
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'émission'))
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates_issued',
        verbose_name=_('Émis par')
    )
    
    # Données du certificat
    certificate_data = models.JSONField(
        default=dict,
        verbose_name=_('Données du certificat')
    )
    
    # Fichier PDF généré
    pdf_file = models.FileField(
        upload_to='certificates/pdfs/',
        blank=True,
        null=True,
        verbose_name=_('Fichier PDF')
    )
    
    is_verified = models.BooleanField(default=False, verbose_name=_('Vérifié'))
    verification_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Code de vérification')
    )

    class Meta:
        verbose_name = _('Certificat utilisateur')
        verbose_name_plural = _('Certificats utilisateurs')
        unique_together = ['user', 'certificate', 'course']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.certificate.name}"

    def save(self, *args, **kwargs):
        if not self.verification_code:
            import secrets
            self.verification_code = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)


class LearningPath(models.Model):
    """
    Parcours d'apprentissage
    """
    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    description = models.TextField(verbose_name=_('Description'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    
    # Métadonnées
    duration_weeks = models.PositiveIntegerField(default=0, verbose_name=_('Durée (semaines)'))
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Débutant'),
            ('intermediate', 'Intermédiaire'),
            ('advanced', 'Avancé'),
        ],
        default='beginner',
        verbose_name=_('Niveau de difficulté')
    )
    
    # Contenu
    thumbnail = models.ImageField(
        upload_to='learning_paths/thumbnails/',
        blank=True,
        null=True,
        verbose_name=_('Miniature')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Parcours d\'apprentissage')
        verbose_name_plural = _('Parcours d\'apprentissage')

    def __str__(self):
        return self.name


class LearningPathCourse(models.Model):
    """
    Cours dans un parcours d'apprentissage
    """
    learning_path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('Parcours d\'apprentissage')
    )
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='learning_paths',
        verbose_name=_('Cours')
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))
    is_required = models.BooleanField(default=True, verbose_name=_('Obligatoire'))

    class Meta:
        verbose_name = _('Cours de parcours')
        verbose_name_plural = _('Cours de parcours')
        unique_together = ['learning_path', 'course']
        ordering = ['order']

    def __str__(self):
        return f"{self.learning_path.name} - {self.course.title}"


class UserLearningPath(models.Model):
    """
    Parcours d'apprentissage d'un utilisateur
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='learning_paths',
        verbose_name=_('Utilisateur')
    )
    
    learning_path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_('Parcours d\'apprentissage')
    )
    
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'inscription'))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Date de completion'))
    
    # Progression
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Pourcentage de progression')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))

    class Meta:
        verbose_name = _('Parcours utilisateur')
        verbose_name_plural = _('Parcours utilisateurs')
        unique_together = ['user', 'learning_path']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.learning_path.name}"


class Achievement(models.Model):
    """
    Réalisations des utilisateurs
    """
    ACHIEVEMENT_TYPE_CHOICES = [
        ('course_completed', 'Cours terminé'),
        ('learning_path_completed', 'Parcours terminé'),
        ('certificate_earned', 'Certificat obtenu'),
        ('badge_earned', 'Badge obtenu'),
        ('quiz_passed', 'Quiz réussi'),
        ('streak', 'Série de connexions'),
        ('time_spent', 'Temps passé'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name=_('Utilisateur')
    )
    
    achievement_type = models.CharField(
        max_length=30,
        choices=ACHIEVEMENT_TYPE_CHOICES,
        verbose_name=_('Type de réalisation')
    )
    
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(verbose_name=_('Description'))
    
    # Données spécifiques à la réalisation
    data = models.JSONField(
        default=dict,
        verbose_name=_('Données')
    )
    
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'obtention'))
    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'))

    class Meta:
        verbose_name = _('Réalisation')
        verbose_name_plural = _('Réalisations')
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"


class StudySession(models.Model):
    """
    Sessions d'étude des utilisateurs
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='study_sessions',
        verbose_name=_('Utilisateur')
    )
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='study_sessions',
        blank=True,
        null=True,
        verbose_name=_('Cours')
    )
    
    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='study_sessions',
        blank=True,
        null=True,
        verbose_name=_('Leçon')
    )
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Débuté à'))
    ended_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Terminé à'))
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name=_('Durée (minutes)'))
    
    # Progression pendant la session
    progress_made = models.JSONField(
        default=dict,
        verbose_name=_('Progression effectuée')
    )

    class Meta:
        verbose_name = _('Session d\'étude')
        verbose_name_plural = _('Sessions d\'étude')
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class UserStatistics(models.Model):
    """
    Statistiques des utilisateurs
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='statistics',
        verbose_name=_('Utilisateur')
    )
    
    # Statistiques générales
    total_courses_enrolled = models.PositiveIntegerField(default=0, verbose_name=_('Cours inscrits'))
    total_courses_completed = models.PositiveIntegerField(default=0, verbose_name=_('Cours terminés'))
    total_lessons_completed = models.PositiveIntegerField(default=0, verbose_name=_('Leçons terminées'))
    total_time_spent_minutes = models.PositiveIntegerField(default=0, verbose_name=_('Temps total passé (minutes)'))
    
    # Statistiques de progression
    current_streak_days = models.PositiveIntegerField(default=0, verbose_name=_('Série actuelle (jours)'))
    longest_streak_days = models.PositiveIntegerField(default=0, verbose_name=_('Plus longue série (jours)'))
    
    # Statistiques de certification
    total_certificates_earned = models.PositiveIntegerField(default=0, verbose_name=_('Certificats obtenus'))
    total_badges_earned = models.PositiveIntegerField(default=0, verbose_name=_('Badges obtenus'))
    
    # Statistiques de quiz
    total_quizzes_taken = models.PositiveIntegerField(default=0, verbose_name=_('Quiz passés'))
    total_quizzes_passed = models.PositiveIntegerField(default=0, verbose_name=_('Quiz réussis'))
    average_quiz_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_('Score moyen des quiz')
    )
    
    # Dernière mise à jour
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_('Dernière mise à jour'))

    class Meta:
        verbose_name = _('Statistiques utilisateur')
        verbose_name_plural = _('Statistiques utilisateurs')

    def __str__(self):
        return f"Statistiques de {self.user.get_full_name()}"
