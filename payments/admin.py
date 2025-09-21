from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    PaymentMethod, Payment, CoursePayment, Refund, PaymentWebhook,
    InstructorCommission, PaymentConfiguration
)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'payment_type', 'is_active', 'created_at')
    list_filter = ('payment_type', 'is_active', 'created_at')
    search_fields = ('name',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount', 'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'currency', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'user__username', 'user__email', 'external_payment_id')
    readonly_fields = ('id', 'transaction_id', 'created_at', 'updated_at')
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('id', 'transaction_id', 'user', 'amount', 'currency', 'payment_method')
        }),
        (_('Statut'), {
            'fields': ('status', 'created_at', 'updated_at', 'completed_at')
        }),
        (_('Détails'), {
            'fields': ('description', 'metadata', 'external_payment_id', 'error_message')
        }),
    )


@admin.register(CoursePayment)
class CoursePaymentAdmin(admin.ModelAdmin):
    list_display = ('payment', 'course', 'enrollment')
    list_filter = ('course', 'payment__status', 'payment__created_at')
    search_fields = ('payment__transaction_id', 'course__title', 'payment__user__username')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'created_at', 'processed_at')
    search_fields = ('payment__transaction_id', 'reason')
    readonly_fields = ('created_at',)


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = ('provider', 'event_type', 'event_id', 'processed', 'created_at')
    list_filter = ('provider', 'event_type', 'processed', 'created_at')
    search_fields = ('event_id', 'event_type')
    readonly_fields = ('created_at', 'processed_at')


@admin.register(InstructorCommission)
class InstructorCommissionAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'course_payment', 'amount', 'percentage', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at', 'paid_at')
    search_fields = ('instructor__username', 'course_payment__course__title')
    readonly_fields = ('created_at',)


@admin.register(PaymentConfiguration)
class PaymentConfigurationAdmin(admin.ModelAdmin):
    list_display = ('instructor_commission_percentage', 'transaction_fee_percentage', 'updated_at')
    
    fieldsets = (
        (_('Commissions'), {
            'fields': ('instructor_commission_percentage',)
        }),
        (_('Frais'), {
            'fields': ('transaction_fee_percentage',)
        }),
        (_('Limites de montant'), {
            'fields': ('minimum_payment_amount', 'maximum_payment_amount')
        }),
        (_('Méthodes de paiement'), {
            'fields': ('stripe_enabled', 'orange_money_enabled', 'free_money_enabled', 'mtn_money_enabled')
        }),
        (_('Sécurité'), {
            'fields': ('webhook_secret',)
        }),
    )
    
    def has_add_permission(self, request):
        # Empêcher l'ajout de plusieurs configurations
        return not PaymentConfiguration.objects.exists()
