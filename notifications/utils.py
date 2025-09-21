def send_email_notification(user, subject, message):
    # Ici tu peux intégrer Django EmailBackend
    print(f"📧 Email envoyé à {user.email} : {subject}")
