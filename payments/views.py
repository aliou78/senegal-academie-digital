from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer
import uuid

# Stripe et PayPal SDK (à installer via pip)
import stripe
import paypalrestsdk

stripe.api_key = "TON_STRIPE_SECRET_KEY"
paypalrestsdk.configure({
    "mode": "sandbox",  # ou "live" en prod
    "client_id": "TON_PAYPAL_CLIENT_ID",
    "client_secret": "TON_PAYPAL_SECRET"
})

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:  # Admin voit tous les paiements
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

    # --- Mobile Money ---
    @action(detail=False, methods=['post'])
    def mobile_money(self, request):
        user = request.user
        amount = request.data.get('amount')
        course_id = request.data.get('course')
        # Ici tu peux appeler l'API Mobile Money officielle
        transaction_id = str(uuid.uuid4())
        payment = Payment.objects.create(
            user=user,
            course_id=course_id,
            amount=amount,
            payment_method='mobile_money',
            status='pending',
            transaction_id=transaction_id
        )
        return Response({"message": "Paiement Mobile Money initié", "transaction_id": transaction_id})

    # --- Paiement par carte (Stripe) ---
    @action(detail=False, methods=['post'])
    def card(self, request):
        user = request.user
        amount = int(float(request.data.get('amount')) * 100)  # Stripe en centimes
        course_id = request.data.get('course')
        token = request.data.get('stripe_token')
        
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="XOF",
                source=token,
                description=f"Paiement cours {course_id} par {user.username}"
            )
            payment = Payment.objects.create(
                user=user,
                course_id=course_id,
                amount=amount / 100,
                payment_method='card',
                status='success',
                transaction_id=charge.id
            )
            return Response({"message": "Paiement réussi", "transaction_id": charge.id})
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=400)

    # --- PayPal ---
    @action(detail=False, methods=['post'])
    def paypal(self, request):
        user = request.user
        amount = request.data.get('amount')
        course_id = request.data.get('course')

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": str(amount), "currency": "XOF"},
                "description": f"Paiement cours {course_id} par {user.username}"
            }],
            "redirect_urls": {
                "return_url": "http://localhost:3000/paypal-success/",
                "cancel_url": "http://localhost:3000/paypal-cancel/"
            }
        })

        if payment.create():
            Payment.objects.create(
                user=user,
                course_id=course_id,
                amount=amount,
                payment_method='paypal',
                status='pending',
                transaction_id=payment.id
            )
            return Response({"message": "Paiement PayPal initié", "approval_url": payment['links'][1]['href']})
        else:
            return Response({"error": payment.error}, status=400)
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import stripe

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Gérer l’événement
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        payment_id = intent["metadata"].get("payment_id")
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = "completed"
            payment.transaction_id = intent["id"]
            payment.save()
        except Payment.DoesNotExist:
            pass

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        payment_id = intent["metadata"].get("payment_id")
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = "failed"
            payment.save()
        except Payment.DoesNotExist:
            pass

    return HttpResponse(status=200)
from django.shortcuts import redirect

def paypal_success(request):
    payment_id = request.GET.get("paymentId")
    payer_id = request.GET.get("PayerID")

    paypal_payment = paypalrestsdk.Payment.find(payment_id)
    if paypal_payment.execute({"payer_id": payer_id}):
        try:
            payment = Payment.objects.get(transaction_id=payment_id)
            payment.status = "completed"
            payment.save()
        except Payment.DoesNotExist:
            pass
        return JsonResponse({"message": "Paiement PayPal réussi"})
    else:
        return JsonResponse({"error": "Échec de l’exécution du paiement PayPal"}, status=400)


def paypal_cancel(request):
    return JsonResponse({"message": "Paiement PayPal annulé"})



