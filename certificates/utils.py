from reportlab.pdfgen import canvas
from io import BytesIO

def generate_certificate(user_name, course_title):
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 750, "CERTIFICAT DE RÉUSSITE")
    c.setFont("Helvetica", 14)
    c.drawString(100, 700, f"Décerné à : {user_name}")
    c.drawString(100, 650, f"Pour avoir complété le cours : {course_title}")
    c.save()
    buffer.seek(0)
    return buffer
