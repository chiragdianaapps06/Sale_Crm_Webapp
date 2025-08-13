from django.db import models
from accounts.models import AbsModel
from .choices import PipelineStages

class Pipeline(AbsModel):
    name=models.CharField(max_length=100)
    stage=models.CharField(max_length=100,choices=PipelineStages.choices,default=PipelineStages.new,null=True)
    order=models.IntegerField()

    def __str__(self):
        return f"{self.name}_{self.stage}"