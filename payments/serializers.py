from rest_framework import serializers
from .models import Payment,Invoice
import stripe
from django.conf import settings
from utils.logger import logging
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .choices import InvoiceStatusChoices

User=get_user_model()

class PaymentSerializer(serializers.ModelSerializer):
    checkout_url=serializers.CharField(read_only=True)
    class Meta:
        model=Payment
        fields = [
            "id",
            "amount",
            "referrer",
            "lead",
            "commission_percentage",
            "status",
            "checkout_url",
        ]
        read_only_fields = ["status", "checkout_url"]

    def validate(self,attrs):
        if attrs['referrer'].id!=attrs['lead'].assigned_from.id:
            raise ValidationError(" given referrer is not associated with the lead.")
        
        # if attrs['lead'].assigned_to.id!=self.context['request'].user:
        #     raise ValidationError("user can't make payment for this lead")
        return attrs



    def create(self,validated_data):
        request=self.context["request"]
        user=request.user

        payment=Payment.objects.create(
            sales_person=user,
            **validated_data
        )

        logging.info(f"payment id for this transaction is {payment.id}")
        # Create Stripe Checkout session
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(payment.amount * 100),  # cents
                        "product_data": {
                            "name": f"Payment to Referrer {payment.referrer.username}",
                        },
                    },
                    "quantity": 1,
                }],
            mode='payment',
            success_url="http://localhost:8000/payments/success/",
            cancel_url="http://localhost:8000/payments/failed/",
            metadata={"payment_id": payment.id},
            )

            # Save checkout session ID
            payment.gateway_payment_id = session.id
            payment.save(update_fields=["gateway_payment_id"])

            # Attach checkout_url to serializer response
            payment.checkout_url = session.url

        except Exception as e:
            raise serializers.ValidationError({"stripe_error": str(e)})

        return payment
    

class InvoiceSerializer(serializers.ModelSerializer):
    stripe_invoice_id=serializers.CharField(read_only=True)
    status=serializers.ChoiceField(choices=InvoiceStatusChoices.choices,read_only=True)
    invoice_url=serializers.CharField(read_only=True)


    class Meta:
        model=Invoice
        fields=['id','payment','stripe_invoice_id','status','invoice_url']


    def create(self,validated_data):
        
        payment=Payment.objects.get(id=validated_data['payment'].id)
        referrer_id=payment.referrer.id
        # create Stripe Customer (if not exists)
        referrer = User.objects.get(id=referrer_id)
        customer = stripe.Customer.create(email=referrer.email)

        invoice = stripe.Invoice.create(customer=customer.id,currency="usd" )

        # create Invoice Item
        stripe.InvoiceItem.create(
            customer=customer.id,
            amount=int(payment.amount * 100),
            currency="usd",
            description=f"Commission payment to {referrer.username}",
            invoice=invoice.id 
        )

        invoice = stripe.Invoice.retrieve(invoice.id )

        finalized_invoice = stripe.Invoice.finalize_invoice(invoice.id)
        logging.info(f"invoice id {invoice}")

        inv = Invoice.objects.create(
            stripe_invoice_id=finalized_invoice.id,
            payment=payment,
            status=finalized_invoice.status
        )
        inv.stripe_invoice_id=finalized_invoice.id
        inv.status=finalized_invoice.status
        inv.invoice_url=finalized_invoice.hosted_invoice_url

        return inv