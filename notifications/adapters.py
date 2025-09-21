class FCMAdapter:
    def send_push(self, token, title, body):
        # Ici, tu pourras intégrer Firebase Cloud Messaging (FCM)
        print(f"📲 Push envoyé à {token}: {title} - {body}")
