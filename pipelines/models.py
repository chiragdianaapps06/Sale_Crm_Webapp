from django.db import models
from accounts.models import AbsModel
from .choices import PipelineStages

#actual pipeline model
class Pipeline(AbsModel):
    name=models.CharField(max_length=100)
    user=models.ForeignKey('accounts.CustomUser',on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"

class PipelineStatus(AbsModel):
    pipeline_name=models.ForeignKey(Pipeline,on_delete=models.CASCADE)
    stage=models.CharField(max_length=100,choices=PipelineStages.choices,default=PipelineStages.new,null=True)

    def __str__(self):
        return f"{self.stage}"
