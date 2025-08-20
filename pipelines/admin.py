from django.contrib import admin
from .models import Pipeline,PipelineStatus

class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'user']
    # list_filter = ['status', 'assigned_to', 'assigned_from']
    # list_filter = ['status']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.user_type == 'sale':
            return qs.filter(user=request.user)
        elif request.user.user_type == 'ref':
            return qs.filter(user=request.user)
        return qs.none()

admin.site.register(Pipeline,PipelineAdmin)
admin.site.register(PipelineStatus)


