from django.db import models
from accounts.models import AbsModel
from .choices import PaymentStatusChoices,InvoiceStatusChoices

class Payment(AbsModel):
    lead = models.ForeignKey("leads.Leads", on_delete=models.CASCADE, related_name="payments")
    sales_person = models.ForeignKey("accounts.CustomUser", on_delete=models.CASCADE, related_name="sales_payments")
    referrer = models.ForeignKey("accounts.CustomUser", on_delete=models.CASCADE, related_name="referrer_payments")

    commission_percentage = models.DecimalField(max_digits=4, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gateway_payment_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20,choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.pending)  # pending, success, failed

    def __str__(self):
        return f"{self.lead.title}_{self.gateway_payment_id}_{self.status}"



class Invoice(AbsModel):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="invoice", null=True, blank=True)
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=InvoiceStatusChoices.choices,default=InvoiceStatusChoices.draft)  # draft, open, paid, void

    def __str__(self):
        return f"{self.stripe_invoice_id}_{self.status}"