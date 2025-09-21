from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
import stripe
import json
from .models import (
    PaymentMethod, Payment, CoursePayment, Refund, PaymentWebhook,
    InstructorCommission, PaymentConfiguration
)
from .serializers import (
    PaymentMethodSerializer, PaymentSerializer, PaymentCreateSerializer,
    CoursePaymentSerializer, CoursePaymentCreateSerializer, RefundSerializer,
    RefundCreateSerializer, PaymentWebhookSerializer, InstructorCommissionSerializer,
    PaymentConfigurationSerializer, PaymentStatusSerializer, MobileMoneyPaymentSerializer,
    StripePaymentIntentSerializer
)
from .services import PaymentService, MobileMoneyService, StripeService


class PaymentMethodListView(generics.ListAPIView):
    """
    Liste des méthodes de paiement disponibles
    """
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [AllowAny]


class PaymentListView(generics.ListAPIView):
    """
    Liste des paiements de l'utilisateur
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related('payment_method')


class PaymentDetailView(generics.RetrieveAPIView):
    """
    Détails d'un paiement
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related('payment_method')


class CoursePaymentCreateView(generics.CreateAPIView):
    """
    Créer un paiement pour un cours
    """
    serializer_class = CoursePaymentCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Vérifier que l'utilisateur est un étudiant
        if request.user.role != 'student':
            return Response(
                {'error': 'Seuls les étudiants peuvent effectuer des paiements'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            course_payment = serializer.save()
            return Response(
                CoursePaymentSerializer(course_payment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stripe_payment_intent(request):
    """
    Créer un PaymentIntent Stripe
    """
    if request.user.role != 'student':
        return Response(
            {'error': 'Seuls les étudiants peuvent effectuer des paiements'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = StripePaymentIntentSerializer(data=request.data)
    if serializer.is_valid():
        try:
            stripe_service = StripeService()
            payment_intent = stripe_service.create_payment_intent(
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data['currency'],
                description=serializer.validated_data.get('description', ''),
                metadata=serializer.validated_data.get('metadata', {}),
                user=request.user
            )
            
            return Response({
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id
            }, status=status.HTTP_201_CREATED)
            
        except stripe.error.StripeError as e:
            return Response(
                {'error': f'Erreur Stripe: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_mobile_money_payment(request):
    """
    Créer un paiement Mobile Money
    """
    if request.user.role != 'student':
        return Response(
            {'error': 'Seuls les étudiants peuvent effectuer des paiements'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = MobileMoneyPaymentSerializer(data=request.data)
    if serializer.is_valid():
        try:
            mobile_money_service = MobileMoneyService()
            payment = mobile_money_service.create_payment(
                phone_number=serializer.validated_data['phone_number'],
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data['currency'],
                description=serializer.validated_data.get('description', ''),
                user=request.user
            )
            
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': f'Erreur Mobile Money: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Webhook Stripe pour traiter les événements de paiement
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        stripe_service = StripeService()
        event = stripe_service.verify_webhook(payload, sig_header)
        
        # Enregistrer le webhook
        webhook = PaymentWebhook.objects.create(
            provider='stripe',
            event_type=event['type'],
            event_id=event['id'],
            payload=event
        )
        
        # Traiter l'événement
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            payment = Payment.objects.filter(
                external_payment_id=payment_intent['id']
            ).first()
            
            if payment:
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.save()
                
                # Créer l'inscription au cours si c'est un paiement de cours
                course_payment = CoursePayment.objects.filter(payment=payment).first()
                if course_payment:
                    course_payment.enrollment.is_active = True
                    course_payment.enrollment.save()
                    
                    # Calculer et créer la commission du formateur
                    config = PaymentConfiguration.objects.first()
                    if config:
                        commission_amount = (course_payment.payment.amount * config.instructor_commission_percentage) / 100
                        InstructorCommission.objects.create(
                            instructor=course_payment.course.instructor,
                            course_payment=course_payment,
                            amount=commission_amount,
                            percentage=config.instructor_commission_percentage
                        )
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            payment = Payment.objects.filter(
                external_payment_id=payment_intent['id']
            ).first()
            
            if payment:
                payment.status = 'failed'
                payment.error_message = payment_intent.get('last_payment_error', {}).get('message', 'Paiement échoué')
                payment.save()
        
        webhook.processed = True
        webhook.processed_at = timezone.now()
        webhook.save()
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
    except stripe.error.SignatureVerificationError:
        return Response({'error': 'Signature invalide'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_payment_status(request, payment_id):
    """
    Mettre à jour le statut d'un paiement (pour les administrateurs)
    """
    if request.user.role != 'admin':
        return Response(
            {'error': 'Accès non autorisé'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    payment = get_object_or_404(Payment, id=payment_id)
    serializer = PaymentStatusSerializer(data=request.data)
    
    if serializer.is_valid():
        payment.status = serializer.validated_data['status']
        
        if serializer.validated_data.get('external_payment_id'):
            payment.external_payment_id = serializer.validated_data['external_payment_id']
        
        if serializer.validated_data.get('error_message'):
            payment.error_message = serializer.validated_data['error_message']
        
        if serializer.validated_data.get('metadata'):
            payment.metadata.update(serializer.validated_data['metadata'])
        
        if payment.status == 'completed' and not payment.completed_at:
            payment.completed_at = timezone.now()
        
        payment.save()
        
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefundListView(generics.ListCreateAPIView):
    """
    Liste et création de remboursements
    """
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Refund.objects.all().select_related('payment')
        return Refund.objects.filter(payment__user=self.request.user).select_related('payment')

    def perform_create(self, serializer):
        # Seuls les administrateurs peuvent créer des remboursements
        if self.request.user.role != 'admin':
            raise PermissionError('Seuls les administrateurs peuvent créer des remboursements')
        serializer.save()


class RefundDetailView(generics.RetrieveUpdateAPIView):
    """
    Détails et mise à jour d'un remboursement
    """
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Refund.objects.all().select_related('payment')
        return Refund.objects.filter(payment__user=self.request.user).select_related('payment')


class InstructorCommissionListView(generics.ListAPIView):
    """
    Liste des commissions d'un formateur
    """
    serializer_class = InstructorCommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'instructor':
            return InstructorCommission.objects.filter(
                instructor=self.request.user
            ).select_related('course_payment', 'course_payment__course', 'course_payment__payment')
        elif self.request.user.role == 'admin':
            return InstructorCommission.objects.all().select_related(
                'instructor', 'course_payment', 'course_payment__course', 'course_payment__payment'
            )
        return InstructorCommission.objects.none()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_statistics(request):
    """
    Statistiques des paiements
    """
    if request.user.role not in ['admin', 'instructor']:
        return Response(
            {'error': 'Accès non autorisé'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Statistiques générales
    total_payments = Payment.objects.filter(status='completed').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Statistiques des 30 derniers jours
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_payments = Payment.objects.filter(
        status='completed',
        completed_at__gte=thirty_days_ago
    ).count()
    recent_revenue = Payment.objects.filter(
        status='completed',
        completed_at__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Statistiques par méthode de paiement
    payment_methods_stats = Payment.objects.filter(status='completed').values(
        'payment_method__name'
    ).annotate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    # Statistiques pour les formateurs
    if request.user.role == 'instructor':
        instructor_commissions = InstructorCommission.objects.filter(
            instructor=request.user
        ).aggregate(
            total_earned=Sum('amount'),
            total_paid=Sum('amount', filter=models.Q(is_paid=True))
        )
        
        return Response({
            'instructor_stats': {
                'total_earned': instructor_commissions['total_earned'] or 0,
                'total_paid': instructor_commissions['total_paid'] or 0,
                'pending_amount': (instructor_commissions['total_earned'] or 0) - (instructor_commissions['total_paid'] or 0)
            }
        })
    
    return Response({
        'general_stats': {
            'total_payments': total_payments,
            'total_revenue': total_revenue,
            'recent_payments': recent_payments,
            'recent_revenue': recent_revenue,
        },
        'payment_methods': list(payment_methods_stats)
    })


class PaymentConfigurationView(generics.RetrieveUpdateAPIView):
    """
    Configuration des paiements
    """
    serializer_class = PaymentConfigurationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        config, created = PaymentConfiguration.objects.get_or_create()
        return config

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return PaymentConfiguration.objects.all()
        return PaymentConfiguration.objects.none()
