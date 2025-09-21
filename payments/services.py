import stripe
import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import Payment, PaymentMethod
import uuid


class PaymentService:
    """
    Service de base pour les paiements
    """
    
    def __init__(self):
        self.config = getattr(settings, 'PAYMENT_CONFIG', {})
    
    def generate_transaction_id(self):
        """Générer un ID de transaction unique"""
        timestamp = int(timezone.now().timestamp())
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"PAY_{timestamp}_{unique_id}"
    
    def create_payment(self, user, amount, currency, payment_method, description="", metadata=None):
        """Créer un paiement"""
        transaction_id = self.generate_transaction_id()
        
        payment = Payment.objects.create(
            transaction_id=transaction_id,
            user=user,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            description=description,
            metadata=metadata or {},
            status='pending'
        )
        
        return payment
    
    def update_payment_status(self, payment, status, external_id=None, error_message=None):
        """Mettre à jour le statut d'un paiement"""
        payment.status = status
        
        if external_id:
            payment.external_payment_id = external_id
        
        if error_message:
            payment.error_message = error_message
        
        if status == 'completed' and not payment.completed_at:
            payment.completed_at = timezone.now()
        
        payment.save()
        return payment


class StripeService(PaymentService):
    """
    Service pour les paiements Stripe
    """
    
    def __init__(self):
        super().__init__()
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_payment_intent(self, amount, currency, description="", metadata=None, user=None):
        """Créer un PaymentIntent Stripe"""
        # Convertir le montant en centimes pour Stripe
        amount_in_cents = int(float(amount) * 100)
        
        # Créer le PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency=currency.lower(),
            description=description,
            metadata=metadata or {},
            automatic_payment_methods={
                'enabled': True,
            },
        )
        
        # Créer l'enregistrement de paiement dans la base de données
        if user:
            payment_method = PaymentMethod.objects.filter(payment_type='stripe').first()
            payment = self.create_payment(
                user=user,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                description=description,
                metadata={
                    **(metadata or {}),
                    'stripe_payment_intent_id': payment_intent.id
                }
            )
        
        return payment_intent
    
    def verify_webhook(self, payload, sig_header):
        """Vérifier la signature du webhook Stripe"""
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError:
            raise ValueError("Payload invalide")
        except stripe.error.SignatureVerificationError:
            raise stripe.error.SignatureVerificationError("Signature invalide")
    
    def create_refund(self, payment_intent_id, amount=None):
        """Créer un remboursement Stripe"""
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=amount  # Si None, rembourse le montant total
            )
            return refund
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe: {str(e)}")


