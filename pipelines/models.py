from django.db import models
from accounts.models import AbsModel
from .choices import PipelineStages

#actual pipeline model
class Pipeline(AbsModel):
    name=models.CharField(max_length=100)
    user=models.ForeignKey('accounts.CustomUser',on_delete=models.CASCADE)
    owner = models.ForeignKey('accounts.CustomUser',on_delete=models.CASCADE,related_name='own_pipeline')

    class Meta:
        unique_together = ('name', 'user','owner') 
    def __str__(self):
        return f"{self.name}-{self.user}"

class PipelineStatus(AbsModel):
    pipeline_name=models.ForeignKey(Pipeline,on_delete=models.CASCADE)
    stage=models.CharField(max_length=100,choices=PipelineStages.choices,default=PipelineStages.new,null=True)
    
    class Meta:
        unique_together = ('pipeline_name', 'stage') 
    def __str__(self):
        return f"{self.pipeline_name}-{self.stage}"
