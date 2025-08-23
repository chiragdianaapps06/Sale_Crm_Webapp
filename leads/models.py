from django.db import models
from accounts.models import AbsModel

class Leads(AbsModel):
    title=models.CharField(max_length=100)
    email=models.EmailField()
    description=models.TextField()
    assigned_from=models.ForeignKey('accounts.CustomUser',on_delete=models.SET_NULL,null=True,related_name='leads_referrar')
    assigned_to=models.ForeignKey('accounts.CustomUser',on_delete=models.CASCADE,related_name='leads_sales')
    lead_pipeline=models.ForeignKey('pipelines.Pipeline',on_delete=models.SET_NULL,related_name='pipeline',null=True)
    status=models.ForeignKey('pipelines.PipelineStatus',on_delete=models.SET_NULL,null=True)

    class Meta:
        verbose_name_plural = "Leads"


# class ReferrerModel(AbsModel):
#     sale_person = models.ForeignKey('accounts.CustomUser',related_name='sale_person',on_delete=models.CASCADE,limit_choices_to={'user_type':'sale'})
#     referrer_person = models.ManyToManyField('account.CustomUser',related_name='referrer',on_delete=models.CASCADE,limit_choices_to={'user_type':'ref'})


