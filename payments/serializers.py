from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    PaymentMethod, Payment, CoursePayment, Refund, PaymentWebhook,
    InstructorCommission, PaymentConfiguration
)

User = get_user_model()


class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer pour les méthodes de paiement
    """
    class Meta:
        model = PaymentMethod
        fields = ('id', 'name', 'payment_type', 'is_active', 'configuration')


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les paiements
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'transaction_id', 'user', 'user_name', 'amount', 'currency',
                 'payment_method', 'payment_method_name', 'status', 'description',
                 'created_at', 'updated_at', 'completed_at', 'error_message')
        read_only_fields = ('id', 'transaction_id', 'user', 'created_at', 'updated_at', 'completed_at')


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un paiement
    """
    class Meta:
        model = Payment
        fields = ('amount', 'currency', 'payment_method', 'description', 'metadata')

    def create(self, validated_data):
        # Générer un ID de transaction unique
        import uuid
        import time
        
        transaction_id = f"PAY_{int(time.time())}_{str(uuid.uuid4())[:8].upper()}"
        validated_data['transaction_id'] = transaction_id
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)


class CoursePaymentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les paiements de cours
    """
    payment = PaymentSerializer(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    enrollment_progress = serializers.SerializerMethodField()

    class Meta:
        model = CoursePayment
        fields = ('id', 'payment', 'course', 'course_title', 'enrollment', 'enrollment_progress')

    def get_enrollment_progress(self, obj):
        return {
            'progress_percentage': obj.enrollment.progress_percentage,
            'enrolled_at': obj.enrollment.enrolled_at,
            'is_active': obj.enrollment.is_active,
        }


class CoursePaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un paiement de cours
    """
    class Meta:
        model = CoursePayment
        fields = ('course', 'payment_method', 'description')

    def create(self, validated_data):
        course = validated_data['course']
        payment_method = validated_data['payment_method']
        description = validated_data.get('description', f'Paiement pour le cours: {course.title}')
        
        # Créer le paiement
        payment_data = {
            'amount': course.price,
            'currency': 'XOF',
            'payment_method': payment_method,
            'description': description,
            'user': self.context['request'].user,
        }
        
        payment = Payment.objects.create(**payment_data)
        
        # Créer l'inscription
        from courses.models import Enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=self.context['request'].user,
            course=course,
            defaults={'is_active': True}
        )
        
        # Créer le paiement de cours
        course_payment = CoursePayment.objects.create(
            payment=payment,
            course=course,
            enrollment=enrollment
        )
        
        return course_payment


class RefundSerializer(serializers.ModelSerializer):
    """
    Serializer pour les remboursements
    """
    payment_transaction_id = serializers.CharField(source='payment.transaction_id', read_only=True)
    payment_amount = serializers.DecimalField(source='payment.amount', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Refund
        fields = ('id', 'payment', 'payment_transaction_id', 'payment_amount', 'amount',
                 'reason', 'status', 'external_refund_id', 'created_at', 'processed_at')
        read_only_fields = ('id', 'created_at', 'processed_at')


class RefundCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un remboursement
    """
    class Meta:
        model = Refund
        fields = ('payment', 'amount', 'reason')

    def validate(self, attrs):
        payment = attrs['payment']
        amount = attrs['amount']
        
        # Vérifier que le paiement est terminé
        if payment.status != 'completed':
            raise serializers.ValidationError("Le paiement doit être terminé pour être remboursé")
        
        # Vérifier que le montant ne dépasse pas le montant du paiement
        if amount > payment.amount:
            raise serializers.ValidationError("Le montant du remboursement ne peut pas dépasser le montant du paiement")
        
        return attrs


class PaymentWebhookSerializer(serializers.ModelSerializer):
    """
    Serializer pour les webhooks de paiement
    """
    class Meta:
        model = PaymentWebhook
        fields = ('id', 'provider', 'event_type', 'event_id', 'payload', 'processed',
                 'created_at', 'processed_at')
        read_only_fields = ('id', 'created_at', 'processed_at')


class InstructorCommissionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les commissions des formateurs
    """
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    course_title = serializers.CharField(source='course_payment.course.title', read_only=True)
    payment_amount = serializers.DecimalField(source='course_payment.payment.amount', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = InstructorCommission
        fields = ('id', 'instructor', 'instructor_name', 'course_payment', 'course_title',
                 'payment_amount', 'amount', 'percentage', 'is_paid', 'paid_at', 'created_at')
        read_only_fields = ('id', 'created_at')


class PaymentConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer pour la configuration des paiements
    """
    class Meta:
        model = PaymentConfiguration
        fields = ('instructor_commission_percentage', 'transaction_fee_percentage',
                 'minimum_payment_amount', 'maximum_payment_amount',
                 'stripe_enabled', 'orange_money_enabled', 'free_money_enabled', 'mtn_money_enabled',
                 'webhook_secret', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class PaymentStatusSerializer(serializers.Serializer):
    """
    Serializer pour mettre à jour le statut d'un paiement
    """
    status = serializers.ChoiceField(choices=Payment.STATUS_CHOICES)
    external_payment_id = serializers.CharField(required=False, allow_blank=True)
    error_message = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False, default=dict)


class MobileMoneyPaymentSerializer(serializers.Serializer):
    """
    Serializer pour les paiements Mobile Money
    """
    phone_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.ChoiceField(choices=Payment.CURRENCY_CHOICES, default='XOF')
    description = serializers.CharField(required=False, allow_blank=True)
    course_id = serializers.IntegerField(required=False)
    
    def validate_phone_number(self, value):
        # Validation basique du numéro de téléphone
        if not value.startswith('+') and not value.startswith('221'):
            if value.startswith('77') or value.startswith('78') or value.startswith('76'):
                value = '+221' + value
            elif value.startswith('70') or value.startswith('75'):
                value = '+221' + value
        return value


class StripePaymentIntentSerializer(serializers.Serializer):
    """
    Serializer pour créer un PaymentIntent Stripe
    """
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.ChoiceField(choices=Payment.CURRENCY_CHOICES, default='XOF')
    description = serializers.CharField(required=False, allow_blank=True)
    course_id = serializers.IntegerField(required=False)
    metadata = serializers.JSONField(required=False, default=dict)
