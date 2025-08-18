from django.contrib import admin
from .models import Leads



class LeadsAdmin(admin.ModelAdmin):

    # Custamize lead dashboard 

    # list of fields that will display on dashborad
    list_display=['title','email','assigned_from','assigned_to','status']
    
    # filter on the list of fields
    list_filter = ['status', 'assigned_to', 'assigned_from']
    
    def get_queryset(self,request):
        qs=super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        if request.user.user_type=='sale':
            return qs.filter(assigned_to=request.user)
        
        if request.user.user_type=='referrer':
            return qs.filter(assigned_from=request.user)
        

        return qs.none()
        
        

admin.site.register(Leads,LeadsAdmin)
