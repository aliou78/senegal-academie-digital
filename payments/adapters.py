import requests
import os

class MobileMoneyAdapter:
    def __init__(self):
        self.base = os.getenv("MOBILE_MONEY_API_URL")
        self.api_key = os.getenv("MOBILE_MONEY_API_KEY")

    def create_payment(self, phone, amount, external_id):
        # Exemple: POST -> provider. Retourner dict avec status & provider_reference
        payload = {"phone":phone,"amount":str(amount),"external_id":external_id}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # simulation: désactiver requête réelle si clé absente
        if not self.api_key or not self.base:
            return {"status":"pending","provider_reference":"SIM-"+external_id}
        r = requests.post(f"{self.base}/payments", json=payload, headers=headers, timeout=10)
        return r.json()

class StripeAdapter:
    def __init__(self):
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.stripe = stripe

    def create_payment_intent(self, amount, currency="usd"):
        intent = self.stripe.PaymentIntent.create(amount=int(amount*100), currency=currency)
        return intent