class MobileMoneyService(PaymentService):
    """
    Service pour les paiements Mobile Money
    """
    
    def __init__(self):
        super().__init__()
        self.orange_money_config = {
            'merchant_id': settings.ORANGE_MONEY_MERCHANT_ID,
            'api_url': 'https://api.orange.com/orange-money-webpay/cm/v1/webpayment',
        }
        self.free_money_config = {
            'merchant_id': settings.FREE_MONEY_MERCHANT_ID,
            'api_url': 'https://api.free.sn/free-money/v1/payment',
        }
    
    def create_payment(self, phone_number, amount, currency, description="", user=None):
        """Créer un paiement Mobile Money"""
        # Déterminer le type de Mobile Money basé sur le numéro
        provider = self._detect_provider(phone_number)
        
        if provider == 'orange_money':
            return self._create_orange_money_payment(phone_number, amount, currency, description, user)
        elif provider == 'free_money':
            return self._create_free_money_payment(phone_number, amount, currency, description, user)
        else:
            raise ValueError("Fournisseur Mobile Money non supporté")
    
    def _detect_provider(self, phone_number):
        """Détecter le fournisseur Mobile Money basé sur le numéro"""
        # Nettoyer le numéro
        clean_number = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        
        if clean_number.startswith('221'):
            clean_number = clean_number[3:]
        
        # Orange Money: 77, 78, 76
        if clean_number.startswith(('77', '78', '76')):
            return 'orange_money'
        # Free Money: 70, 75
        elif clean_number.startswith(('70', '75')):
            return 'free_money'
        else:
            raise ValueError("Numéro de téléphone non reconnu")
    
    def _create_orange_money_payment(self, phone_number, amount, currency, description, user):
        """Créer un paiement Orange Money"""
        payment_method = PaymentMethod.objects.filter(payment_type='orange_money').first()
        
        # Créer le paiement dans la base de données
        payment = self.create_payment(
            user=user,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            description=description,
            metadata={
                'phone_number': phone_number,
                'provider': 'orange_money'
            }
        )
        
        # Simuler l'appel API Orange Money (à remplacer par l'API réelle)
        try:
            # Ici, vous feriez l'appel réel à l'API Orange Money
            # Pour l'instant, on simule une réponse
            response_data = {
                'status': 'pending',
                'transaction_id': payment.transaction_id,
                'external_id': f"OM_{payment.transaction_id}",
                'message': 'Paiement initié avec succès'
            }
            
            # Mettre à jour le paiement avec l'ID externe
            payment.external_payment_id = response_data['external_id']
            payment.status = 'processing'
            payment.save()
            
            return payment
            
        except Exception as e:
            payment.status = 'failed'
            payment.error_message = str(e)
            payment.save()
            raise Exception(f"Erreur Orange Money: {str(e)}")
    
    def _create_free_money_payment(self, phone_number, amount, currency, description, user):
        """Créer un paiement Free Money"""
        payment_method = PaymentMethod.objects.filter(payment_type='free_money').first()
        
        # Créer le paiement dans la base de données
        payment = self.create_payment(
            user=user,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            description=description,
            metadata={
                'phone_number': phone_number,
                'provider': 'free_money'
            }
        )
        
        # Simuler l'appel API Free Money (à remplacer par l'API réelle)
        try:
            # Ici, vous feriez l'appel réel à l'API Free Money
            # Pour l'instant, on simule une réponse
            response_data = {
                'status': 'pending',
                'transaction_id': payment.transaction_id,
                'external_id': f"FM_{payment.transaction_id}",
                'message': 'Paiement initié avec succès'
            }
            
            # Mettre à jour le paiement avec l'ID externe
            payment.external_payment_id = response_data['external_id']
            payment.status = 'processing'
            payment.save()
            
            return payment
            
        except Exception as e:
            payment.status = 'failed'
            payment.error_message = str(e)
            payment.save()
            raise Exception(f"Erreur Free Money: {str(e)}")
    
    def check_payment_status(self, external_id, provider):
        """Vérifier le statut d'un paiement Mobile Money"""
        try:
            if provider == 'orange_money':
                # Appel API Orange Money pour vérifier le statut
                # À implémenter selon la documentation Orange Money
                pass
            elif provider == 'free_money':
                # Appel API Free Money pour vérifier le statut
                # À implémenter selon la documentation Free Money
                pass
            
            # Pour l'instant, on retourne un statut simulé
            return {
                'status': 'completed',
                'message': 'Paiement confirmé'
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': str(e)
            }


class BankTransferService(PaymentService):
    """
    Service pour les virements bancaires
    """
    
    def __init__(self):
        super().__init__()
        self.bank_config = {
            'account_number': getattr(settings, 'BANK_ACCOUNT_NUMBER', ''),
            'bank_name': getattr(settings, 'BANK_NAME', ''),
            'swift_code': getattr(settings, 'BANK_SWIFT_CODE', ''),
        }
    
    def create_payment(self, amount, currency, description="", user=None):
        """Créer un paiement par virement bancaire"""
        payment_method = PaymentMethod.objects.filter(payment_type='bank_transfer').first()
        
        payment = self.create_payment(
            user=user,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            description=description,
            metadata={
                'bank_account': self.bank_config['account_number'],
                'bank_name': self.bank_config['bank_name'],
                'swift_code': self.bank_config['swift_code'],
                'reference': f"REF_{payment.transaction_id}"
            }
        )
        
        return payment
    
    def get_bank_details(self):
        """Obtenir les détails bancaires pour le virement"""
        return {
            'account_number': self.bank_config['account_number'],
            'bank_name': self.bank_config['bank_name'],
            'swift_code': self.bank_config['swift_code'],
            'account_holder': getattr(settings, 'BANK_ACCOUNT_HOLDER', 'Sénégal Académie Digital'),
        }
