from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour Sénégal Académie Digital
    """
    ROLE_CHOICES = [
        ('student', 'Apprenant'),
        ('instructor', 'Formateur'),
        ('admin', 'Administrateur'),
        ('enterprise', 'Entreprise'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    ]
    
    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('wo', 'Wolof'),
        ('en', 'Anglais'),
    ]

    # Champs personnalisés
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name=_('Rôle')
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Téléphone')
    )
    
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de naissance')
    )
    
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Genre')
    )
    
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name=_('Photo de profil')
    )
    
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Biographie')
    )
    
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Localisation')
    )
    
    preferred_language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='fr',
        verbose_name=_('Langue préférée')
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('Compte vérifié')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de modification')
    )

    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


class UserProfile(models.Model):
    """
    Profil étendu pour les utilisateurs
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Utilisateur')
    )
    
    # Compétences
    skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Compétences')
    )
    
    # Expérience professionnelle
    experience = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Expérience')
    )
    
    # Éducation
    education = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Formation')
    )
    
    # Certifications
    certifications = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Certifications')
    )
    
    # Réseaux sociaux
    social_links = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Liens sociaux')
    )
    
    # Préférences de notification
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Préférences de notification')
    )

    class Meta:
        verbose_name = _('Profil utilisateur')
        verbose_name_plural = _('Profils utilisateurs')

    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"


class InstructorProfile(models.Model):
    """
    Profil spécialisé pour les formateurs
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='instructor_profile',
        verbose_name=_('Formateur')
    )
    
    # Informations professionnelles
    title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Titre professionnel')
    )
    
    company = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Entreprise')
    )
    
    years_of_experience = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Années d\'expérience')
    )
    
    # Spécialisations
    specializations = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Spécialisations')
    )
    
    # Tarif horaire
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Tarif horaire (FCFA)')
    )
    
    # Disponibilité
    availability = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Disponibilité')
    )
    
    # Statut
    is_approved = models.BooleanField(
        default=False,
        verbose_name=_('Approuvé')
    )
    
    approval_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Date d\'approbation')
    )

    class Meta:
        verbose_name = _('Profil formateur')
        verbose_name_plural = _('Profils formateurs')

    def __str__(self):
        return f"Formateur: {self.user.get_full_name()}"


class EnterpriseProfile(models.Model):
    """
    Profil pour les entreprises
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='enterprise_profile',
        verbose_name=_('Entreprise')
    )
    
    # Informations de l'entreprise
    company_name = models.CharField(
        max_length=100,
        verbose_name=_('Nom de l\'entreprise')
    )
    
    company_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Type d\'entreprise')
    )
    
    industry = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Secteur d\'activité')
    )
    
    company_size = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Taille de l\'entreprise')
    )
    
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Site web')
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    
    # Contact
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Personne de contact')
    )
    
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Téléphone de contact')
    )

    class Meta:
        verbose_name = _('Profil entreprise')
        verbose_name_plural = _('Profils entreprises')

    def __str__(self):
        return self.company_name
