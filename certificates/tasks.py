from celery import shared_task
from django.core.files.base import ContentFile
from .utils import generate_certificate
from django.core.files.storage import default_storage

@shared_task
def generate_certificate_task(user_id, course_id):
    from users.models import User
    from courses.models import Course

    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)

    pdf_buffer = generate_certificate(user.username, course.title)
    file_path = f"certificates/{user.username}_{course.id}.pdf"
    default_storage.save(file_path, ContentFile(pdf_buffer.read()))
    return file_path
