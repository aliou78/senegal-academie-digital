# contact/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, mail_admins
from django.conf import settings
import threading

from .models import ContactMessage

def send_admin_notification(subject, message, recipient_list=None):
    """
    run send_mail in a background thread to avoid blocking request/response.
    For production, use Celery / RQ instead.
    """
    def _send():
        try:
            if getattr(settings, "EMAIL_USE_ADMIN", False):
                # mail_admins sends to ADMINS configured in settings
                mail_admins(subject, message, fail_silently=True)
            else:
                # fallback: use default from settings to send to single admin email if set
                admin_email = getattr(settings, "CONTACT_ADMIN_EMAIL", None)
                if admin_email:
                    send_mail(subject, message, getattr(settings, "DEFAULT_FROM_EMAIL", admin_email), [admin_email], fail_silently=True)
        except Exception:
            pass

    t = threading.Thread(target=_send)
    t.daemon = True
    t.start()

@receiver(post_save, sender=ContactMessage)
def notify_admin_on_new_message(sender, instance: ContactMessage, created, **kwargs):
    if not created:
        return
    subject = f"[Contact] Nouveau message de {instance.full_name}"
    body = (
        f"Nom: {instance.full_name}\n"
        f"Email: {instance.email}\n"
        f"Adresse: {instance.address}\n"
        f"IP: {instance.ip_address}\n"
        f"User-Agent: {instance.user_agent}\n\n"
        f"Message:\n{instance.message}\n\n"
        f"Envoyé le: {instance.created_at}\n"
    )
    send_admin_notification(subject, body)
