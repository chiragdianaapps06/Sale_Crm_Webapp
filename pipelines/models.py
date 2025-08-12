from django.db import models
from accounts.models import AbsModel

class Pipeline(AbsModel):
    name=models.CharField(max_length=100)
    is_active=models.BooleanField(default=False)

class PipelineStages(AbsModel):

    pipeline=models.ForeignKey(Pipeline,on_delete=models.CASCADE)
    stage=models.CharField(max_length=100)
    order=models.IntegerField()
