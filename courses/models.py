from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Category(models.Model):
    """
    Catégorie de cours
    """
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Icône'))
    color = models.CharField(max_length=7, default='#007bff', verbose_name=_('Couleur'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    """
    Modèle de cours
    """
    LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]

    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('wo', 'Wolof'),
        ('en', 'Anglais'),
    ]

    # Informations de base
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(verbose_name=_('Description'))
    short_description = models.TextField(max_length=500, verbose_name=_('Description courte'))
    
    # Métadonnées
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses',
        limit_choices_to={'role': 'instructor'},
        verbose_name=_('Formateur')
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name=_('Catégorie')
    )
    
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name=_('Niveau')
    )
    
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='fr',
        verbose_name=_('Langue')
    )
    
    # Contenu
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/',
        blank=True,
        null=True,
        verbose_name=_('Miniature')
    )
    
    video_intro = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Vidéo d\'introduction')
    )
    
    # Prix et durée
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Prix (FCFA)')
    )
    
    duration_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Durée (heures)')
    )
    
    # Statut et dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Statut')
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('Mis en avant')
    )
    
    is_certified = models.BooleanField(
        default=False,
        verbose_name=_('Certifié')
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de modification'))
    published_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Date de publication'))

    class Meta:
        verbose_name = _('Cours')
        verbose_name_plural = _('Cours')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_enrolled_students_count(self):
        return self.enrollments.filter(is_active=True).count()

    def get_average_rating(self):
        ratings = self.reviews.filter(is_active=True)
        if ratings.exists():
            return sum(rating.rating for rating in ratings) / ratings.count()
        return 0


class CourseModule(models.Model):
    """
    Module d'un cours
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name=_('Cours')
    )
    
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))
    is_published = models.BooleanField(default=True, verbose_name=_('Publié'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Module de cours')
        verbose_name_plural = _('Modules de cours')
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """
    Leçon d'un module
    """
    LESSON_TYPE_CHOICES = [
        ('video', 'Vidéo'),
        ('text', 'Texte'),
        ('quiz', 'Quiz'),
        ('assignment', 'Devoir'),
        ('live', 'Classe virtuelle'),
    ]

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('Module')
    )
    
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    content = models.TextField(blank=True, null=True, verbose_name=_('Contenu'))
    
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        default='video',
        verbose_name=_('Type de leçon')
    )
    
    video_url = models.URLField(blank=True, null=True, verbose_name=_('URL vidéo'))
    video_duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Durée vidéo (minutes)')
    )
    
    attachment = models.FileField(
        upload_to='courses/attachments/',
        blank=True,
        null=True,
        verbose_name=_('Fichier joint')
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))
    is_published = models.BooleanField(default=True, verbose_name=_('Publié'))
    is_free = models.BooleanField(default=False, verbose_name=_('Gratuit'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Leçon')
        verbose_name_plural = _('Leçons')
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Enrollment(models.Model):
    """
    Inscription à un cours
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Étudiant')
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('Cours')
    )
    
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'inscription'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Date de completion'))
    
    # Progression
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Pourcentage de progression')
    )

    class Meta:
        verbose_name = _('Inscription')
        verbose_name_plural = _('Inscriptions')
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title}"


class LessonProgress(models.Model):
    """
    Progression d'une leçon
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name=_('Étudiant')
    )
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name=_('Leçon')
    )
    
    is_completed = models.BooleanField(default=False, verbose_name=_('Terminé'))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Date de completion'))
    time_spent = models.PositiveIntegerField(default=0, verbose_name=_('Temps passé (minutes)'))
    last_position = models.PositiveIntegerField(default=0, verbose_name=_('Dernière position (secondes)'))

    class Meta:
        verbose_name = _('Progression de leçon')
        verbose_name_plural = _('Progressions de leçons')
        unique_together = ['student', 'lesson']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.lesson.title}"


class CourseReview(models.Model):
    """
    Avis sur un cours
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_reviews',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Étudiant')
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Cours')
    )
    
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('Note')
    )
    
    comment = models.TextField(blank=True, null=True, verbose_name=_('Commentaire'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Avis de cours')
        verbose_name_plural = _('Avis de cours')
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} ({self.rating}/5)"


class Quiz(models.Model):
    """
    Quiz d'une leçon
    """
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='quiz',
        verbose_name=_('Leçon')
    )
    
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    time_limit = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Limite de temps (minutes)')
    )
    
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Score de passage (%)')
    )
    
    max_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name=_('Nombre maximum de tentatives')
    )
    
    is_published = models.BooleanField(default=True, verbose_name=_('Publié'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quiz')

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class QuizQuestion(models.Model):
    """
    Question d'un quiz
    """
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Choix multiple'),
        ('true_false', 'Vrai/Faux'),
        ('text', 'Texte libre'),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Quiz')
    )
    
    question_text = models.TextField(verbose_name=_('Question'))
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='multiple_choice',
        verbose_name=_('Type de question')
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))
    points = models.PositiveIntegerField(default=1, verbose_name=_('Points'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Question de quiz')
        verbose_name_plural = _('Questions de quiz')
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - {self.question_text[:50]}..."


class QuizAnswer(models.Model):
    """
    Réponse d'une question de quiz
    """
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Question')
    )
    
    answer_text = models.TextField(verbose_name=_('Réponse'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Correct'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))

    class Meta:
        verbose_name = _('Réponse de quiz')
        verbose_name_plural = _('Réponses de quiz')
        ordering = ['order']

    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.answer_text[:30]}..."


class QuizAttempt(models.Model):
    """
    Tentative de quiz par un étudiant
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_('Étudiant')
    )
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('Quiz')
    )
    
    score = models.PositiveIntegerField(default=0, verbose_name=_('Score'))
    percentage = models.PositiveIntegerField(default=0, verbose_name=_('Pourcentage'))
    is_passed = models.BooleanField(default=False, verbose_name=_('Réussi'))
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Débuté à'))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Terminé à'))
    time_taken = models.PositiveIntegerField(default=0, verbose_name=_('Temps pris (minutes)'))

    class Meta:
        verbose_name = _('Tentative de quiz')
        verbose_name_plural = _('Tentatives de quiz')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.quiz.title} ({self.percentage}%)"
