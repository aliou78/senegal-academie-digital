from celery import shared_task
from .utils import send_email_notification

@shared_task
def send_course_notification(user_id, course_title):
    from users.models import User
    user = User.objects.get(id=user_id)
    send_email_notification(user, "Nouveau cours disponible", f"Découvrez {course_title}")
