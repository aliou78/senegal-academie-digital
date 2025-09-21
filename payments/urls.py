from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, stripe_webhook, paypal_success, paypal_cancel
router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename="payments")

urlpatterns = [
    path('', include(router.urls)),
    path("payments/stripe-webhook/", stripe_webhook, name="stripe-webhook"),
    path("payments/paypal-success/", paypal_success, name="paypal-success"),
    path("payments/paypal-cancel/", paypal_cancel, name="paypal-cancel"),

]
