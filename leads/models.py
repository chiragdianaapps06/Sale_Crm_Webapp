from django.db import models
from accounts.models import AbsModel

class Leads(AbsModel):
    title=models.CharField(max_length=100)
    email=models.EmailField()
    description=models.TextField()
    assigned_from=models.ForeignKey('accounts.CustomUser',on_delete=models.SET_NULL,null=True,related_name='leads_referrar')
    assigned_to=models.ForeignKey('accounts.CustomUser',on_delete=models.CASCADE,related_name='leads_sales')
    # pipeline=models.ForeignKey('pipelines.Pipeline',on_delete=models.SET_NULL,null=True
    status=models.ForeignKey('pipelines.Pipeline',on_delete=models.SET_NULL,null=True)

    def __str__(self):
        return self.title or self.email