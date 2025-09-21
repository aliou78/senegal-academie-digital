from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Message)
def notify_topic_author(sender, instance, created, **kwargs):
    if not created:
        return
    topic = instance.topic
    author = topic.author
    # envoi console/email simple si l'auteur souhaite être notifié (améliorer plus tard)
    if author and author.email:
        subject = f"Nouveau message sur votre sujet: {topic.title}"
        body = f"Bonjour {author.username},\n\nUn nouvel utilisateur a répondu à votre sujet \"{topic.title}\".\n\nMessage:\n{instance.content}\n\n--\nSénégal Académie Digital"
        # send_mail en console si EMAIL_BACKEND = console
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [author.email], fail_silently=True)
