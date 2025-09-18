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
from .serializers import PaymentSerializer,InvoiceSerializer
from django.http import HttpResponse
from leads.models import Leads

User=get_user_model()


stripe.api_key=settings.STRIPE_SECRET_KEY


class CreateStripeCheckout(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        try:
            lead=Leads.objects.get(id=request.data['lead'])
            logging.info(f"lead status is{lead.status.stage}")
            if lead.status.stage!='closed':
                return Response({
                    "message":"Lead is not closed yet. Thus can't make payments",
                    "data":lead.status.stage
                },status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "data":str(e)
            },status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            payment = serializer.save()
            return Response({
                "message": "Success",
                "data": serializer.data
            },status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    logging.info(f"payload is {payload} sig_header is {sig_header} event is {event}")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        logging.info("Stripe webhook event created successfullly")
    except Exception:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment_id = session["metadata"]["payment_id"]
        logging.info(f"payment with id {payment_id} has been completed ")
        Payment.objects.filter(id=payment_id).update(status="success")

    elif event["type"] == "checkout.session.async_payment_failed" or event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        payment_id = session["metadata"]["payment_id"]
        logging.info(f"payment with id {payment_id} has been failed ")
        Payment.objects.filter(id=payment_id).update(status="failed")

    return JsonResponse({"status": "ok"})



class SuccessView(APIView):
    def get(self, request):
        return HttpResponse("Hi, your payment has been completed ")

class CancelView(APIView):
    def get(self, request):
        return HttpResponse("Hi, your payment was cancelled ")
    
class CreateStripeInvoice(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self, request):
        serializer=InvoiceSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            # return Response({"invoice_url": finalized_invoice.hosted_invoice_url, "invoice_id": inv.id,"payment_id": payment.id if payment else None})
            return Response({
                "data":serializer.data
            },status=status.HTTP_201_CREATED)
        return Response({
            "data":serializer.errors
        },status=status.HTTP_400_BAD_REQUEST)



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
