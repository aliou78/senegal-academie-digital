import os
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import Enrollment, Certificate

@shared_task
def generate_certificate_task(enrollment_id):
    """
    Generate a simple PDF certificate for the enrollment and save it to Certificate.pdf_file.
    Enrollment id passed as string (UUID) is fine.
    """
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
    except Enrollment.DoesNotExist:
        return {'error':'enrollment not found'}

    # Create PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    p.setFont('Helvetica-Bold', 22)
    p.drawCentredString(width/2, height - 120, "CERTIFICAT D'ACHÈVEMENT")

    # Student & course info
    p.setFont('Helvetica', 14)
    student_name = str(enrollment.student)
    course_title = enrollment.course.title
    p.drawCentredString(width/2, height - 180, f"Ce certificat est décerné à : {student_name}")
    p.drawCentredString(width/2, height - 210, f"Pour la réussite du cours : {course_title}")
    p.drawCentredString(width/2, height - 260, f"Date : {enrollment.enrolled_at.date()}")

    # Footer / signature line
    p.setFont('Helvetica-Oblique', 12)
    p.drawString(60, 60, "Sénégal Académie Digital")
    p.drawString(width - 220, 60, "Signature du formateur")

    p.showPage()
    p.save()
    buffer.seek(0)

    fname = f'certificate_{enrollment.id}.pdf'
    content = ContentFile(buffer.read())

    cert = Certificate.objects.create(enrollment=enrollment)
    cert.pdf_file.save(fname, content)
    cert.save()
    return {'ok': True, 'certificate_id': str(cert.id)}
