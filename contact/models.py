from django.db import models

# Create your models here.
# contact/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password

class ContactMessage(models.Model):
    """
    Stocke un message de contact envoyé via le formulaire.
    Si le visiteur envoie un mot de passe, on le stocke hashé (non recommandé par défaut,
    mais on le gère de manière sûre si nécessaire).
    """
    full_name = models.CharField("Nom complet", max_length=255)
    address = models.CharField("Adresse", max_length=255, blank=True, null=True)
    email = models.EmailField("Email")
    # stocker password hashé si fourni — mieux vaut ne pas demander le mot de passe du visiteur.
    password_hash = models.CharField("Mot de passe (hash)", max_length=255, blank=True, null=True)
    message = models.TextField("Message")
    user_agent = models.CharField("User agent", max_length=512, blank=True, null=True)
    ip_address = models.GenericIPAddressField("IP address", blank=True, null=True)
    honeypot = models.CharField("Honeypot (anti-spam)", max_length=255, blank=True, null=True)
    created_at = models.DateTimeField("Date d'envoi", default=timezone.now)
    is_read = models.BooleanField("Lu", default=False)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} <{self.email}> - {self.created_at:%Y-%m-%d %H:%M}"

    def set_password(self, raw_password: str):
        """Hash and store the password safely (if you must collect it)."""
        if raw_password:
            self.password_hash = make_password(raw_password)
        else:
            self.password_hash = None
