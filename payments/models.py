from django.db import models
from accounts.models import AbsModel
# Create your models here.
class Payment(AbsModel):
    lead = models.ForeignKey("leads.Leads", on_delete=models.CASCADE, related_name="payments")
    sales_person = models.ForeignKey("accounts.CustomUser", on_delete=models.CASCADE, related_name="sales_payments")
    referrer = models.ForeignKey("accounts.CustomUser", on_delete=models.CASCADE, related_name="referrer_payments")

    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    gateway = models.CharField(max_length=50, default="stripe")
    gateway_payment_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, default="pending")  # pending, success, failed



class Invoice(AbsModel):
    referrer = models.ForeignKey("accounts.CustomUser", on_delete=models.CASCADE, related_name="invoices")
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="invoice", null=True, blank=True)
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, default="draft")  # draft, open, paid, void
    amount = models.DecimalField(max_digits=10, decimal_places=2)