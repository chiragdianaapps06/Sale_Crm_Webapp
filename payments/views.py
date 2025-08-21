from django.shortcuts import render
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Payment,Invoice
from utils.logger import logging
from rest_framework import status,permissions
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model

User=get_user_model()


stripe.api_key=settings.STRIPE_SECRET_KEY

class CreateStripeCheckout(APIView):
    def post(self, request):
        try:
            amount = float(request.data['amount'])
            referrer_id = request.data['referrer']
            lead_id = request.data['lead']

            # Create payment record
            payment = Payment.objects.create(
                lead_id=lead_id,
                sales_person=request.user,
                referrer_id=referrer_id,
                amount=amount,
                commission_percentage=request.data.get("commission_percentage", 0),
                status="pending",
            )

            # Create Stripe Checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(amount * 100),  # cents
                        'product_data': {
                            'name': f'Payment to Referrer {payment.referrer.username}',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url="http://localhost:8000/payments/success/",
                cancel_url="http://localhost:8000/payments/failed/",
                metadata={"payment_id": payment.id},
            )

            # Save gateway payment id (checkout session id)
            payment.gateway_payment_id = session.id
            payment.save()

            return Response({
                "checkout_url": session.url,  # Redirect user here
                "payment_id": payment.id,
                "amount": amount,
                "referrer": payment.referrer.username
            })

        except Exception as e:
            return Response({
                "message": "error",
                "data": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment_id = session["metadata"]["payment_id"]

        Payment.objects.filter(id=payment_id).update(status="success")

    elif event["type"] == "checkout.session.async_payment_failed":
        session = event["data"]["object"]
        payment_id = session["metadata"]["payment_id"]

        Payment.objects.filter(id=payment_id).update(status="failed")

    return JsonResponse({"status": "ok"})


from django.http import HttpResponse

class SuccessView(APIView):
    def get(self, request):
        return HttpResponse("Hi, your payment has been completed ")

class CancelView(APIView):
    def get(self, request):
        return HttpResponse("Hi, your payment was cancelled ")
    


class CreateStripeInvoice(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self, request):
        referrer_id = request.data["referrer"]
        amount = float(request.data["amount"])
        payment_id=request.data['payment_id']

        payment=None
        if payment_id:
            payment=Payment.objects.get(id=payment_id)

        # create Stripe Customer (if not exists)
        referrer = User.objects.get(id=referrer_id)
        customer = stripe.Customer.create(email=referrer.email)

        # create Invoice Item
        stripe.InvoiceItem.create(
            customer=customer.id,
            amount=int(amount * 100),
            currency="usd",
            description=f"Commission payment to {referrer.username}",
        )

        # create Invoice
        invoice = stripe.Invoice.create(customer=customer.id)
        finalized_invoice = stripe.Invoice.finalize_invoice(invoice.id)

        # save in DB
        inv = Invoice.objects.create(
            referrer_id=referrer_id,
            amount=amount,
            stripe_invoice_id=finalized_invoice.id,
            payment=payment,
            status=finalized_invoice.status
        )

        return Response({"invoice_url": finalized_invoice.hosted_invoice_url, "invoice_id": inv.id,"payment_id": payment.id if payment else None})



from django.db.models import Sum, Count
from django.utils.timezone import now

class ReportsView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self, request):
        year = request.query_params.get("year", now().year)

        successful = Payment.objects.filter(status="success", created_at__year=year)
        failed = Payment.objects.filter(status="failed", created_at__year=year)

        data = {
            "total_deals_successful": successful.count(),
            "total_deals_failed": failed.count(),
            "total_revenue": successful.aggregate(Sum("amount"))["amount__sum"] or 0,
            "monthly_breakdown": list(
                successful.extra(select={"month": "EXTRACT(month FROM created_at)"})
                .values("month")
                .annotate(total=Sum("amount"))
                .order_by("month")
            ),
        }
        return Response(data)
