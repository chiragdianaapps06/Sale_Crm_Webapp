from django.db.models import TextChoices


class UserType(TextChoices):
    sale="sale","sales"
    ref="ref","referrer"