from django.urls import path
from . import views

urlpatterns = [
    # Méthodes de paiement
    path('methods/', views.PaymentMethodListView.as_view(), name='payment_methods'),
    
    # Paiements
    path('', views.PaymentListView.as_view(), name='payment_list'),
    path('<uuid:payment_id>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('<uuid:payment_id>/status/', views.update_payment_status, name='update_payment_status'),
    
    # Paiements de cours
    path('course/', views.CoursePaymentCreateView.as_view(), name='course_payment_create'),
    
    # Paiements spécifiques
    path('stripe/create-intent/', views.create_stripe_payment_intent, name='stripe_payment_intent'),
    path('mobile-money/', views.create_mobile_money_payment, name='mobile_money_payment'),
    
    # Webhooks
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
    
    # Remboursements
    path('refunds/', views.RefundListView.as_view(), name='refund_list'),
    path('refunds/<int:refund_id>/', views.RefundDetailView.as_view(), name='refund_detail'),
    
    # Commissions
    path('commissions/', views.InstructorCommissionListView.as_view(), name='instructor_commissions'),
    
    # Statistiques
    path('statistics/', views.payment_statistics, name='payment_statistics'),
    
    # Configuration
    path('configuration/', views.PaymentConfigurationView.as_view(), name='payment_configuration'),
]
