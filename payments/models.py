from django.db import models
from django.conf import settings

class Payment(models.Model):
    METHOD_CHOICES = [
        ("orange_money", "Orange Money"),
        ("wave", "Wave"),
        ("free_money", "Free Money"),
        ("stripe", "Carte Bancaire (Stripe)"),
        ("paypal", "PayPal"),
    ]

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("completed", "Terminé"),
        ("failed", "Échoué"),
        ("canceled", "Annulé"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.amount} CFA via {self.method}"
