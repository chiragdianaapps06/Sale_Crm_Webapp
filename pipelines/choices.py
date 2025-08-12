from django.db.models import TextChoices


class PipelineStages(TextChoices):
    new="new","New"
    current="current","Current"
    customer="customer","Customer"
    closed="closed","Closed"