from django.contrib import admin
from .models import Leads
# Register your models here.


class LeadsAdmin(admin.ModelAdmin):
    list_display=['title','email','assigned_from','assigned_to','status']
    list_filter=['status']
    def get_queryset(self,request):
        qs=super().get_queryset(request)
        # print(qs)

        if request.user.is_superuser:
            return qs
        if request.user.user_type=='sale':
            return qs.filter(assigned_to=request.user)
        
        return qs.none()

admin.site.register(Leads,LeadsAdmin)
