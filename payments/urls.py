from django.urls import path
from .views import CreateStripeCheckout
from . import views

urlpatterns = [
    # API for creating a Stripe PaymentIntent
    path("create-payment/", CreateStripeCheckout.as_view(), name="create-stripe-payment"),
    # Webhook endpoint for Stripe
    path("stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),
    path("invoice/", views.CreateStripeInvoice.as_view(), name="strip-invoice"),
    path("report/", views.ReportsView.as_view(), name="payment-report"),
    path("success/", views.SuccessView.as_view()),
    path("failed/", views.CancelView.as_view()),
]
