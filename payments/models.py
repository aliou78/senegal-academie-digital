from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
import uuid

User = get_user_model()


class PaymentMethod(models.Model):
    """
    Méthodes de paiement disponibles
    """
    PAYMENT_TYPE_CHOICES = [
        ('stripe', 'Carte bancaire (Stripe)'),
        ('orange_money', 'Orange Money'),
        ('free_money', 'Free Money'),
        ('mtn_money', 'MTN Money'),
        ('bank_transfer', 'Virement bancaire'),
        ('cash', 'Espèces'),
    ]

    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name=_('Type de paiement')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    configuration = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Configuration')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Méthode de paiement')
        verbose_name_plural = _('Méthodes de paiement')

    def __str__(self):
        return self.name


class Payment(models.Model):
    """
    Modèle de paiement
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]

    CURRENCY_CHOICES = [
        ('XOF', 'Franc CFA (XOF)'),
        ('USD', 'Dollar américain (USD)'),
        ('EUR', 'Euro (EUR)'),
    ]

    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('ID de transaction')
    )
    
    # Utilisateur et montant
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Utilisateur')
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Montant')
    )
    
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='XOF',
        verbose_name=_('Devise')
    )
    
    # Méthode de paiement
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('Méthode de paiement')
    )
    
    # Statut et dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de modification'))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Date de completion'))
    
    # Détails du paiement
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Métadonnées'))
    
    # Références externes
    external_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('ID de paiement externe')
    )
    
    # Erreurs
    error_message = models.TextField(blank=True, null=True, verbose_name=_('Message d\'erreur'))

    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement {self.transaction_id} - {self.user.get_full_name()} ({self.amount} {self.currency})"


class CoursePayment(models.Model):
    """
    Paiement spécifique pour un cours
    """
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='course_payment',
        verbose_name=_('Paiement')
    )
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Cours')
    )
    
    enrollment = models.OneToOneField(
        'courses.Enrollment',
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name=_('Inscription')
    )

    class Meta:
        verbose_name = _('Paiement de cours')
        verbose_name_plural = _('Paiements de cours')

    def __str__(self):
        return f"Paiement cours {self.course.title} - {self.payment.user.get_full_name()}"


class Refund(models.Model):
    """
    Remboursement
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name=_('Paiement')
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Montant du remboursement')
    )
    
    reason = models.TextField(verbose_name=_('Raison du remboursement'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )
    
    external_refund_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('ID de remboursement externe')
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Date de traitement'))

    class Meta:
        verbose_name = _('Remboursement')
        verbose_name_plural = _('Remboursements')

    def __str__(self):
        return f"Remboursement {self.payment.transaction_id} - {self.amount} {self.payment.currency}"


class PaymentWebhook(models.Model):
    """
    Webhooks de paiement pour traiter les notifications des processeurs de paiement
    """
    PAYMENT_PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('orange_money', 'Orange Money'),
        ('free_money', 'Free Money'),
        ('mtn_money', 'MTN Money'),
    ]

    provider = models.CharField(
        max_length=20,
        choices=PAYMENT_PROVIDER_CHOICES,
        verbose_name=_('Fournisseur')
    )
    
    event_type = models.CharField(max_length=100, verbose_name=_('Type d\'événement'))
    event_id = models.CharField(max_length=100, unique=True, verbose_name=_('ID de l\'événement'))
    
    payload = models.JSONField(verbose_name=_('Données reçues'))
    processed = models.BooleanField(default=False, verbose_name=_('Traité'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Date de traitement'))

    class Meta:
        verbose_name = _('Webhook de paiement')
        verbose_name_plural = _('Webhooks de paiement')

    def __str__(self):
        return f"Webhook {self.provider} - {self.event_type}"


class InstructorCommission(models.Model):
    """
    Commission des formateurs
    """
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commissions',
        limit_choices_to={'role': 'instructor'},
        verbose_name=_('Formateur')
    )
    
    course_payment = models.ForeignKey(
        CoursePayment,
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name=_('Paiement de cours')
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Montant de la commission')
    )
    
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MinValueValidator(100)],
        verbose_name=_('Pourcentage de commission')
    )
    
    is_paid = models.BooleanField(default=False, verbose_name=_('Payé'))
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Date de paiement'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))

    class Meta:
        verbose_name = _('Commission de formateur')
        verbose_name_plural = _('Commissions de formateurs')

    def __str__(self):
        return f"Commission {self.instructor.get_full_name()} - {self.amount} {self.course_payment.payment.currency}"


class PaymentConfiguration(models.Model):
    """
    Configuration des paiements
    """
    # Commission des formateurs (par défaut 70%)
    instructor_commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.00,
        validators=[MinValueValidator(0), MinValueValidator(100)],
        verbose_name=_('Pourcentage de commission des formateurs')
    )
    
    # Frais de transaction
    transaction_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.50,
        validators=[MinValueValidator(0), MinValueValidator(100)],
        verbose_name=_('Pourcentage de frais de transaction')
    )
    
    # Montant minimum de paiement
    minimum_payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Montant minimum de paiement')
    )
    
    # Montant maximum de paiement
    maximum_payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000000.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Montant maximum de paiement')
    )
    
    # Configuration des méthodes de paiement
    stripe_enabled = models.BooleanField(default=True, verbose_name=_('Stripe activé'))
    orange_money_enabled = models.BooleanField(default=True, verbose_name=_('Orange Money activé'))
    free_money_enabled = models.BooleanField(default=True, verbose_name=_('Free Money activé'))
    mtn_money_enabled = models.BooleanField(default=True, verbose_name=_('MTN Money activé'))
    
    # Configuration des webhooks
    webhook_secret = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Secret des webhooks')
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de modification'))

    class Meta:
        verbose_name = _('Configuration des paiements')
        verbose_name_plural = _('Configurations des paiements')

    def __str__(self):
        return "Configuration des paiements"

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule configuration
        if not self.pk and PaymentConfiguration.objects.exists():
            raise ValueError("Une seule configuration de paiement est autorisée")
        super().save(*args, **kwargs)
