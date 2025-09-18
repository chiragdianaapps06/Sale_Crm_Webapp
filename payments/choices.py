from django.db.models import TextChoices

class PaymentStatusChoices(TextChoices):
    pending="pending", "Pending"
    success="success", "Success"
    failed="failed", "Failed"


class InvoiceStatusChoices(TextChoices):
    draft="draft", "Draft"        # Created but not finalized yet
    open="open", "Open"             # Finalized and awaiting payment
    paid="paid", "Paid"             # Successfully paid
    void="void", "Void"             # Canceled and not payable