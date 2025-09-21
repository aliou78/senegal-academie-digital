from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
STRIPE_SECRET_KEY = "sk_test_votre_cle"
STRIPE_WEBHOOK_SECRET = "whsec_votre_secret"  # trouvé dans dashboard Stripe
PAYPAL_CLIENT_ID = "ton_client_id"
PAYPAL_CLIENT_SECRET = "ton_client_secret"



